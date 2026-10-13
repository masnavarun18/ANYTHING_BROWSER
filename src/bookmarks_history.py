"""
ANYTHING BROWSER - Bookmarks & History Manager
Provides persistent SQLite storage for browsing history, auto-completion index, and bookmarks.
"""

import os
import sqlite3
import time
import hashlib


class BookmarksHistoryManager:
    """
    Manages SQLite database storage for browsing history and user bookmarks.
    """

    def __init__(self, db_path=None):
        if db_path is None:
            appdata = os.getenv("LOCALAPPDATA", os.path.expanduser("~"))
            storage_dir = os.path.join(appdata, "AnythingBrowser")
            os.makedirs(storage_dir, exist_ok=True)
            db_path = os.path.join(storage_dir, "browser_data.db")

        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # History table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    title TEXT NOT NULL,
                    visit_time REAL NOT NULL
                )
                """
            )
            # Bookmarks table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS bookmarks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    created_at REAL NOT NULL
                )
                """
            )
            # Downloads table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS downloads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    save_path TEXT NOT NULL,
                    url TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    created_at REAL NOT NULL
                )
                """
            )
            # Users table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    full_name TEXT,
                    is_active INTEGER DEFAULT 0,
                    created_at REAL NOT NULL
                )
                """
            )
            # Settings table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def add_history(self, url: str, title: str):
        if not url or url.startswith("about:") or url.startswith("data:"):
            return
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO history (url, title, visit_time) VALUES (?, ?, ?)",
                (url, title or url, time.time()),
            )
            conn.commit()

    def get_history(self, limit: int = 100) -> list:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT url, title, visit_time FROM history ORDER BY visit_time DESC LIMIT ?",
                (limit,),
            )
            rows = cursor.fetchall()
            return [
                {"url": r[0], "title": r[1], "visit_time": r[2]}
                for r in rows
            ]

    def clear_history(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM history")
            conn.commit()

    def add_bookmark(self, url: str, title: str) -> bool:
        if not url:
            return False
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR REPLACE INTO bookmarks (url, title, created_at) VALUES (?, ?, ?)",
                    (url, title or url, time.time()),
                )
                conn.commit()
                return True
        except Exception:
            return False

    def remove_bookmark(self, url: str):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM bookmarks WHERE url = ?", (url,))
            conn.commit()

    def is_bookmarked(self, url: str) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM bookmarks WHERE url = ?", (url,))
            return cursor.fetchone()[0] > 0

    def get_bookmarks(self) -> list:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT url, title, created_at FROM bookmarks ORDER BY created_at DESC"
            )
            rows = cursor.fetchall()
            return [
                {"url": r[0], "title": r[1], "created_at": r[2]}
                for r in rows
            ]

    def add_download(self, filename: str, save_path: str, url: str, file_size: int = 0):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO downloads (filename, save_path, url, file_size, created_at) VALUES (?, ?, ?, ?, ?)",
                (filename, save_path, url, file_size, time.time()),
            )
            conn.commit()

    def get_downloads(self, limit: int = 100) -> list:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, filename, save_path, url, file_size, created_at FROM downloads ORDER BY created_at DESC LIMIT ?",
                (limit,),
            )
            rows = cursor.fetchall()
            return [
                {
                    "id": r[0],
                    "filename": r[1],
                    "save_path": r[2],
                    "url": r[3],
                    "file_size": r[4],
                    "created_at": r[5],
                }
                for r in rows
            ]

    def remove_download(self, download_id: int):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM downloads WHERE id = ?", (download_id,))
            conn.commit()

    def clear_downloads(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM downloads")
            conn.commit()

    def _hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def create_user(self, username: str, password: str, full_name: str = "") -> tuple:
        username = username.strip().lower()
        if not username or len(username) < 3:
            return False, "Username must be at least 3 characters long."
        if not password or len(password) < 4:
            return False, "Password must be at least 4 characters long."

        pwd_hash = self._hash_password(password)
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (username, password_hash, full_name, is_active, created_at) VALUES (?, ?, ?, 1, ?)",
                    (username, pwd_hash, full_name or username, time.time()),
                )
                cursor.execute("UPDATE users SET is_active = 0 WHERE username != ?", (username,))
                conn.commit()
                return True, "User account created successfully!"
        except sqlite3.IntegrityError:
            return False, "Username already exists. Please choose a different username."
        except Exception as e:
            return False, f"Failed to create account: {str(e)}"

    def authenticate_user(self, username: str, password: str) -> tuple:
        username = username.strip().lower()
        pwd_hash = self._hash_password(password)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, username, full_name FROM users WHERE username = ? AND password_hash = ?",
                (username, pwd_hash),
            )
            row = cursor.fetchone()
            if row:
                user = {"id": row[0], "username": row[1], "full_name": row[2]}
                self.set_active_user(username)
                return user, "Login successful!"
            else:
                return None, "Invalid username or password. Please try again."

    def set_active_user(self, username: str):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET is_active = 0")
            cursor.execute("UPDATE users SET is_active = 1 WHERE username = ?", (username.lower(),))
            conn.commit()

    def get_active_user(self) -> dict | None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, full_name FROM users WHERE is_active = 1 LIMIT 1")
            row = cursor.fetchone()
            if row:
                return {"id": row[0], "username": row[1], "full_name": row[2]}
            return None

    def logout_active_user(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET is_active = 0")
            conn.commit()

    def get_setting(self, key: str, default_value: str = "") -> str:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row[0] if row else default_value

    def set_setting(self, key: str, value: str):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
            conn.commit()
