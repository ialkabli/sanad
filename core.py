from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path
import csv, sqlite3


class RuleError(ValueError):
    pass


def required(value, label, minimum=2, maximum=120):
    value = str(value).strip()
    if not minimum <= len(value) <= maximum:
        raise RuleError(f"{label}: الطول المسموح من {minimum} إلى {maximum} حرفًا.")
    return value


def valid_date(value):
    try:
        parsed = date.fromisoformat(value)
        if parsed.isoformat() != value:
            raise ValueError()
    except (ValueError, TypeError):
        raise RuleError("أدخل تاريخًا صحيحًا بصيغة YYYY-MM-DD.")
    return value


class Database:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA busy_timeout=10000")

    @contextmanager
    def transaction(self):
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            yield self.conn
            self.conn.execute("COMMIT")
        except Exception:
            self.conn.execute("ROLLBACK")
            raise

    def rows(self, sql, args=()):
        return [dict(row) for row in self.conn.execute(sql, args)]

    def close(self):
        self.conn.close()


def export_csv(path, headers, rows):
    def safe(value):
        text = str(value if value is not None else "")
        if text.lstrip().startswith(("=", "+", "-", "@")):
            text = "'" + text
        return text

    with Path(path).open("w", encoding="utf-8-sig", newline="") as out:
        writer = csv.writer(out)
        writer.writerow(headers)
        writer.writerows([[safe(value) for value in row] for row in rows])
