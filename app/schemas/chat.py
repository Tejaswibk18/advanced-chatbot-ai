from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# =========================================================
# Chat Request / Response
# =========================================================

class ChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        description="Message sent by the user"
    )

    conversation_id: str = Field(
        ...,
        min_length=1,
        description="Unique ID of the conversation"
    )

    document_id: str | None = Field(
        default=None,
        description=(
            "ID of the document currently "
            "associated with this conversation"
        )
    )


class ChatResponse(BaseModel):
    conversation_id: str
    response: str


# =========================================================
# Agent Request / Response (Phase 5)
# =========================================================

class AgentRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        description="User message sent to the agent"
    )

    conversation_id: str = Field(
        ...,
        min_length=1,
        description="Unique ID of the conversation"
    )

    document_id: str | None = Field(
        default=None,
        description="Optional document ID for RAG"
    )


class ToolCallRecord(BaseModel):
    tool_name: str
    args: Dict[str, Any]
    result: Dict[str, Any]
    success: bool


class AgentResponse(BaseModel):
    conversation_id: str
    response: str
    iterations: int
    tool_calls: List[ToolCallRecord]
    rag_sources: List[Dict[str, Any]]
    image_result: Optional[Dict[str, Any]]
    reached_max_iterations: bool