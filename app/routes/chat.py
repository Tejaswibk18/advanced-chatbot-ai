"""
Chat Route — updated for Phase 6 (memory-aware)

Uses get_memory_context() to provide short-term conversation memory
to the LLM on every request, instead of the raw full history.
"""

import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.schemas.chat import ChatRequest, ChatResponse

from app.services.llm_service import (
    generate_response,
    generate_stream
)

from app.services.chat_history_service import (
    ChatHistoryService
)


router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)


chat_history_service = ChatHistoryService()


# =========================================================
# Normal Chat
# =========================================================

@router.post(
    "/",
    response_model=ChatResponse
)
async def chat(
    request: ChatRequest
):

    try:

        conversation_id = (
            request.conversation_id
        )

        # Phase 6 — memory-aware context for LLM
        history = (
            chat_history_service
            .get_memory_context(
                conversation_id
            )
        )

        if not history:
            title = request.message[:50]
            chat_history_service.create_conversation(
                conversation_id=conversation_id,
                title=title
            )

        response = generate_response(
            message=request.message,
            history=history,
            document_id=request.document_id
        )

        # -------------------------------------------------
        # Save user message
        # -------------------------------------------------

        chat_history_service.add_message(
            conversation_id=conversation_id,
            role="user",
            content=request.message,
            message_type="text"
        )

        # -------------------------------------------------
        # Save model response
        # -------------------------------------------------

        chat_history_service.add_message(
            conversation_id=conversation_id,
            role="model",
            content=response,
            message_type="text"
        )

        return ChatResponse(
            conversation_id=conversation_id,
            response=response
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Failed to generate response: "
                f"{error}"
            )
        )


# =========================================================
# Streaming Chat
# =========================================================

@router.post("/stream")
async def chat_stream(
    request: ChatRequest
):

    conversation_id = (
        request.conversation_id
    )

    # Phase 6 — memory-aware context
    history = (
        chat_history_service
        .get_memory_context(
            conversation_id
        )
    )

    if not history:
        title = request.message[:50]
        chat_history_service.create_conversation(
            conversation_id=conversation_id,
            title=title
        )

    def stream():

        generated_text = ""

        try:

            for event in generate_stream(
                message=request.message,
                history=history,
                document_id=request.document_id
            ):

                if event["type"] == "text":

                    text = event["content"]
                    generated_text += text

                    yield (
                        json.dumps(
                            {
                                "type": "text",
                                "content": text
                            }
                        )
                        + "\n"
                    )

                elif event["type"] == "image":

                    yield (
                        json.dumps(event)
                        + "\n"
                    )

            # -------------------------------------------------
            # Save user message
            # -------------------------------------------------

            chat_history_service.add_message(
                conversation_id=conversation_id,
                role="user",
                content=request.message,
                message_type="text"
            )

            # -------------------------------------------------
            # Save model response
            # -------------------------------------------------

            if generated_text.strip():

                chat_history_service.add_message(
                    conversation_id=conversation_id,
                    role="model",
                    content=generated_text,
                    message_type="text"
                )

            yield (
                json.dumps({"type": "done"})
                + "\n"
            )

        except Exception as error:

            yield (
                json.dumps(
                    {
                        "type": "error",
                        "content": str(error)
                    }
                )
                + "\n"
            )

    return StreamingResponse(
        stream(),
        media_type="application/x-ndjson"
    )


# =========================================================
# Recent Chats
# =========================================================

@router.get("/recent")
async def recent_chats():

    return {
        "conversations":
            chat_history_service
            .get_recent_conversations()
    }


# =========================================================
# Get Conversation Messages
# =========================================================

@router.get("/{conversation_id}")
async def get_conversation(
    conversation_id: str
):

    messages = (
        chat_history_service
        .get_messages(
            conversation_id
        )
    )

    if not messages:

        raise HTTPException(
            status_code=404,
            detail="Conversation not found."
        )

    return {
        "conversation_id": conversation_id,
        "messages": messages
    }


# =========================================================
# Delete Conversation (Phase 6)
# =========================================================

@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str
):

    deleted = (
        chat_history_service
        .delete_conversation(
            conversation_id
        )
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found."
        )

    return {
        "message": "Conversation deleted.",
        "conversation_id": conversation_id
    }