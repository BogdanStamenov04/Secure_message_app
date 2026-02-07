"""
Database module handling SQLite interactions for users, friends,
groups, public rooms, and message history.
"""

import sqlite3
import hashlib
import os
from typing import List, Tuple, Dict

DB_DIR: str = "data"
DB_PATH: str = os.path.join(DB_DIR, "data.db")


class Database:
    """
    Handles all SQLite database interactions including users, friends,
    groups, public rooms, and message history.
    """

    def __init__(self) -> None:
        if not os.path.exists(DB_DIR):
            os.makedirs(DB_DIR)
        self.create_tables()

    def get_connection(self) -> sqlite3.Connection:
        """Creates and returns a new database connection."""
        return sqlite3.connect(DB_PATH)

    def create_tables(self) -> None:
        """Creates necessary tables if they do not exist."""
        conn = self.get_connection()
        try:
            with conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS friends (
                        user_1 TEXT NOT NULL,
                        user_2 TEXT NOT NULL,
                        PRIMARY KEY (user_1, user_2)
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS friend_requests (
                        sender TEXT NOT NULL,
                        receiver TEXT NOT NULL,
                        PRIMARY KEY (sender, receiver)
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS groups (
                        group_name TEXT PRIMARY KEY
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS group_members (
                        group_name TEXT NOT NULL,
                        username TEXT NOT NULL,
                        PRIMARY KEY (group_name, username)
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS public_rooms (
                        room_name TEXT PRIMARY KEY,
                        tags TEXT,
                        creator TEXT
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        sender TEXT NOT NULL,
                        receiver TEXT NOT NULL,
                        content TEXT NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
        finally:
            conn.close()

    def _hash_password(self, password: str) -> str:
        """Hashes a password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()

    def register_user(self, username: str, password: str) -> str:
        """Registers a new user. Returns 'success' or 'taken'."""
        pwd_hash = self._hash_password(password)
        conn = self.get_connection()
        try:
            with conn:
                conn.execute(
                    "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                    (username, pwd_hash)
                )
            return "success"
        except sqlite3.IntegrityError:
            return "taken"
        finally:
            conn.close()

    def check_login(self, username: str, password: str) -> bool:
        """Verifies username and password credentials."""
        pwd_hash = self._hash_password(password)
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                "SELECT id FROM users WHERE username = ? AND password_hash = ?",
                (username, pwd_hash)
            )
            return cursor.fetchone() is not None
        finally:
            conn.close()

    def send_friend_request(self, sender: str, receiver: str) -> str:
        """Sends a friend request. Returns status string."""
        if sender == receiver:
            return "error"
        conn = self.get_connection()
        try:
            if not conn.execute(
                "SELECT id FROM users WHERE username = ?", (receiver,)
            ).fetchone():
                return "not_found"

            if conn.execute(
                "SELECT * FROM friends WHERE user_1 = ? AND user_2 = ?", (sender, receiver)
            ).fetchone():
                return "already_friends"

            with conn:
                conn.execute(
                    "INSERT INTO friend_requests (sender, receiver) VALUES (?, ?)",
                    (sender, receiver)
                )
            return "success"
        except sqlite3.IntegrityError:
            return "already_sent"
        finally:
            conn.close()

    def get_pending_requests(self, username: str) -> List[str]:
        """Returns a list of usernames who sent friend requests."""
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                "SELECT sender FROM friend_requests WHERE receiver = ?", (username,)
            )
            return [row[0] for row in cursor.fetchall()]
        finally:
            conn.close()

    def handle_request(self, sender: str, receiver: str, action: str) -> None:
        """Accepts or declines a friend request."""
        conn = self.get_connection()
        try:
            with conn:
                conn.execute(
                    "DELETE FROM friend_requests WHERE sender = ? AND receiver = ?",
                    (sender, receiver)
                )
                if action == "accept":
                    conn.execute(
                        "INSERT OR IGNORE INTO friends (user_1, user_2) VALUES (?, ?)",
                        (receiver, sender)
                    )
                    conn.execute(
                        "INSERT OR IGNORE INTO friends (user_1, user_2) VALUES (?, ?)",
                        (sender, receiver)
                    )
        finally:
            conn.close()

    def get_friends_list(self, username: str) -> List[str]:
        """Returns a list of friends."""
        conn = self.get_connection()
        try:
            cursor = conn.execute("SELECT user_2 FROM friends WHERE user_1 = ?", (username,))
            return [row[0] for row in cursor.fetchall()]
        finally:
            conn.close()

    def create_group(self, group_name: str, creator: str) -> bool:
        """Creates a private group."""
        conn = self.get_connection()
        try:
            with conn:
                conn.execute("INSERT INTO groups (group_name) VALUES (?)", (group_name,))
                conn.execute(
                    "INSERT INTO group_members (group_name, username) VALUES (?, ?)",
                    (group_name, creator)
                )
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def join_group(self, group_name: str, username: str) -> bool:
        """Adds a user to a private group."""
        conn = self.get_connection()
        try:
            if not conn.execute(
                "SELECT group_name FROM groups WHERE group_name = ?", (group_name,)
            ).fetchone():
                return False
            with conn:
                conn.execute(
                    "INSERT OR IGNORE INTO group_members (group_name, username) VALUES (?, ?)",
                    (group_name, username)
                )
            return True
        finally:
            conn.close()

    def get_group_members(self, group_name: str) -> List[str]:
        """Returns members of a group."""
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                "SELECT username FROM group_members WHERE group_name = ?", (group_name,)
            )
            return [row[0] for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_user_groups(self, username: str) -> List[str]:
        """Returns groups the user is part of."""
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                "SELECT group_name FROM group_members WHERE username = ?", (username,)
            )
            return [row[0] for row in cursor.fetchall()]
        finally:
            conn.close()

    def create_public_room(self, room_name: str, tags: str, creator: str) -> bool:
        """Creates a public room with tags."""
        conn = self.get_connection()
        try:
            with conn:
                conn.execute(
                    "INSERT INTO public_rooms (room_name, tags, creator) VALUES (?, ?, ?)",
                    (room_name, tags, creator)
                )
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def get_public_rooms(self) -> List[Tuple[str, str]]:
        """Returns a list of all public rooms and their tags."""
        conn = self.get_connection()
        try:
            cursor = conn.execute("SELECT room_name, tags FROM public_rooms")
            return cursor.fetchall()
        finally:
            conn.close()

    def store_message(self, sender: str, receiver: str, encrypted_content: str) -> None:
        """Stores an encrypted message in the database for history/offline access."""
        conn = self.get_connection()
        try:
            with conn:
                conn.execute(
                    "INSERT INTO messages (sender, receiver, content) VALUES (?, ?, ?)",
                    (sender, receiver, encrypted_content)
                )
        finally:
            conn.close()

    def get_chat_history(self, user1: str, user2: str) -> List[Dict[str, str]]:
        """Retrieves chat history between two entities."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            if user2.startswith("#") or user2.startswith("&"):
                # Group/Room history
                cursor.execute(
                    "SELECT sender, receiver, content FROM messages "
                    "WHERE receiver = ? ORDER BY id ASC",
                    (user2,)
                )
            else:
                # Direct message history
                cursor.execute("""
                    SELECT sender, receiver, content FROM messages 
                    WHERE (sender = ? AND receiver = ?) OR (sender = ? AND receiver = ?)
                    ORDER BY id ASC
                """, (user1, user2, user2, user1))

            rows = cursor.fetchall()
            history = []
            for r in rows:
                history.append({"sender": r[0], "to": r[1], "text": r[2]})
            return history
        finally:
            conn.close()
