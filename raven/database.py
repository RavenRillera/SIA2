import hashlib
import hmac
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

ITERATIONS = 310_000


class UserDatabase:
    def __init__(self, database_path=None):
        if database_path is None:
            data_directory = Path(__file__).resolve().parent.parent / "data"
            data_directory.mkdir(exist_ok=True)
            database_path = data_directory / "users.db"
        self.database_path = Path(database_path)
        self.create_table()

    @contextmanager
    def connect(self):
        """Always commits/rolls back and closes, even when an error is raised."""
        connection = sqlite3.connect(self.database_path)
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def create_table(self):
        with self.connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL
                )
                """
            )

    @staticmethod
    def hash_password(password, salt=None):
        if salt is None:
            salt = os.urandom(16).hex()
        password_hash = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt), ITERATIONS
        ).hex()
        return password_hash, salt

    def register_user(self, username, email, password):
        password_hash, salt = self.hash_password(password)
        try:
            with self.connect() as connection:
                connection.execute(
                    "INSERT INTO users (username, email, password_hash, salt) VALUES (?, ?, ?, ?)",
                    (username, email.lower(), password_hash, salt),
                )
        except sqlite3.IntegrityError:
            return False, "Username or email already exists."
        return True, "Account successfully created!"

    def authenticate(self, username, password):
        with self.connect() as connection:
            row = connection.execute(
                "SELECT password_hash, salt FROM users WHERE username = ?", (username,)
            ).fetchone()
        if row is None:
            return False, "Username or password is incorrect."
        stored_hash, salt = row
        check_hash, _ = self.hash_password(password, salt)
        # constant-time comparison avoids timing attacks
        if not hmac.compare_digest(check_hash, stored_hash):
            return False, "Username or password is incorrect."
        return True, "Signed in."