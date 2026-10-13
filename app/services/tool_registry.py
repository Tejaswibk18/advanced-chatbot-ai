"""
Tool Registry — Phase 5

Centralizes all tool definitions and their execution logic.
New tools should be registered here and nowhere else.
"""

from typing import Any, Callable, Dict

from google.genai import types

from app.services.web_search_service import web_search
from app.services.image_generation_service import generate_image
from app.services.vector_store_service import search_documents


# =========================================================
# Tool Definitions (Gemini function declarations)
# =========================================================

_WEB_SEARCH_DECLARATION = types.FunctionDeclaration(
    name="web_search",
    description=(
        "Search the internet for current or recent information. "
        "Use when the user asks about news, prices, latest versions, "
        "weather, events, or any information that may have changed."
    ),
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "A concise web search query."
            }
        },
        "required": ["query"]
    }
)

_IMAGE_GENERATION_DECLARATION = types.FunctionDeclaration(
    name="image_generation",
    description=(
        "Generate an image from a textual description. "
        "Use when the user explicitly asks to create, generate, "
        "draw, or visualize an image."
    ),
    parameters={
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string",
                "description": (
                    "A detailed description of the image to generate."
                )
            }
        },
        "required": ["prompt"]
    }
)

_DOCUMENT_SEARCH_DECLARATION = types.FunctionDeclaration(
    name="document_search",
    description=(
        "Search the user's uploaded document for relevant information. "
        "Use when the user asks questions about their document or "
        "asks to summarize it."
    ),
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": (
                    "The question or topic to look up in the document."
                )
            }
        },
        "required": ["query"]
    }
)


# =========================================================
# Gemini Tool Objects
# =========================================================

ALL_TOOLS = types.Tool(
    function_declarations=[
        _WEB_SEARCH_DECLARATION,
        _IMAGE_GENERATION_DECLARATION,
        _DOCUMENT_SEARCH_DECLARATION,
    ]
)


# =========================================================
# Tool Registry — maps tool name → executor function
# =========================================================

def _execute_web_search(
    args: Dict[str, Any],
    **kwargs
) -> Dict:
    query = args.get("query", "")
    if not query:
        return {"error": "Search query was not provided."}
    print(f"[TOOL] web_search: {query}")
    result = web_search(query)
    print("[TOOL] web_search completed")
    return result


def _execute_image_generation(
    args: Dict[str, Any],
    **kwargs
) -> Dict:
    prompt = args.get("prompt", "")
    if not prompt:
        return {"error": "Image generation prompt was not provided."}
    print(f"[TOOL] image_generation: {prompt}")
    result = generate_image(prompt)
    print("[TOOL] image_generation completed")
    return result


def _execute_document_search(
    args: Dict[str, Any],
    document_id: str | None = None,
    **kwargs
) -> Dict:
    query = args.get("query", "")
    if not query:
        return {"error": "Document search query was not provided."}
    if not document_id:
        return {
            "error": (
                "No document is currently associated "
                "with this conversation."
            )
        }
    print(f"[TOOL] document_search: {query} (doc={document_id})")
    result = search_documents(
        query=query,
        n_results=5,
        document_id=document_id
    )
    print("[TOOL] document_search completed")
    return result


# Registry: tool name → executor callable
TOOL_REGISTRY: Dict[str, Callable] = {
    "web_search":        _execute_web_search,
    "image_generation":  _execute_image_generation,
    "document_search":   _execute_document_search,
}


def execute_tool(
    tool_name: str,
    args: Dict[str, Any],
    document_id: str | None = None
) -> Dict:
    """
    Look up and execute a tool by name.
    Returns a dict with the tool result (or an error key on failure).
    """
    executor = TOOL_REGISTRY.get(tool_name)

    if not executor:
        return {"error": f"Unknown tool: {tool_name}"}

    try:
        return executor(
            args=args,
            document_id=document_id
        )
    except Exception as exc:
        print(f"[TOOL] {tool_name} failed: {exc}")
        return {"error": str(exc)}
