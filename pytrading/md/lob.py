from typing import List, Tuple

import numpy as np
from numba import njit

from pytrading.container.array import ResizableArray


# This function uses numba to speed up the appending of values to two arrays
@njit
def bulk_append(arr1: np.ndarray, arr2: np.ndarray, values: List[Tuple[float, float]]):
    for i in range(len(values)):
        arr1[i] = values[i][0]
        arr2[i] = values[i][1]

# This class represents a Limit Order Book (LOB)
class LOB:

    # This function initializes the LOB with a symbol and a capacity
    def __init__(self, symbol: str, capacity: int = 50):
        self.symbol = symbol
        self.bids = ResizableArray(np.float64, capacity)
        self.asks = ResizableArray(np.float64, capacity)
        self.bid_volumes = ResizableArray(np.float64, capacity)
        self.ask_volumes = ResizableArray(np.float64, capacity)
        self.timestamp = 0
        self.sequence = 0

    # This property returns the size of the bid array
    @property
    def bid_size(self):
        return self.bids.size

    # This property returns the size of the ask array
    @property
    def ask_size(self):
        return self.asks.size

    # This function returns a string representation of the LOB
    def __str__(self):
        return f"LOB({self.symbol}: bid size={self.bid_size}, ask size={self.ask_size}))"

    # This function updates the bid snapshot with a list of tuples
    def bid_snapshot_update(self, arr: List[Tuple[float, float]]):
        self.bids.clear()
        self.bids.resize(len(arr))
        self.bid_volumes.clear()
        self.bid_volumes.resize(len(arr))
        bulk_append(self.bids.underlying(), self.bid_volumes.underlying(), arr)

    # This function updates the ask snapshot with a list of tuples
    def ask_snapshot_update(self, arr: List[Tuple[float, float]]):
        self.asks.clear()
        self.asks.resize(len(arr))
        self.ask_volumes.clear()
        self.ask_volumes.resize(len(arr))
        bulk_append(self.asks.underlying(), self.ask_volumes.underlying(), arr)
