import os
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer


# Use DATA_DIR env variable if set (e.g. Render persistent disk at /data),
# otherwise fall back to the project root for local development.
DATA_DIR = Path(os.environ.get("DATA_DIR", Path(__file__).resolve().parents[2]))

CHROMA_DB_DIR = DATA_DIR / "chroma_db"


# Persistent ChromaDB client
chroma_client = chromadb.PersistentClient(
    path=str(CHROMA_DB_DIR)
)


# Collection where document chunks are stored
collection = chroma_client.get_or_create_collection(
    name="documents"
)


# Local embedding model
embedding_model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)


def create_embeddings(
    texts: list[str]
) -> list[list[float]]:
    """
    Convert text chunks into embeddings.
    """

    embeddings = embedding_model.encode(
        texts
    )

    return embeddings.tolist()


def store_document_chunks(
    document_id: str,
    file_name: str,
    chunks: list[str]
) -> int:
    """
    Create embeddings and store document
    chunks in ChromaDB.
    """

    if not chunks:
        return 0

    embeddings = create_embeddings(
        chunks
    )

    ids = [
        f"{document_id}_{index}"
        for index in range(len(chunks))
    ]

    metadata = [
        {
            "document_id": document_id,
            "file_name": file_name,
            "chunk_index": index
        }
        for index in range(len(chunks))
    ]

    collection.add(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadata
    )

    return len(chunks)

def search_documents(
    query: str,
    n_results: int = 5,
    document_id: str | None = None
) -> dict:
    """
    Search uploaded document chunks using
    semantic similarity.
    """

    query_embedding = create_embeddings(
        [query]
    )[0]

    where_filter = None

    if document_id:
        where_filter = {
            "document_id": document_id
        }

    results = collection.query(
        query_embeddings=[
            query_embedding
        ],
        n_results=n_results,
        where=where_filter
    )

    documents = results.get(
        "documents",
        [[]]
    )[0]

    metadatas = results.get(
        "metadatas",
        [[]]
    )[0]

    distances = results.get(
        "distances",
        [[]]
    )[0]

    search_results = []

    for index, document in enumerate(documents):

        metadata = metadatas[index]

        search_results.append({
            "text": document,
            "file_name": metadata.get(
                "file_name"
            ),
            "document_id": metadata.get(
                "document_id"
            ),
            "chunk_index": metadata.get(
                "chunk_index"
            ),
            "distance": distances[index]
            if index < len(distances)
            else None
        })

    return {
        "query": query,
        "results": search_results
    }