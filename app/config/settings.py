import os

from dotenv import load_dotenv


load_dotenv()


GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY"
)

TAVILY_API_KEY = os.getenv(
    "TAVILY_API_KEY"
)

HUGGINGFACE_API_KEY = os.getenv(
    "HUGGINGFACE_API_KEY"
)


if not GEMINI_API_KEY:
    raise ValueError(
        "GEMINI_API_KEY is not set in the environment."
    )


if not TAVILY_API_KEY:
    raise ValueError(
        "TAVILY_API_KEY is not set in the environment."
    )


if not HUGGINGFACE_API_KEY:
    raise ValueError(
        "HUGGINGFACE_API_KEY is not set in the environment."
    )