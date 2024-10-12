import sqlite3


class Database:
    def __init__(self, db_name="trades.db"):
        self.connection = sqlite3.connect(db_name)
        self.cursor = self.connection.cursor()
        self.create_table()

    def create_table(self):
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY,
                trade_type TEXT,
                entry_price REAL,
                sl_price REAL,
                tp_price REAL,
                lot_size REAL,
                stage TEXT
            )
        """
        )
        self.connection.commit()

    def insert_trade(self, trade_type, entry_price, sl_price, tp_price, lot_size, stage):
        self.cursor.execute(
            """
            INSERT INTO trades (trade_type, entry_price, sl_price, tp_price, lot_size, stage)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (trade_type, entry_price, sl_price, tp_price, lot_size, stage),
        )
        self.connection.commit()

    def update_trade_status(self, trade_id, status):
        self.cursor.execute(
            """
            UPDATE trades
            SET stage = ?
            WHERE id = ?
        """,
            (status, trade_id),
        )
        self.connection.commit()

    def fetch_trades(self):
        self.cursor.execute("SELECT * FROM trades")
        return self.cursor.fetchall()

    def close(self):
        self.connection.close()


# https://github.com/ErikKalkoken/aiodbm
