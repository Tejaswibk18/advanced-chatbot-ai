"""
Agent Route — Phase 5

POST /api/agent/run        — run agent, get full execution result
POST /api/agent/stream     — run agent, stream events to frontend
DELETE /api/agent/{conversation_id} — delete a conversation (Phase 6)
"""

import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.schemas.chat import (
    AgentRequest,
    AgentResponse,
    ToolCallRecord,
)
from app.services.agent_service import (
    run_agent,
    run_agent_stream,
)
from app.services.chat_history_service import ChatHistoryService


router = APIRouter(
    prefix="/api/agent",
    tags=["Agent"]
)

chat_history = ChatHistoryService()


# =========================================================
# Run Agent (blocking)
# =========================================================

@router.post(
    "/run",
    response_model=AgentResponse
)
async def agent_run(
    request: AgentRequest
):
    """
    Run the AI agent and return the full execution result,
    including all tool calls, RAG sources, and iteration count.
    """

    try:

        conversation_id = request.conversation_id

        # Phase 6 — load memory context for the agent
        history = chat_history.get_memory_context(conversation_id)

        # Ensure conversation exists
        if not history:
            title = request.message[:50]
            chat_history.create_conversation(
                conversation_id=conversation_id,
                title=title
            )

        # Run the agent loop
        execution = run_agent(
            message=request.message,
            history=history,
            document_id=request.document_id
        )

        # Persist user message
        chat_history.add_message(
            conversation_id=conversation_id,
            role="user",
            content=request.message,
            message_type="text"
        )

        # Persist agent response
        chat_history.add_message(
            conversation_id=conversation_id,
            role="model",
            content=execution.response,
            message_type="text"
        )

        return AgentResponse(
            conversation_id=conversation_id,
            response=execution.response,
            iterations=execution.iterations,
            tool_calls=[
                ToolCallRecord(
                    tool_name=tc.tool_name,
                    args=tc.args,
                    result=tc.result,
                    success=tc.success
                )
                for tc in execution.tool_calls
            ],
            rag_sources=execution.rag_sources,
            image_result=execution.image_result,
            reached_max_iterations=execution.reached_max_iterations
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Agent execution failed: {error}"
        )


# =========================================================
# Stream Agent
# =========================================================

@router.post("/stream")
async def agent_stream(
    request: AgentRequest
):
    """
    Run the AI agent and stream structured JSON events.

    Event types streamed (newline-delimited JSON):
      tool_start  — agent is about to call a tool
      tool_result — tool call finished (success/failure)
      image       — image was generated
      text        — final text answer
      done        — agent finished, includes iterations + sources
      error       — something went wrong
    """

    conversation_id = request.conversation_id

    history = chat_history.get_memory_context(conversation_id)

    if not history:
        title = request.message[:50]
        chat_history.create_conversation(
            conversation_id=conversation_id,
            title=title
        )

    def stream():

        generated_text = ""

        for event in run_agent_stream(
            message=request.message,
            history=history,
            document_id=request.document_id
        ):

            yield json.dumps(event) + "\n"

            if event["type"] == "text":
                generated_text += event.get("content", "")

        # Persist after stream ends
        chat_history.add_message(
            conversation_id=conversation_id,
            role="user",
            content=request.message,
            message_type="text"
        )

        if generated_text.strip():
            chat_history.add_message(
                conversation_id=conversation_id,
                role="model",
                content=generated_text,
                message_type="text"
            )

    return StreamingResponse(
        stream(),
        media_type="application/x-ndjson"
    )


# =========================================================
# Delete Conversation (Phase 6)
# =========================================================

@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str
):
    """
    Delete a conversation and all its messages.
    """

    deleted = chat_history.delete_conversation(conversation_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found."
        )

    return {
        "message": "Conversation deleted successfully.",
        "conversation_id": conversation_id
    }
