from enum import Enum
from typing import Optional

import lmdb


class LMDBMode(Enum):
    READ = 0
    WRITE = 1


class LMDB:
    def __init__(self, db_path, mode: LMDBMode = LMDBMode.READ, db: Optional[int] = None):
        if mode == LMDBMode.READ:
            self.env: lmdb.Environment = lmdb.open(db_path, subdir=False, readonly=True)
        else:
            self.env: lmdb.Environment = lmdb.open(db_path, subdir=False)
        self.db = db

    def __del__(self):
        self.env.close()

    def get(self, key: bytes):
        with self.env.begin(db=self.db) as txn:
            with txn.cursor() as cursor:
                return cursor.get(key)

    def get_all_records(self):
        d = {}
        with self.env.begin(db=self.db) as txn:
            with txn.cursor() as cursor:
                for key, value in cursor:
                    d[key] = value
        return d

    def put(self, key: bytes, value: bytes) -> bool:
        with self.env.begin(db=self.db, write=True) as txn:
            with txn.cursor() as cursor:
                return cursor.put(key, value)
