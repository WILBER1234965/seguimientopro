"""Simple SQLite wrapper used by the application."""

import os
import sqlite3
from contextlib import closing

DB_FILE = "atajados.db"
PHOTO_DIR = "photos"
os.makedirs(PHOTO_DIR, exist_ok=True)

class Database:
    """SQLite database connection with helper methods."""

    def __init__(self, db_file: str = DB_FILE):
        self.conn = sqlite3.connect(db_file)
        self.init_tables()
    def close(self) -> None:
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None


    def init_tables(self) -> None:
        """Create tables if they do not exist."""
        with closing(self.conn.cursor()) as c:
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS items (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    unit TEXT,
                    total REAL,
                    incidence REAL,
                    active INTEGER DEFAULT 0
                )
                """
            )
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS atajados (
                    id INTEGER PRIMARY KEY,
                    number INTEGER,
                    comunidad TEXT,
                    beneficiario TEXT,
                    ci TEXT,
                    coord_e REAL,
                    coord_n REAL,
                    start_date TEXT,
                    end_date TEXT,
                    status TEXT,
                    observations TEXT,
                    photo TEXT
                )
                """
            )
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS avances (
                    id INTEGER PRIMARY KEY,
                    atajado_id INTEGER,
                    item_id INTEGER,
                    date TEXT,
                    quantity REAL,
                    start_date TEXT,
                    end_date TEXT
                )
                """
            )
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS hitos (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    date TEXT,
                    notes TEXT
                )
                """
            )
            self.conn.commit()

    def fetchall(self, sql: str, params: tuple = ()):
        """Return all rows for a query."""
        with closing(self.conn.cursor()) as cur:
            cur.execute(sql, params)
            return cur.fetchall()
    def execute(self, sql: str, params: tuple = ()) -> None:
        """Execute an SQL statement and commit changes."""
        with closing(self.conn.cursor()) as cur:
            cur.execute(sql, params)
            self.conn.commit()