import os

from dotenv import load_dotenv


load_dotenv()


# =========================================================
# API Keys
# =========================================================

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


# =========================================================
# Agent Settings (Phase 5)
# =========================================================

# Max number of tool-call iterations before the agent
# is forced to stop and return whatever it has.
AGENT_MAX_ITERATIONS = int(
    os.getenv("AGENT_MAX_ITERATIONS", "10")
)

# Temperature for agent response generation
AGENT_TEMPERATURE = float(
    os.getenv("AGENT_TEMPERATURE", "0.7")
)


# =========================================================
# Memory Settings (Phase 6)
# =========================================================

# Total messages to keep per conversation in the DB
MEMORY_MAX_MESSAGES = int(
    os.getenv("MEMORY_MAX_MESSAGES", "100")
)

# Number of most-recent messages to send to the model
# as short-term context on each turn
MEMORY_RELEVANT_MESSAGES = int(
    os.getenv("MEMORY_RELEVANT_MESSAGES", "20")
)