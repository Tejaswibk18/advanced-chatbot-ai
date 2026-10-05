from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.database.database import initialize_database
from app.routes.chat import router as chat_router 
from app.routes.documents import router as documents_router

initialize_database()


app = FastAPI(
    title="AI Information Assistant",
    description="Simple general information chatbot powered by Gemini",
    version="1.0.0"
)


app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)


app.mount(
    "/generated-images",
    StaticFiles(directory="generated_images"),
    name="generated-images"
)

templates = Jinja2Templates(
    directory="templates"
)


app.include_router(
    chat_router
)

app.include_router(
    documents_router
)


@app.get("/")
async def home(
    request: Request
):
    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )