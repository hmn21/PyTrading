import time

class Timer:

    def __init__(self):
        self._local_start = time.time_ns()
        self._start = time.perf_counter_ns()

    def calibrate(self):
        self._local_start = time.time_ns()
        self._start = time.perf_counter_ns()

    def monotonic(self) -> float:
        return time.perf_counter()

    def monotonic_ns(self) -> int:
        return time.perf_counter_ns()

    def localtime(self) -> int:
        return self.to_localtime(self.monotonic_ns())

    def to_localtime(self, ts: int) -> int:
        return ts - self._start + self._local_start
