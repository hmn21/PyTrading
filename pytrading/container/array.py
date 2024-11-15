from typing import Optional

import numpy as np
from numba import njit

# Define a function to update a portion of an array with another array
@njit
def bulk_update(arr1: np.ndarray, arr2: np.ndarray, s1: int, e1: int, s2: int, e2: int):
    arr1[s1:e1] = arr2[s2:e2]

# Define a class to create a resizable array
class ResizableArray:

    # Initialize the resizable array with a given data type, capacity, and resize factor
    def __init__(self, dtype: type, capacity: int, resize_factor: float = 1.5):
        assert capacity > 0
        assert issubclass(dtype, np.generic)
        self._arr = np.empty(capacity, dtype=dtype)
        self._capacity = capacity
        self._size = 0
        self._resize_factor = resize_factor

    # Return the size of the array
    def __len__(self) -> int:
        return self._size

    # Return the value at a given index
    def __getitem__(self, index):
        if index >= self._size:
            raise IndexError
        return self._arr[index]

    # Set the value at a given index
    def __setitem__(self, index, value):
        if index >= self._size:
            raise IndexError
        self._arr[index] = value

    # Iterate over the array
    def __iter__(self):
        for i in range(self._size):
            yield self._arr[i]

    # Return the size of the array
    @property
    def size(self) -> int:
        return self._size

    # Return the capacity of the array
    @property
    def capacity(self) -> int:
        return self._capacity

    # Return the underlying array
    def underlying(self) -> np.ndarray:
        return self._arr

    # Delete an element at a given index
    def delete(self, index):
        if index >= self._size:
            raise IndexError
        bulk_update(self._arr, self._arr, index, self._size - 1, index + 1, self._size)
        self._size -= 1

    # Resize the array to a given size
    def resize(self, size: int):
        if size <= self._capacity:
            self._size = size
        else:
            self.extend(size)

    # Extend the array to a given capacity
    def extend(self, capacity: Optional[int] = None):
        if capacity is None:
            capacity = int(self._capacity * self._resize_factor)
        if capacity < self._capacity:
            return
        new_arr = np.empty(capacity, dtype=self._arr.dtype)
        bulk_update(new_arr, self._arr, 0, self._size, 0, self._size)
        self._arr = new_arr
        self._capacity = capacity

    # Insert a value at a given index
    def insert(self, index, value):
        if self._size == self._capacity:
            self.extend()
        bulk_update(self._arr, self._arr, index + 1, self._size + 1, index, self.size)
        self._arr[index] = value
        self._size += 1

    # Append a value to the end of the array
    def append(self, value):
        if self._size == self._capacity:
            self.extend()
        self._arr[self._size] = value
        self._size += 1

    # Clear the array
    def clear(self):
        self._size = 0

    # Shrink the array to fit the given size
    def shrink_to_fit(self, size: Optional[int]):
        assert size < self._capacity
        if size is not None:
            assert size >= self._size
        else:
            size = self._size
        new_arr = np.empty(size, dtype=self._arr.dtype)
        bulk_update(new_arr, self._arr, 0, self._size, 0, self._size)
        self._capacity = size
