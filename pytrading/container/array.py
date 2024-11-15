from typing import Optional

import numpy as np


class ResizableArray:

    def __init__(self, dtype: type, capacity: int, resize_factor: float = 1.5):
        assert capacity > 0
        assert issubclass(dtype, np.generic)
        self._arr = np.empty(capacity, dtype=dtype)
        self._capacity = capacity
        self._size = 0
        self._resize_factor = resize_factor

    def __len__(self) -> int:
        return self._size

    def __getitem__(self, index):
        if index >= self._size:
            raise IndexError
        return self._arr[index]

    def __setitem__(self, index, value):
        if index >= self._size:
            raise IndexError
        self._arr[index] = value

    def __iter__(self):
        for i in range(self._size):
            yield self._arr[i]

    @property
    def capacity(self) -> int:
        return self._capacity

    def underlying(self) -> np.ndarray:
        return self._arr

    def delete(self, index):
        if index >= self._size:
            raise IndexError
        self._arr[index - 1:self._size - 1] = self._arr[index:self._size]
        self._size -= 1

    def resize(self, size: int):
        if size <= self._capacity:
            self._size = size
        else:
            self.extend(size)

    def extend(self, capacity: Optional[int] = None):
        if capacity is None:
            capacity = int(self._capacity * self._resize_factor)
        new_arr = np.empty(capacity, dtype=self._arr.dtype)
        new_arr[:self._size] = self._arr[:self._size]
        self._arr = new_arr
        self._capacity = capacity

    def insert(self, index, value):
        if self._size == self._capacity:
            self.extend()
        self._arr[index + 1:self._size + 1] = self._arr[index:self._size]
        self._arr[index] = value
        self._size += 1

    def append(self, value):
        if self._size == self._capacity:
            self.extend()
        self._arr[self._size] = value
        self._size += 1
