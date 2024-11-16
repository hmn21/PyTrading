"""
Design:
    8 byte header for each ring buffer for version and latest index
    8 byte header for each record for sequence
"""
import mmap
import struct
from typing import Optional

from pytrading.ipc.mmap import MMapRecord


class RingBuffer:
    def __init__(self, size = 4, record_size = 0, mmrecord: Optional[MMapRecord] = None):
        assert record_size > 0
        assert mmrecord is not None
        self.size = size
        self.record_size = record_size
        self.mmrecord = mmrecord
        self.idx = None

    @property
    def itemsize(self):
        return (self.record_size + 8) * self.size + 8

    def __len__(self):
        return self.size

    def get_latest_idx(self):
        mm: mmap.mmap = self.mmrecord.mf.mm
        mm.seek(self.mmrecord.offset)
        b = mm.read(8)
        i = struct.unpack("<Q", b)[0]
        idx = i % (1 << 32)
        return idx

    def get_sequence(self, idx):
        mm: mmap.mmap = self.mmrecord.mf.mm
        mm.seek(self.mmrecord.offset + 8 + idx * (self.record_size + 8))
        b = mm.read(8)
        i = struct.unpack("<Q", b)[0]
        return i

class RecordCacheReader:
    pass


class RecordCacheWriter:
    pass