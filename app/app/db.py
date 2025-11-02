import sqlite3, os, hashlib, json
from contextlib import contextmanager

def ensure_dir(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)

def init_db(db_path: str):
    ensure_dir(db_path)
    with sqlite3.connect(db_path) as con:
        con.execute("CREATE TABLE IF NOT EXISTS sent_items (url TEXT PRIMARY KEY, first_sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);")
        con.execute("CREATE TABLE IF NOT EXISTS sent_signals (sig_hash TEXT PRIMARY KEY, payload TEXT, first_sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);")
        con.commit()

@contextmanager
def connect(db_path: str):
    con = sqlite3.connect(db_path, timeout=10)
    try:
        yield con
    finally:
        con.close()

def is_sent(db_path: str, url: str) -> bool:
    with connect(db_path) as con:
        cur = con.execute("SELECT 1 FROM sent_items WHERE url = ?;", (url,))
        return cur.fetchone() is not None

def mark_sent(db_path: str, url: str):
    with connect(db_path) as con:
        con.execute("INSERT OR IGNORE INTO sent_items (url) VALUES (?);", (url,))
        con.commit()

def _sig_hash(d: dict) -> str:
    raw = json.dumps(d, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()

def signal_already_sent(db_path: str, sig: dict) -> bool:
    h = _sig_hash(sig)
    with connect(db_path) as con:
        cur = con.execute("SELECT 1 FROM sent_signals WHERE sig_hash = ?;", (h,))
        return cur.fetchone() is not None

def mark_signal(db_path: str, sig: dict):
    h = _sig_hash(sig)
    with connect(db_path) as con:
        con.execute("INSERT OR IGNORE INTO sent_signals (sig_hash, payload) VALUES (?, ?);", (h, json.dumps(sig)))
        con.commit()
