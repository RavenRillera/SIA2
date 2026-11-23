import hashlib
import os
import sqlite3
from pathlib import Path


class UserDatabase:
    def __init__(self, database_path=None):
        if database_path is None:
            data_directory = Path(__file__).resolve().parent.parent / "data"
            data_directory.mkdir(exist_ok=True)
            database_path = data_directory / "users.db"
        self.database_path = Path(database_path)
        self.create_table()

    def connect(self):
        return sqlite3.connect(self.database_path)

    def create_table(self):
        connection = self.connect()
        cursor = connection.cursor()
        cursor.execute(
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
        connection.commit()
        connection.close()

    def hash_password(self, password, salt=None):
        if salt is None:
            salt = os.urandom(16).hex()
        password_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt),
            310000,
        ).hex()
        return password_hash, salt

    def register_user(self, username, email, password):
        connection = self.connect()
        cursor = connection.cursor()
        password_hash, salt = self.hash_password(password)
        try:
            cursor.execute(
                """
                INSERT INTO users
                (username, email, password_hash, salt)
                VALUES (?, ?, ?, ?)
                """,
                (username, email, password_hash, salt),
            )
            connection.commit()
            return True, "Account successfully created!"
        except sqlite3.IntegrityError:
            return False, "Username or email already exists."
        finally:
            connection.close()

    def authenticate(self, username, password):
        connection = self.connect()
        cursor = connection.cursor()
        cursor.execute(
            "SELECT password_hash, salt FROM users WHERE username = ?",
            (username,),
        )
        row = cursor.fetchone()
        connection.close()
        if row is None:
            return False, "Username or password is incorrect."
        stored_hash, salt = row
        check_hash, _salt = self.hash_password(password, salt)
        if check_hash != stored_hash:
            return False, "Username or password is incorrect."
        return True, "Signed in."
