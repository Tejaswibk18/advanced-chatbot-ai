from typing import Dict, Generator, List

from google import genai
from google.genai import types

from app.config.settings import GEMINI_API_KEY
from app.services.web_search_service import web_search
from app.services.image_generation_service import generate_image
from app.services.vector_store_service import search_documents


# =========================================================
# Gemini Client
# =========================================================

client = genai.Client(
    api_key=GEMINI_API_KEY
)


MODEL_NAME = "gemini-3.5-flash-lite"


# =========================================================
# System Instruction
# =========================================================

SYSTEM_INSTRUCTION = """
You are a helpful general information assistant.

Your responsibilities:

- Answer questions clearly and accurately.
- Explain difficult concepts in simple language.
- Give examples when useful.
- If you are unsure about something, say so.
- Do not invent facts.
- Keep responses structured and easy to understand.


WEB SEARCH:

- Use the web_search tool when the question requires
  current, recent, changing, or web-based information.
- Do not use web search for questions that can be answered
  reliably from your existing knowledge.
- When you use web search, base your answer on the
  information returned by the tool.
- Do not claim that you searched the web if you did not.


IMAGE GENERATION:

- Use the image_generation tool when the user explicitly
  asks you to generate, create, draw, or visualize an image.
- Do not use image generation when the user is only asking
  about images, image generation, or visual concepts.
- Create a clear and detailed image prompt from the user's
  request.


DOCUMENT SEARCH:

- Use document_search when the user asks about information
  contained in their uploaded document.
- Use document_search when the user asks to summarize
  an uploaded document.
- Do not use web_search when the answer can be obtained
  from the uploaded document.
- When answering from documents, base the answer on
  the retrieved document content.
- If the retrieved content is insufficient, clearly say
  that the document does not contain enough information.
- Never invent information that is not present in the
  retrieved document content.
"""


# =========================================================
# Web Search Tool
# =========================================================

WEB_SEARCH_TOOL = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="web_search",
            description=(
                "Search the internet for current or "
                "relevant information. Use this when "
                "the user asks about recent events, "
                "current information, news, prices, "
                "latest versions, weather, or information "
                "that may have changed."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "A concise web search query."
                        )
                    }
                },
                "required": [
                    "query"
                ]
            }
        )
    ]
)


# =========================================================
# Image Generation Tool
# =========================================================

IMAGE_GENERATION_TOOL = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="image_generation",
            description=(
                "Generate an image from a textual "
                "description. Use this when the user "
                "explicitly asks to create, generate, "
                "draw, or visualize an image."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": (
                            "A detailed description of "
                            "the image that should be generated."
                        )
                    }
                },
                "required": [
                    "prompt"
                ]
            }
        )
    ]
)


# =========================================================
# Document Search Tool
# =========================================================

DOCUMENT_SEARCH_TOOL = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="document_search",
            description=(
                "Search the user's currently selected "
                "uploaded document for relevant information. "
                "Use this when the user asks questions about "
                "their uploaded document or asks to summarize it."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "The question or information "
                            "to search for in the document."
                        )
                    }
                },
                "required": [
                    "query"
                ]
            }
        )
    ]
)


# =========================================================
# Build Gemini Contents
# =========================================================

def build_contents(
    message: str,
    history: List[Dict[str, str]]
):
    """
    Build the conversation contents that are sent to Gemini.
    """

    contents = []

    for item in history:

        contents.append(
            types.Content(
                role=item["role"],
                parts=[
                    types.Part(
                        text=item["content"]
                    )
                ]
            )
        )

    contents.append(
        types.Content(
            role="user",
            parts=[
                types.Part(
                    text=message
                )
            ]
        )
    )

    return contents


# =========================================================
# Execute Tool
# =========================================================

