import unittest

import time

from pytrading.utils import Timer


class TestTimerCase(unittest.TestCase):

    def setUp(self):
        self.timer = Timer()

    def test_localtime(self):
        self.timer.calibrate()
        self.assertLess(abs(time.time_ns() - self.timer.localtime()), 1_000_000)  # add assertion here


if __name__ == '__main__':
    unittest.main()
