from fastapi import FastAPI, Request

from fastapi.staticfiles import StaticFiles

from fastapi.templating import Jinja2Templates

from app.database.database import (
    initialize_database
)

from app.routes.chat import (
    router as chat_router
)


# ---------------------------------------------------------
# Initialize database
# ---------------------------------------------------------

initialize_database()


# ---------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------

app = FastAPI(
    title="AI Information Assistant",
    description=(
        "Simple general information "
        "chatbot powered by Gemini"
    ),
    version="1.0.0"
)


# ---------------------------------------------------------
# Static files
# ---------------------------------------------------------

app.mount(
    "/static",
    StaticFiles(
        directory="static"
    ),
    name="static"
)


# ---------------------------------------------------------
# Templates
# ---------------------------------------------------------

templates = Jinja2Templates(
    directory="templates"
)


# ---------------------------------------------------------
# Routes
# ---------------------------------------------------------

app.include_router(
    chat_router
)


# ---------------------------------------------------------
# Home
# ---------------------------------------------------------

@app.get("/")
async def home(
    request: Request
):

    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )