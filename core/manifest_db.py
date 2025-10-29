import sqlite3
from contextlib import closing
from datetime import datetime
import hashlib
import os

MANIFEST_DB_PATH = None

def init_db(base_dir):
    """Initialize the manifest DB and create the table if needed."""
    global MANIFEST_DB_PATH
    MANIFEST_DB_PATH = os.path.join(base_dir, "manifest")

    with sqlite3.connect(MANIFEST_DB_PATH) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS files (
            aircraft_id TEXT NOT NULL,
            file_path TEXT NOT NULL,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            file_hash TEXT DEFAULT NULL,
            PRIMARY KEY (aircraft_id, file_path)
        )
        """)

        # Table for aircraft_id preset version tracking
        conn.execute("""
        CREATE TABLE IF NOT EXISTS aircraft_preset_versions (
            aircraft_id TEXT PRIMARY KEY,
            current_version TEXT DEFAULT NULL,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata TEXT DEFAULT NULL
        )
        """)
        
        conn.commit()


def get_conn() -> sqlite3.Connection:
    """Open and return a persistent connection to the manifest DB."""
    return sqlite3.connect(MANIFEST_DB_PATH)


def close_conn(conn: sqlite3.Connection):
    """Close previously opened manifest DB connection."""
    conn.close()


def add_file(aircraft_id: str, file_path: str, file_hash: str, conn: sqlite3.Connection = None):
    """Add a file entry to the manifest."""
    own_conn = False
    if conn is None:
        conn = sqlite3.connect(MANIFEST_DB_PATH)
        own_conn = True
    
    conn.execute(
        "INSERT OR REPLACE INTO files (aircraft_id, file_path, added_at, file_hash) VALUES (?, ?, ?, ?)",
        (aircraft_id, file_path, datetime.now(), file_hash)
    )
    conn.commit()
    if own_conn:
        conn.close()


def add_folder(aircraft_id: str, file_path: str, conn: sqlite3.Connection = None):
    """Add a folder entry to the manifest."""
    own_conn = False
    if conn is None:
        conn = sqlite3.connect(MANIFEST_DB_PATH)
        own_conn = True
    
    conn.execute(
        "INSERT OR REPLACE INTO files (aircraft_id, file_path, added_at) VALUES (?, ?, ?)",
        (aircraft_id, file_path, datetime.now())
    )
    conn.commit()
    if own_conn:
        conn.close()


def remove_file(aircraft_id: str, file_path: str, file_hash: str = None):
    """Remove a file entry from the database."""
    with sqlite3.connect(MANIFEST_DB_PATH) as conn:
        conn.execute(
            "DELETE FROM files WHERE aircraft_id=? AND file_path=?",
            (aircraft_id, file_path)
        )
        conn.commit()


def list_files(aircraft_id: str):
    """List all files tracked for a given aircraft preset."""
    with sqlite3.connect(MANIFEST_DB_PATH) as conn:
        cur = conn.execute(
            "SELECT file_path, added_at FROM files WHERE aircraft_id=?",
            (aircraft_id,)
        )
        return cur.fetchall()


def compute_file_hash(file_path: str, chunk_size: int = 1024 * 1024) -> str:
    """Compute MD5 hash of the file in a memory-efficent way
    - Reads file in chunks (default 1MB) to handle any large files
    - Returns the hex digest as a string
    """
    md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            while chunk := f.read(chunk_size):
                md5.update(chunk)
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found for hashing: {file_path}")
    except Exception as e:
        raise RuntimeError(f"Error hashing file '{file_path}': {e}")
    return md5.hexdigest()