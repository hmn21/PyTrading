import unittest

import numpy as np

from pytrading.container import ResizableArray

class TestResizableArray(unittest.TestCase):

    def setUp(self):
        self.array = ResizableArray(dtype=np.int32, capacity=4)

    def test_initialization(self):
        self.assertEqual(len(self.array), 0)
        self.assertEqual(self.array._capacity, 4)
        self.assertEqual(self.array._resize_factor, 1.5)

    def test_append(self):
        self.array.append(np.int32(1))
        self.array.append(np.int32(2))
        self.assertEqual(len(self.array), 2)
        self.assertEqual(self.array[0], 1)
        self.assertEqual(self.array[1], 2)

    def test_insert(self):
        self.array.append(1)
        self.array.append(3)
        self.array.insert(1, 2)
        self.assertEqual(len(self.array), 3)
        self.assertEqual(self.array[0], 1)
        self.assertEqual(self.array[1], 2)
        self.assertEqual(self.array[2], 3)

    def test_resize(self):
        self.assertEqual(self.array._capacity, 4)
        for i in range(4):
            self.array.append(i)
        self.assertEqual(self.array._capacity, 4)
        self.array.append(4)
        self.assertEqual(self.array._capacity, 6)
        self.assertEqual(len(self.array), 5)

    def test_getitem(self):
        self.array.append(1)
        self.array.append(2)
        self.assertEqual(self.array[0], 1)
        self.assertEqual(self.array[1], 2)
        with self.assertRaises(IndexError):
            _ = self.array[2]

    def test_setitem(self):
        self.array.append(1)
        self.array.append(2)
        self.array[1] = 3
        self.assertEqual(self.array[1], 3)
        with self.assertRaises(IndexError):
            self.array[2] = 4

    def test_delitem(self):
        self.array.append(1)
        self.array.append(2)
        self.array.append(3)
        self.array.delete(1)
        self.assertEqual(self.array[1], 3)
        with self.assertRaises(IndexError):
            _ = self.array[2]

    def test_iter(self):
        elements = [1, 2, 3]
        for element in elements:
            self.array.append(element)
        iter_elements = [x for x in self.array]
        self.assertEqual(iter_elements, elements)


if __name__ == '__main__':
    unittest.main()
