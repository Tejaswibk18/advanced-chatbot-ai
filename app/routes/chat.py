from fastapi import APIRouter, HTTPException

from fastapi.responses import StreamingResponse

from app.schemas.chat import (
    ChatRequest,
    ChatResponse
)

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


chat_history_service = (
    ChatHistoryService()
)


# ---------------------------------------------------------
# Send message
# ---------------------------------------------------------

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

        # Get previous messages.
        history = (
            chat_history_service
            .get_messages(
                conversation_id
            )
        )

        # Generate response.
        response = generate_response(
            message=request.message,
            history=history
        )

        # Create conversation if this
        # is the first message.
        if not history:

            title = request.message[:50]

            chat_history_service.create_conversation(
                conversation_id=conversation_id,
                title=title
            )

        # Save user message.
        chat_history_service.add_message(
            conversation_id=conversation_id,
            role="user",
            content=request.message
        )

        # Save assistant response.
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


# ---------------------------------------------------------
# Streaming chat
# ---------------------------------------------------------

@router.post(
    "/stream"
)
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

    generated_chunks = []

    def stream():

        try:

            for chunk in generate_stream(
                message=request.message,
                history=history
            ):

                generated_chunks.append(
                    chunk
                )

                yield chunk

            complete_response = "".join(
                generated_chunks
            )

            # Create conversation if needed.
            if not history:

                title = request.message[:50]

                chat_history_service.create_conversation(
                    conversation_id=conversation_id,
                    title=title
                )

            # Save user message.
            chat_history_service.add_message(
                conversation_id=conversation_id,
                role="user",
                content=request.message
            )

            # Save assistant message.
            chat_history_service.add_message(
                conversation_id=conversation_id,
                role="model",
                content=complete_response
            )

        except Exception as error:

            yield (
                f"\n\n[ERROR] {error}"
            )

    return StreamingResponse(
        stream(),
        media_type="text/plain"
    )


# ---------------------------------------------------------
# Get recent chats
# ---------------------------------------------------------

@router.get(
    "/recent"
)
async def recent_chats():

    return {
        "conversations":
            chat_history_service
            .get_recent_conversations()
    }


# ---------------------------------------------------------
# Get previous conversation
# ---------------------------------------------------------

@router.get(
    "/{conversation_id}"
)
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
        "conversation_id":
            conversation_id,

        "messages":
            messages
    }