from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        description="Message sent by the user"
    )

    conversation_id: str = Field(
        ...,
        min_length=1,
        description="Unique ID of the conversation"
    )

    document_id: str | None = Field(
        default=None,
        description=(
            "ID of the document currently "
            "associated with this conversation"
        )
    )


class ChatResponse(BaseModel):
    conversation_id: str
    response: str