"""
Chat History Service — Phase 6

Manages persistent conversation memory using SQLite.
Enforces MEMORY_MAX_MESSAGES per conversation and provides
MEMORY_RELEVANT_MESSAGES recent messages to the agent as context.
"""

from typing import List, Dict

from app.database.database import get_connection
from app.config.settings import (
    MEMORY_MAX_MESSAGES,
    MEMORY_RELEVANT_MESSAGES,
)


MAX_RECENT_CHATS = 20


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

    # -----------------------------------------------------
    # Add message
    # -----------------------------------------------------

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        message_type: str = "text",
        metadata: str | None = None
    ) -> None:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO messages
            (
                conversation_id,
                role,
                content,
                message_type,
                metadata
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                conversation_id,
                role,
                content,
                message_type,
                metadata
            )
        )

        cursor.execute(
            """
            UPDATE conversations
            SET updated_at = CURRENT_TIMESTAMP
            WHERE conversation_id = ?
            """,
            (conversation_id,)
        )

        connection.commit()
        connection.close()

        # Enforce per-conversation message limit
        self._trim_messages(conversation_id)

    # -----------------------------------------------------
    # Get conversation history (full — for display)
    # -----------------------------------------------------

    def get_messages(
        self,
        conversation_id: str
    ) -> List[Dict[str, str]]:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT role, content, message_type, metadata
            FROM messages
            WHERE conversation_id = ?
            ORDER BY id ASC
            """,
            (conversation_id,)
        )

        rows = cursor.fetchall()
        connection.close()

        return [
            {
                "role": row["role"],
                "content": row["content"],
                "message_type": row["message_type"],
                "metadata": row["metadata"]
            }
            for row in rows
        ]

    # -----------------------------------------------------
    # Get memory context (short-term — for agent)
    # Returns only the most recent N text messages
    # -----------------------------------------------------

    def get_memory_context(
        self,
        conversation_id: str
    ) -> List[Dict[str, str]]:
        """
        Returns the most recent MEMORY_RELEVANT_MESSAGES text
        messages formatted for the Gemini agent.
        """

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT role, content
            FROM messages
            WHERE conversation_id = ?
              AND message_type = 'text'
            ORDER BY id DESC
            LIMIT ?
            """,
            (conversation_id, MEMORY_RELEVANT_MESSAGES)
        )

        rows = cursor.fetchall()
        connection.close()

        # Return in chronological order
        return [
            {
                "role": row["role"],
                "content": row["content"]
            }
            for row in reversed(rows)
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
            (MAX_RECENT_CHATS,)
        )

        rows = cursor.fetchall()
        connection.close()

        return [
            {
                "conversation_id": row["conversation_id"],
                "title": row["title"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            }
            for row in rows
        ]

    # -----------------------------------------------------
    # Delete a conversation
    # -----------------------------------------------------

    def delete_conversation(
        self,
        conversation_id: str
    ) -> bool:
        """
        Delete a conversation and all its messages.
        Returns True if a row was deleted, False if not found.
        """

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            DELETE FROM conversations
            WHERE conversation_id = ?
            """,
            (conversation_id,)
        )

        deleted = cursor.rowcount > 0

        connection.commit()
        connection.close()

        return deleted

    # -----------------------------------------------------
    # Trim old messages (enforce MEMORY_MAX_MESSAGES)
    # -----------------------------------------------------

    def _trim_messages(
        self,
        conversation_id: str
    ) -> None:
        """
        Keep only the most recent MEMORY_MAX_MESSAGES messages
        for a given conversation.
        """

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            DELETE FROM messages
            WHERE conversation_id = ?
              AND id NOT IN (
                SELECT id FROM messages
                WHERE conversation_id = ?
                ORDER BY id DESC
                LIMIT ?
              )
            """,
            (
                conversation_id,
                conversation_id,
                MEMORY_MAX_MESSAGES
            )
        )

        connection.commit()
        connection.close()