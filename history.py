"""
Translation History Manager
=============================
Stores and retrieves translation history using SQLite.
All data lives in ~/.trilingo/history.db
"""

import os
import sqlite3
import datetime
from typing import List, Tuple


DB_DIR  = os.path.join(os.path.expanduser("~"), ".trilingo")
DB_PATH = os.path.join(DB_DIR, "history.db")


class HistoryManager:
    """SQLite-backed translation history."""

    def __init__(self, db_path: str = DB_PATH):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._create_table()

    def _create_table(self):
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at  TEXT    NOT NULL,
                from_lang   TEXT    NOT NULL,
                to_lang     TEXT    NOT NULL,
                source_text TEXT    NOT NULL,
                result_text TEXT    NOT NULL
            )
        """)
        self._conn.commit()

    def add(self, from_lang: str, to_lang: str,
            source_text: str, result_text: str):
        """Insert a new history record."""
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._conn.execute(
            "INSERT INTO history (created_at, from_lang, to_lang, source_text, result_text) "
            "VALUES (?, ?, ?, ?, ?)",
            (now, from_lang, to_lang, source_text, result_text),
        )
        self._conn.commit()

    def fetch_all(self, limit: int = 200) -> List[Tuple]:
        """Return recent history records, newest first."""
        cur = self._conn.execute(
            "SELECT id, created_at, from_lang, to_lang, source_text, result_text "
            "FROM history ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        return cur.fetchall()

    def delete(self, record_id: int):
        """Delete a specific record."""
        self._conn.execute("DELETE FROM history WHERE id = ?", (record_id,))
        self._conn.commit()

    def clear_all(self):
        """Remove all history."""
        self._conn.execute("DELETE FROM history")
        self._conn.commit()

    def export_to_file(self, filepath: str, fmt: str = "txt"):
        """
        Export history to a text or CSV file.

        Args:
            filepath: Output file path.
            fmt:      'txt' or 'csv'
        """
        records = self.fetch_all(limit=10000)

        if fmt == "csv":
            import csv
            with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(["ID", "Date", "From", "To", "Source", "Translation"])
                for row in records:
                    writer.writerow(row)
        else:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("TriLingo Translation History\n")
                f.write("=" * 60 + "\n\n")
                for row in records:
                    rid, created, fr, to, src, res = row
                    f.write(f"[{created}]  {fr.upper()} → {to.upper()}\n")
                    f.write(f"  Source:      {src}\n")
                    f.write(f"  Translation: {res}\n")
                    f.write("-" * 60 + "\n")

    def count(self) -> int:
        cur = self._conn.execute("SELECT COUNT(*) FROM history")
        return cur.fetchone()[0]

    def close(self):
        self._conn.close()
