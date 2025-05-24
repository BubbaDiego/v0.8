# data_locker/database.py

import sqlite3
import os

class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None

    def connect(self):
        if self.conn is None:
            dir_name = os.path.dirname(self.db_path)
            if dir_name and dir_name.strip() != "":
                os.makedirs(dir_name, exist_ok=True)

            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            try:
                self.conn.execute("PRAGMA journal_mode=WAL;")
            except sqlite3.DatabaseError as e:
                # Handle corruption or non-database files gracefully
                if "file is not a database" in str(e) or "database disk image is malformed" in str(e):
                    self.conn.close()
                    # Remove the bad file and recreate a fresh database
                    try:
                        os.remove(self.db_path)
                    except OSError:
                        pass
                    self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
                    self.conn.row_factory = sqlite3.Row
                    self.conn.execute("PRAGMA journal_mode=WAL;")
                else:
                    raise
        return self.conn

    def recover_database(self):
        """Recreate the database file if it's corrupt."""
        if self.conn:
            try:
                self.conn.close()
            finally:
                self.conn = None
        try:
            os.remove(self.db_path)
        except OSError:
            pass
        # Fresh connection will recreate the DB file
        self.connect()

    def get_cursor(self):
        return self.connect().cursor()

    def commit(self):
        self.connect().commit()

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    # New helper methods
    def list_tables(self) -> list:
        """Return a list of user-defined table names."""
        cursor = self.get_cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        return [row[0] for row in cursor.fetchall()]

    def fetch_all(self, table_name: str) -> list:
        """Return all rows from a table as a list of dictionaries."""
        cursor = self.get_cursor()
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        return [dict(r) for r in rows]
