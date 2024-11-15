import os
import mmap
import sys
from enum import Enum
from typing import Optional


class MMapMode(Enum):
    READ = 0
    WRITE = 1


MMapReadFileRegistry = {}
MMapWriteFileRegistry = {}


class MMapFile:

    def __init__(self, file_path: str, mode: MMapMode, size: Optional[int] = None):
        self.file_path = file_path
        self.mode = mode
        if self.mode == MMapMode.READ:
            self.size = os.path.getsize(file_path)
            self.file = open(file_path, "rb")
            if sys.platform == "win32":
                self.mm = mmap.mmap(self.file.fileno(), self.size, access=mmap.ACCESS_READ)
            else:
                self.mm = mmap.mmap(self.file.fileno(), 0, prot=mmap.PROT_READ)
            MMapReadFileRegistry[self.file_path] = self
        else:
            if os.path.exists(file_path):
                self.size = os.path.getsize(file_path)
                self.file = open(file_path, "r+b")
            else:
                self.file = open(file_path, "w+b")
                assert size > 0
                self.size = size
                self.file.truncate(size)
            if sys.platform == "win32":
                self.mm = mmap.mmap(self.file.fileno(), self.size)
            else:
                self.mm = mmap.mmap(self.file.fileno(), 0)
            MMapWriteFileRegistry[self.file_path] = self

    def __del__(self):
        self.mm.close()
        self.file.close()

    def extend(self, size: int):
        assert self.mode == MMapMode.WRITE
        if size > self.size:
            self.mm.resize(size)
            self.size = size


class MMapRecord:

    def __init__(self, mmap_file: str, offset: int, size: int, mode: MMapMode = MMapMode.READ):
        if mode == MMapMode.READ:
            self.mm = MMapReadFileRegistry[mmap_file]
        else:
            self.mm = MMapWriteFileRegistry[mmap_file]
        self.offset = offset
        self.size = size
