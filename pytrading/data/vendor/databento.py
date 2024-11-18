import databento as db

client = db.Historical('')

# Get 10 levels of ES lead month
data = client.timeseries.get_range(
    dataset='GLBX.MDP3',
    schema='mbp-10',
    start="2023-12-06T14:30",
    end="2023-12-06T20:30",
    symbols=['ES.n.0'],
    stype_in='continuous',
)
df = data.to_df()

live_client = db.Live(key="")

# Next, we will subscribe to the ohlcv-1s schema for a few symbols
live_client.subscribe(
    dataset="GLBX.MDP3",
    schema="ohlcv-1s",
    stype_in="continuous",
    symbols=["ES.c.0", "ES.c.1", "CL.c.0", "CL.c.1"],
)

# Now, we will open a file for writing and start streaming
live_client.add_stream("example.dbn")
live_client.start()

# We will listen for 10 seconds before closing the connection
# Any ohlcv-1s bars received during this time will be saved
live_client.block_for_close(timeout=10)

# Finally, we will open the DBN file
dbn_store = db.read_dbn("example.dbn")
print(dbn_store.to_df(schema="ohlcv-1s"))
