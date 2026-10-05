# AI Information Assistant

A conversational AI chatbot powered by **Google Gemini** that can answer questions, search the web for real-time information, generate images, and analyze uploaded documents — all from a clean web interface.

---

## Features

- 💬 **Multi-turn Chat** — Persistent conversation history with support for multiple sessions
- 🔍 **Web Search** — Automatically searches the web using Tavily when questions need up-to-date information
- 🖼️ **Image Generation** — Generates images via Hugging Face (FLUX.1-schnell) from natural language prompts
- 📄 **Document Q&A** — Upload PDF, DOCX, or TXT files and ask questions about them using semantic search (ChromaDB + sentence-transformers)
- 🧠 **Gemini 3.5** — Powered by `gemini-3.5-flash-lite` with function-calling for tool use

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI |
| LLM | Google Gemini (`gemini-3.5-flash-lite`) |
| Web Search | Tavily API |
| Image Generation | Hugging Face Inference API (FLUX.1-schnell) |
| Vector Store | ChromaDB + sentence-transformers (`all-MiniLM-L6-v2`) |
| Database | SQLite |
| Frontend | HTML, CSS, Vanilla JS + Jinja2 Templates |

---

## Project Structure

```
ai-information-assistant/
├── app/
│   ├── config/
│   │   └── settings.py          # Loads env variables
│   ├── database/
│   │   └── database.py          # SQLite setup & connection
│   ├── routes/
│   │   ├── chat.py              # Chat API endpoints
│   │   └── documents.py         # Document upload endpoints
│   ├── schemas/
│   │   └── chat.py              # Pydantic request/response models
│   ├── services/
│   │   ├── llm_service.py       # Gemini LLM with tool calling
│   │   ├── chat_history_service.py  # Conversation management
│   │   ├── document_service.py  # File saving & text extraction
│   │   ├── document_chunker.py  # Text chunking for embeddings
│   │   ├── vector_store_service.py  # ChromaDB embeddings & search
│   │   ├── web_search_service.py    # Tavily web search
│   │   └── image_generation_service.py  # HuggingFace image gen
│   └── main.py                  # FastAPI app entry point
├── static/                      # CSS, JS, static assets
├── templates/                   # Jinja2 HTML templates
├── .env                         # Environment variables (not committed)
├── requirements.txt
└── README.md
```

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/Tejaswibk18/advanced-chatbot-ai.git
cd advanced-chatbot-ai
```

### 2. Create a virtual environment

```bash
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate  # macOS/Linux
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key
TAVILY_API_KEY=your_tavily_api_key
HUGGINGFACE_API_KEY=your_huggingface_api_key
```

| Variable | Where to get it |
|---|---|
| `GEMINI_API_KEY` | [Google AI Studio](https://aistudio.google.com/app/apikey) |
| `TAVILY_API_KEY` | [Tavily](https://tavily.com) |
| `HUGGINGFACE_API_KEY` | [Hugging Face Settings](https://huggingface.co/settings/tokens) |

### 5. Run the app

```bash
uvicorn app.main:app --reload
```

Open your browser at **http://localhost:8000**

---

## Deployment on Render

### 1. Push your code to GitHub

### 2. Create a Web Service on Render
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port 10000`

### 3. Add Environment Variables on Render
```
GEMINI_API_KEY=...
TAVILY_API_KEY=...
HUGGINGFACE_API_KEY=...
DATA_DIR=/data
```

### 4. Add a Persistent Disk
- Go to **Disks** in your Render service settings
- Mount Path: `/data`

> The app uses `DATA_DIR` to store the SQLite database, ChromaDB vector store, uploaded documents, and generated images on the persistent disk so data is not lost on restarts.
