"""
Agent Service — Phase 5

Implements the explicit agent loop:
  1. Understand goal
  2. Decide whether a tool is needed
  3. Execute tool
  4. Observe result
  5. Reason again
  6. Produce final answer

Includes:
- Configurable max iteration limit
- Tool execution tracking (name, args, result, success/failure)
- RAG source tracking
- Structured AgentExecution state
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Generator, List

from google import genai
from google.genai import types

from app.config.settings import (
    GEMINI_API_KEY,
    AGENT_MAX_ITERATIONS,
    AGENT_TEMPERATURE,
    MEMORY_RELEVANT_MESSAGES,
)
from app.services.tool_registry import (
    ALL_TOOLS,
    execute_tool,
)


# =========================================================
# Gemini Client
# =========================================================

client = genai.Client(api_key=GEMINI_API_KEY)

MODEL_NAME = "gemini-3.5-flash-lite"


# =========================================================
# System Instruction
# =========================================================

AGENT_SYSTEM_INSTRUCTION = """
You are a helpful AI agent with access to tools.

Your responsibilities:
- Answer questions clearly and accurately.
- Explain difficult concepts in simple language.
- Give examples when useful.
- If you are unsure about something, say so.
- Do not invent facts.
- Keep responses structured and easy to understand.

MEMORY:
- You are given recent conversation history as context.
- Use this to understand references like "that project", "the answer
  you gave earlier", or "the document I uploaded".
- Do not rely on memory for current/real-time information;
  use tools instead.

WEB SEARCH:
- Use web_search when the question requires current, recent, or
  web-based information.
- Do not use web search for questions answerable from your knowledge.
- Base your answer on the information returned by the tool.

IMAGE GENERATION:
- Use image_generation when the user explicitly asks to create,
  generate, draw, or visualize an image.
- Create a clear and detailed image prompt from the user's request.