def execute_tool_call(
    function_call,
    document_id: str | None = None
) -> dict:
    """
    Execute the tool requested by Gemini.

    document_id is supplied by the backend and is not
    selected by Gemini.
    """

    # -----------------------------------------------------
    # Web Search
    # -----------------------------------------------------

    if function_call.name == "web_search":

        query = function_call.args.get(
            "query"
        )

        if not query:

            return {
                "error": (
                    "Search query was not provided."
                )
            }

        print(
            f"\n[TOOL] web_search: {query}"
        )

        result = web_search(
            query
        )

        print(
            "[TOOL] web_search completed"
        )

        return result


    # -----------------------------------------------------
    # Image Generation
    # -----------------------------------------------------

    if function_call.name == "image_generation":

        prompt = function_call.args.get(
            "prompt"
        )

        if not prompt:

            return {
                "error": (
                    "Image generation prompt "
                    "was not provided."
                )
            }

        print(
            f"\n[TOOL] image_generation: {prompt}"
        )

        result = generate_image(
            prompt
        )

        print(
            "[TOOL] image_generation completed"
        )

        return result


    # -----------------------------------------------------
    # Document Search
    # -----------------------------------------------------

    if function_call.name == "document_search":

        query = function_call.args.get(
            "query"
        )

        if not query:

            return {
                "error": (
                    "Document search query "
                    "was not provided."
                )
            }

        if not document_id:

            return {
                "error": (
                    "No document is currently "
                    "associated with this conversation."
                )
            }

        print(
            f"\n[TOOL] document_search: {query}"
        )

        print(
            f"[TOOL] document_id: {document_id}"
        )

        result = search_documents(
            query=query,
            n_results=5,
            document_id=document_id
        )

        print(
            "[TOOL] document_search completed"
        )

        return result


    # -----------------------------------------------------
    # Unknown Tool
    # -----------------------------------------------------

    return {
        "error": (
            f"Unknown tool: "
            f"{function_call.name}"
        )
    }


# =========================================================
# Add Tool Result
# =========================================================

def add_tool_result(
    contents,
    response,
    function_call,
    tool_result
):
    """
    Add Gemini's tool call and the tool result
    back into the conversation.
    """

    contents.append(
        response.candidates[0].content
    )

    function_response_part = (
        types.Part.from_function_response(
            name=function_call.name,
            response=tool_result
        )
    )

    contents.append(
        types.Content(
            role="user",
            parts=[
                function_response_part
            ]
        )
    )


# =========================================================
# Generate Response
# =========================================================

def generate_response(
    message: str,
    history: List[Dict[str, str]],
    document_id: str | None = None
) -> str:
    """
    Generate a response using Gemini and the available tools.
    """

    contents = build_contents(
        message,
        history
    )

    while True:

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,

                tools=[
                    WEB_SEARCH_TOOL,
                    IMAGE_GENERATION_TOOL,
                    DOCUMENT_SEARCH_TOOL
                ]
            )
        )

        function_call = None

        for part in response.candidates[0].content.parts:

            if part.function_call:

                function_call = (
                    part.function_call
                )

                break


        # -------------------------------------------------
        # No Tool Call
        # -------------------------------------------------

        if not function_call:

            if not response.text:

                raise RuntimeError(
                    "Gemini returned an empty response."
                )

            return response.text


        # -------------------------------------------------
        # Execute Tool
        # -------------------------------------------------

        tool_result = execute_tool_call(
            function_call,
            document_id=document_id
        )


        # -------------------------------------------------
        # Send Tool Result Back To Gemini
        # -------------------------------------------------

        add_tool_result(
            contents=contents,
            response=response,
            function_call=function_call,
            tool_result=tool_result
        )


# =========================================================
# Generate Stream
# =========================================================

def generate_stream(
    message: str,
    history: List[Dict[str, str]],
    document_id: str | None = None
) -> Generator[dict, None, None]:
    """
    Generate a response using Gemini tools and yield
    structured events for the frontend.
    """

    contents = build_contents(
        message,
        history
    )

    while True:

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,

                tools=[
                    WEB_SEARCH_TOOL,
                    IMAGE_GENERATION_TOOL,
                    DOCUMENT_SEARCH_TOOL
                ]
            )
        )

        function_call = None

        for part in response.candidates[0].content.parts:

            if part.function_call:

                function_call = (
                    part.function_call
                )

                break


        # -------------------------------------------------
        # No Tool Call
        # -------------------------------------------------

        if not function_call:

            if not response.text:

                raise RuntimeError(
                    "Gemini returned an empty response."
                )

            yield {
                "type": "text",
                "content": response.text
            }

            return


        # -------------------------------------------------
        # Execute Tool
        # -------------------------------------------------

        tool_result = execute_tool_call(
            function_call,
            document_id=document_id
        )


        # -------------------------------------------------
        # Image Result
        # -------------------------------------------------

        if (
            function_call.name ==
            "image_generation"
        ):

            if tool_result.get("type") == "image":

                yield {
                    "type": "image",
                    "url": tool_result["url"],
                    "prompt": tool_result.get(
                        "prompt",
                        ""
                    ),
                    "model": tool_result.get(
                        "model",
                        ""
                    )
                }


        # -------------------------------------------------
        # Send Tool Result Back To Gemini
        # -------------------------------------------------

        add_tool_result(
            contents=contents,
            response=response,
            function_call=function_call,
            tool_result=tool_result
        )