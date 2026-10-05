from uuid import uuid4

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException
)

from app.services.document_service import (
    save_document,
    extract_text
)

from app.services.document_chunker import (
    chunk_text
)

from app.services.vector_store_service import (
    store_document_chunks
)


router = APIRouter(
    prefix="/documents",
    tags=["Documents"]
)


ALLOWED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".txt"
}


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...)
):
    """
    Upload a document, extract its text,
    split it into chunks, generate embeddings,
    and store the chunks in ChromaDB.
    """

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="File name is required."
        )

    extension = (
        "." +
        file.filename.split(".")[-1].lower()
    )

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported file type. "
                "Only PDF, DOCX and TXT files "
                "are allowed."
            )
        )

    file_content = await file.read()

    if not file_content:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty."
        )

    try:
        # Generate unique ID for this document
        document_id = str(uuid4())

        # Save uploaded document
        file_path = save_document(
            file.filename,
            file_content
        )

        # Extract text
        text = extract_text(
            file_path
        )

        if not text.strip():
            raise HTTPException(
                status_code=400,
                detail=(
                    "No readable text was found "
                    "in the document."
                )
            )

        # Split text into chunks
        chunks = chunk_text(
            text
        )

        if not chunks:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Could not create document "
                    "chunks."
                )
            )

        # Generate embeddings and store
        # chunks in ChromaDB
        stored_chunks = store_document_chunks(
            document_id=document_id,
            file_name=file.filename,
            chunks=chunks
        )

        return {
            "message": (
                "Document uploaded and "
                "processed successfully."
            ),
            "document_id": document_id,
            "file_name": file.filename,
            "characters": len(text),
            "chunks": stored_chunks,
            "preview": text[:1000]
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )