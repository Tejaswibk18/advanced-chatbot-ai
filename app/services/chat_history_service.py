from typing import List, Dict, Optional

from app.database.database import get_connection


MAX_RECENT_CHATS = 5


class ChatHistoryService:

    # -----------------------------------------------------
    # Create conversation
    # -----------------------------------------------------

    def create_conversation(
        self,
        conversation_id: str,
        title: str
    ) -> None:

        connection = get_connection()

        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT OR IGNORE INTO conversations
            (
                conversation_id,
                title
            )
            VALUES (?, ?)
            """,
            (
                conversation_id,
                title
            )
        )

        connection.commit()

        connection.close()

        self._cleanup_old_conversations()

    # -----------------------------------------------------
    # Add message
    # -----------------------------------------------------

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str
    ) -> None:

        connection = get_connection()

        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO messages
            (
                conversation_id,
                role,
                content
            )
            VALUES (?, ?, ?)
            """,
            (
                conversation_id,
                role,
                content
            )
        )

        cursor.execute(
            """
            UPDATE conversations
            SET updated_at = CURRENT_TIMESTAMP
            WHERE conversation_id = ?
            """,
            (
                conversation_id,
            )
        )

        connection.commit()

        connection.close()

        self._cleanup_old_conversations()

    # -----------------------------------------------------
    # Get conversation history
    # -----------------------------------------------------

    def get_messages(
        self,
        conversation_id: str
    ) -> List[Dict[str, str]]:

        connection = get_connection()

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT role, content
            FROM messages
            WHERE conversation_id = ?
            ORDER BY id ASC
            """,
            (
                conversation_id,
            )
        )

        rows = cursor.fetchall()

        connection.close()

        return [
            {
                "role": row["role"],
                "content": row["content"]
            }
            for row in rows
        ]

    # -----------------------------------------------------
    # Get recent conversations
    # -----------------------------------------------------

    def get_recent_conversations(
        self
    ) -> List[Dict]:

        connection = get_connection()

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                conversation_id,
                title,
                created_at,
                updated_at
            FROM conversations
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            (
                MAX_RECENT_CHATS,
            )
        )

        rows = cursor.fetchall()

        connection.close()

        return [
            {
                "conversation_id":
                    row["conversation_id"],

                "title":
                    row["title"],

                "created_at":
                    row["created_at"],

                "updated_at":
                    row["updated_at"]
            }
            for row in rows
        ]

    # -----------------------------------------------------
    # Delete old conversations
    # -----------------------------------------------------

    def _cleanup_old_conversations(
        self
    ) -> None:

        connection = get_connection()

        cursor = connection.cursor()

        cursor.execute(
            """
            DELETE FROM conversations
            WHERE conversation_id NOT IN (
                SELECT conversation_id
                FROM conversations
                ORDER BY updated_at DESC
                LIMIT ?
            )
            """,
            (
                MAX_RECENT_CHATS,
            )
        )

        connection.commit()

        connection.close()