DOCUMENT SEARCH:
- Use document_search when the user asks about their uploaded document.
- Base your answer strictly on the retrieved document content.
- Never invent information not present in the document.
"""


# =========================================================
# Data Structures
# =========================================================

@dataclass
class ToolCall:
    """Records one tool invocation during agent execution."""
    tool_name: str
    args: Dict[str, Any]
    result: Dict[str, Any]
    success: bool


@dataclass
class AgentExecution:
    """Full execution state returned after the agent loop finishes."""
    response: str
    iterations: int
    tool_calls: List[ToolCall] = field(default_factory=list)
    rag_sources: List[Dict] = field(default_factory=list)
    image_result: Dict | None = None
    reached_max_iterations: bool = False


# =========================================================
# Build Gemini Contents
# =========================================================

def _build_contents(
    message: str,
    history: List[Dict[str, str]]
) -> List[types.Content]:
    """
    Build the conversation contents list.
    Limits history to MEMORY_RELEVANT_MESSAGES most-recent entries.
    """
    recent = history[-MEMORY_RELEVANT_MESSAGES:]

    contents = []

    for item in recent:
        contents.append(
            types.Content(
                role=item["role"],
                parts=[types.Part(text=item["content"])]
            )
        )

    contents.append(
        types.Content(
            role="user",
            parts=[types.Part(text=message)]
        )
    )

    return contents


# =========================================================
# Agent Loop
# =========================================================

def run_agent(
    message: str,
    history: List[Dict[str, str]],
    document_id: str | None = None
) -> AgentExecution:
    """
    Run the full agent loop and return an AgentExecution result.
    """

    contents = _build_contents(message, history)
    execution = AgentExecution(response="", iterations=0)

    for iteration in range(1, AGENT_MAX_ITERATIONS + 1):

        execution.iterations = iteration

        print(f"\n[AGENT] Iteration {iteration}/{AGENT_MAX_ITERATIONS}")

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=AGENT_SYSTEM_INSTRUCTION,
                temperature=AGENT_TEMPERATURE,
                tools=[ALL_TOOLS]
            )
        )

        # -------------------------------------------------
        # Check for a tool call
        # -------------------------------------------------

        function_call = None

        for part in response.candidates[0].content.parts:
            if part.function_call:
                function_call = part.function_call
                break

        # -------------------------------------------------
        # No tool call — agent has its final answer
        # -------------------------------------------------

        if not function_call:

            text = response.text

            if not text:
                text = "I was unable to generate a response."

            execution.response = text

            print(f"[AGENT] Final answer produced at iteration {iteration}")

            return execution

        # -------------------------------------------------
        # Execute the tool
        # -------------------------------------------------

        tool_name = function_call.name
        args = dict(function_call.args)

        print(f"[AGENT] Calling tool: {tool_name} args={args}")

        tool_result = execute_tool(
            tool_name=tool_name,
            args=args,
            document_id=document_id
        )

        success = "error" not in tool_result

        # Track this tool call
        execution.tool_calls.append(
            ToolCall(
                tool_name=tool_name,
                args=args,
                result=tool_result,
                success=success
            )
        )

        # Track RAG sources from document search
        if tool_name == "document_search" and success:
            sources = tool_result.get("results", [])
            for source in sources:
                execution.rag_sources.append({
                    "file_name": source.get("file_name"),
                    "chunk_index": source.get("chunk_index"),
                    "distance": source.get("distance"),
                    "text_preview": source.get("text", "")[:200]
                })

        # Track image result
        if (
            tool_name == "image_generation"
            and success
            and tool_result.get("type") == "image"
        ):
            execution.image_result = tool_result

        # -------------------------------------------------
        # Add tool call + result back into the conversation
        # -------------------------------------------------

        contents.append(response.candidates[0].content)

        contents.append(
            types.Content(
                role="user",
                parts=[
                    types.Part.from_function_response(
                        name=tool_name,
                        response=tool_result
                    )
                ]
            )
        )

    # -------------------------------------------------
    # Max iterations reached
    # -------------------------------------------------

    execution.reached_max_iterations = True

    print(
        f"[AGENT] Reached max iterations ({AGENT_MAX_ITERATIONS}), "
        "forcing final response."
    )

    # Ask Gemini for a best-effort final answer
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=AGENT_SYSTEM_INSTRUCTION,
            temperature=AGENT_TEMPERATURE,
        )
    )

    execution.response = (
        response.text
        or "Reached maximum iterations without a complete answer."
    )

    return execution


# =========================================================
# Agent Stream (yields events for the frontend)
# =========================================================

def run_agent_stream(
    message: str,
    history: List[Dict[str, str]],
    document_id: str | None = None
) -> Generator[Dict, None, None]:
    """
    Run the agent loop and yield structured events for the frontend.

    Event types:
      {"type": "tool_start",  "tool": "...", "args": {...}}
      {"type": "tool_result", "tool": "...", "success": bool}
      {"type": "image",       "url": "...", "prompt": "..."}
      {"type": "text",        "content": "..."}
      {"type": "done",        "iterations": N, "sources": [...]}
      {"type": "error",       "content": "..."}
    """

    contents = _build_contents(message, history)
    iterations = 0
    rag_sources = []

    try:

        for iteration in range(1, AGENT_MAX_ITERATIONS + 1):

            iterations = iteration

            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=AGENT_SYSTEM_INSTRUCTION,
                    temperature=AGENT_TEMPERATURE,
                    tools=[ALL_TOOLS]
                )
            )

            function_call = None

            for part in response.candidates[0].content.parts:
                if part.function_call:
                    function_call = part.function_call
                    break

            # -------------------------------------------------
            # No tool call — final answer
            # -------------------------------------------------

            if not function_call:

                text = response.text or ""

                yield {
                    "type": "text",
                    "content": text
                }

                yield {
                    "type": "done",
                    "iterations": iteration,
                    "sources": rag_sources
                }

                return

            # -------------------------------------------------
            # Tool call
            # -------------------------------------------------

            tool_name = function_call.name
            args = dict(function_call.args)

            yield {
                "type": "tool_start",
                "tool": tool_name,
                "args": args
            }

            tool_result = execute_tool(
                tool_name=tool_name,
                args=args,
                document_id=document_id
            )

            success = "error" not in tool_result

            yield {
                "type": "tool_result",
                "tool": tool_name,
                "success": success
            }

            # Track RAG sources
            if tool_name == "document_search" and success:
                for src in tool_result.get("results", []):
                    rag_sources.append({
                        "file_name": src.get("file_name"),
                        "chunk_index": src.get("chunk_index"),
                        "distance": src.get("distance"),
                        "text_preview": src.get("text", "")[:200]
                    })

            # Emit image event immediately
            if (
                tool_name == "image_generation"
                and success
                and tool_result.get("type") == "image"
            ):
                yield {
                    "type": "image",
                    "url": tool_result["url"],
                    "prompt": tool_result.get("prompt", ""),
                    "model": tool_result.get("model", "")
                }

            # Feed result back
            contents.append(response.candidates[0].content)

            contents.append(
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_function_response(
                            name=tool_name,
                            response=tool_result
                        )
                    ]
                )
            )

        # -------------------------------------------------
        # Max iterations reached
        # -------------------------------------------------

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=AGENT_SYSTEM_INSTRUCTION,
                temperature=AGENT_TEMPERATURE,
            )
        )

        yield {
            "type": "text",
            "content": (
                response.text
                or "Reached maximum iterations without a complete answer."
            )
        }

        yield {
            "type": "done",
            "iterations": iterations,
            "sources": rag_sources,
            "max_iterations_reached": True
        }

    except Exception as exc:

        yield {
            "type": "error",
            "content": str(exc)
        }
