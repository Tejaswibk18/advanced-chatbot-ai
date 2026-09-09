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

from app.services.memory_service import (
    MemoryService
)


router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)


memory_service = MemoryService()


@router.post(
    "/",
    response_model=ChatResponse
)
async def chat(
    request: ChatRequest
):

    try:

        history = memory_service.get_history(
            request.conversation_id
        )

        response = generate_response(
            message=request.message,
            history=history
        )

        memory_service.add_message(
            conversation_id=request.conversation_id,
            role="user",
            content=request.message
        )

        memory_service.add_message(
            conversation_id=request.conversation_id,
            role="model",
            content=response
        )

        return ChatResponse(
            conversation_id=request.conversation_id,
            response=response
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate response: {error}"
        )


@router.post("/stream")
async def chat_stream(
    request: ChatRequest
):

    history = memory_service.get_history(
        request.conversation_id
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

            memory_service.add_message(
                conversation_id=request.conversation_id,
                role="user",
                content=request.message
            )

            memory_service.add_message(
                conversation_id=request.conversation_id,
                role="model",
                content=complete_response
            )

        except Exception as error:

            yield f"\n\n[ERROR] {error}"

    return StreamingResponse(
        stream(),
        media_type="text/plain"
    )


@router.delete(
    "/{conversation_id}"
)
async def clear_chat(
    conversation_id: str
):

    memory_service.clear_conversation(
        conversation_id
    )

    return {
        "message": "Conversation cleared",
        "conversation_id": conversation_id
    }