
import unittest

import os

from pytrading.ipc.lmdb import LMDB, LMDBMode


class TestLMDB(unittest.TestCase):

    def setUp(self):
        self.db_path = "test_lmdb.db"
        self.lmdb_write = LMDB(self.db_path, mode=LMDBMode.WRITE)
        self.lmdb_read = LMDB(self.db_path, mode=LMDBMode.READ)

    def tearDown(self):
        del self.lmdb_read
        del self.lmdb_write
        os.remove(self.db_path + "-lock")
        os.remove(self.db_path)

    def test_get_nonexistent_key(self):
        self.assertIsNone(self.lmdb_read.get(b"nonexistent_key"))

    def test_get_all_records_empty(self):
        self.assertEqual(self.lmdb_read.get_all_records(), {})

    def test_put_and_get(self):
        key = "test_key".encode()
        value = b"test_value"
        self.assertTrue(self.lmdb_write.put(key, value))
        self.assertEqual(self.lmdb_read.get(key), value)

    def test_get_all_records(self):
        records = {b"key1": b"value1", b"key2": b"value2"}
        for key, value in records.items():
            self.lmdb_write.put(key, value)
        self.assertEqual(self.lmdb_read.get_all_records(), records)

    def test_put_existing_key(self):
        key = b"test_key"
        value1 = b"value1"
        value2 = b"value2"
        self.assertTrue(self.lmdb_write.put(key, value1))
        self.assertTrue(self.lmdb_write.put(key, value2))
        self.assertEqual(self.lmdb_read.get(key), value2)

if __name__ == '__main__':
    unittest.main()