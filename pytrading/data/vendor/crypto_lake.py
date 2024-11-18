import datetime

import lakeapi
import lakeapi.orderbook
import pandas as pd

diffs = lakeapi.load_data(
    table="book_delta_v2",
    start=datetime.datetime(2024, 4, 1),
    end=datetime.datetime(2024, 4, 2),
    symbols=["AVAX-USDT"],
    exchanges=['BINANCE'],
)

ob = lakeapi.orderbook.OrderBookUpdater(diffs)

# Aggregate order book into one-minute snapshot
minutes = pd.DataFrame(
    index=range(24 * 60),
    columns=['received_time', 'time', 'sequence_number', 'bids', 'asks']
)

last_timestamp = 0
last_idx = 0
while ob.process_next_update():
    timestamp_seconds = ob.received_timestamp // 60_000_000_000
    # Save only the first snapshot in each minute
    if last_timestamp and timestamp_seconds > last_timestamp:
        minutes.iloc[last_idx]['bids'] = ob.bid.copy()
        minutes.iloc[last_idx]['asks'] = ob.ask.copy()
        minutes.iloc[last_idx]['received_time'] = ob.received_timestamp
        minutes.iloc[last_idx]['time'] = timestamp_seconds
        minutes.iloc[last_idx]['sequence_number'] = ob.sequence_number
        last_idx += 1
    # print('debug: best bid ask:', ob.get_bests(), last_idx)
    last_timestamp = timestamp_seconds

# Keep empty minutes missing and drop the empty end of dataframe
minutes = minutes.iloc[:last_idx]
minutes['time'] = pd.to_datetime(minutes['time'], unit='m')
