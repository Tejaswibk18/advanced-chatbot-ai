import os
import sqlite3

from pathlib import Path


# Use DATA_DIR env variable if set (e.g. Render persistent disk at /data),
# otherwise fall back to the project root for local development.
DATA_DIR = Path(os.environ.get("DATA_DIR", Path(__file__).resolve().parents[2]))

DATABASE_PATH = DATA_DIR / "chat.db"


def get_connection():
    """
    Create and return a SQLite database connection.
    """

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = sqlite3.Row

    return connection


def initialize_database():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            message_type TEXT NOT NULL DEFAULT 'text',
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (
                conversation_id
            )
            REFERENCES conversations(
                conversation_id
            )
            ON DELETE CASCADE
        )
        """
    )

    connection.commit()
    connection.close()