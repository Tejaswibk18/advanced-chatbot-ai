from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

import json

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

        history = (
            chat_history_service
            .get_messages(
                conversation_id
            )
        )

        response = generate_response(
            message=request.message,
            history=history,
            document_id=request.document_id
        )

        if not history:

            title = request.message[:50]

            chat_history_service.create_conversation(
                conversation_id=conversation_id,
                title=title
            )

        # -------------------------------------------------
        # Save user message
        # -------------------------------------------------

        chat_history_service.add_message(
            conversation_id=conversation_id,
            role="user",
            content=request.message
        )

        # -------------------------------------------------
        # Save model response
        # -------------------------------------------------

        chat_history_service.add_message(
            conversation_id=conversation_id,
            role="model",
            content=response
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

    history = (
        chat_history_service
        .get_messages(
            conversation_id
        )
    )

    def stream():

        generated_text = ""

        try:

            # -------------------------------------------------
            # Generate AI response
            # -------------------------------------------------

            for event in generate_stream(
                message=request.message,
                history=history,
                document_id=request.document_id
            ):

                # ---------------------------------------------
                # Text event
                # ---------------------------------------------

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

                # ---------------------------------------------
                # Image event
                # ---------------------------------------------

                elif event["type"] == "image":

                    yield (
                        json.dumps(
                            event
                        )
                        + "\n"
                    )

            # -------------------------------------------------
            # Create conversation if new
            # -------------------------------------------------

            if not history:

                title = request.message[:50]

                chat_history_service.create_conversation(
                    conversation_id=conversation_id,
                    title=title
                )

            # -------------------------------------------------
            # Save user message
            # -------------------------------------------------

            chat_history_service.add_message(
                conversation_id=conversation_id,
                role="user",
                content=request.message
            )

            # -------------------------------------------------
            # Save model response
            # -------------------------------------------------

            if generated_text.strip():

                chat_history_service.add_message(
                    conversation_id=conversation_id,
                    role="model",
                    content=generated_text
                )

            # -------------------------------------------------
            # End event
            # -------------------------------------------------

            yield (
                json.dumps(
                    {
                        "type": "done"
                    }
                )
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
# Get Conversation
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