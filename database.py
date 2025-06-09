# database.py
import os
import sqlite3

DB_FILE   = "atajados.db"
PHOTO_DIR = "photos"
os.makedirs(PHOTO_DIR, exist_ok=True)

class Database:
    def __init__(self, db_file=DB_FILE):
        self.conn = sqlite3.connect(db_file)
        self.init_tables()

    def init_tables(self):
        c = self.conn.cursor()
        # Tabla items
        c.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id         INTEGER PRIMARY KEY,
                name       TEXT,
                unit       TEXT,
                total      REAL,
                incidence  REAL
            )
        ''')
        # Añadir columna active si no existe
        try:
            c.execute("ALTER TABLE items ADD COLUMN active INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass

        # Tabla atajados
        c.execute('''
            CREATE TABLE IF NOT EXISTS atajados (
                id           INTEGER PRIMARY KEY,
                number       INTEGER,
                comunidad    TEXT,
                beneficiario TEXT,
                ci           TEXT,
                coord_e      REAL,
                coord_n      REAL,
                start_date   TEXT,
                end_date     TEXT,
                status       TEXT,
                observations TEXT,
                photo        TEXT
            )
        ''')

        # Tabla avances con columnas de fechas
        c.execute('''
            CREATE TABLE IF NOT EXISTS avances (
                id          INTEGER PRIMARY KEY,
                atajado_id  INTEGER,
                item_id     INTEGER,
                date        TEXT,
                quantity    REAL,
                start_date  TEXT,
                end_date    TEXT
            )
        ''')
        # Si la tabla ya existía sin estas columnas, agregarlas
        try:
            c.execute("ALTER TABLE avances ADD COLUMN start_date TEXT")
        except sqlite3.OperationalError:
            pass
        try:
            c.execute("ALTER TABLE avances ADD COLUMN end_date TEXT")
        except sqlite3.OperationalError:
            pass

        # Tabla hitos
        c.execute('''
            CREATE TABLE IF NOT EXISTS hitos (
                id    INTEGER PRIMARY KEY,
                name  TEXT,
                date  TEXT,
                notes TEXT
            )
        ''')

        self.conn.commit()

    def fetchall(self, sql, params=()):
        cur = self.conn.cursor()
        cur.execute(sql, params)
        return cur.fetchall()

    def execute(self, sql, params=()):
        cur = self.conn.cursor()
        cur.execute(sql, params)
        self.conn.commit()