# data_locker/database.py

import sqlite3
import os

class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None

    def connect(self):
        if self.conn is None:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            self.conn.execute("PRAGMA journal_mode=WAL;")
        return self.conn

    def get_cursor(self):
        return self.connect().cursor()

    def commit(self):
        self.connect().commit()

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None
