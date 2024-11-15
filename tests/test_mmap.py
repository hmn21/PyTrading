import os
import unittest

from pytrading.ipc.mmap import MMapMode, MMapFile, MMapRecord, MMapReadFileRegistry, MMapWriteFileRegistry


class TestMMapFile(unittest.TestCase):

    def setUp(self):
        self.file_path = "test_mmap_file.bin"
        self.size = 1024
        self.mmap_file_write = MMapFile(self.file_path, MMapMode.WRITE, size=self.size)
        self.mmap_file_read = MMapFile(self.file_path, MMapMode.READ)

    def tearDown(self):
        del self.mmap_file_read
        MMapReadFileRegistry.clear()
        del self.mmap_file_write
        MMapWriteFileRegistry.clear()
        os.remove(self.file_path)

    def test_initialization_write_mode(self):
        self.assertEqual(self.mmap_file_write.mode, MMapMode.WRITE)
        self.assertTrue(os.path.exists(self.file_path))

    def test_initialization_read_mode(self):
        self.assertEqual(self.mmap_file_read.mode, MMapMode.READ)

    def test_extend(self):
        new_size = 2048
        self.mmap_file_write.extend(new_size)
        self.assertEqual(self.mmap_file_write.size, new_size)
        self.assertEqual(self.mmap_file_write.mm.size(), new_size)

    def test_mmap_record(self):
        offset = 0
        size = 512
        record = MMapRecord(self.file_path, offset, size)
        self.assertEqual(record.mm, self.mmap_file_read)
        self.assertEqual(record.offset, offset)
        self.assertEqual(record.size, size)

if __name__ == '__main__':
    unittest.main()