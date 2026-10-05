import base64
import io
import uuid

from huggingface_hub import InferenceClient

from app.config.settings import HUGGINGFACE_API_KEY


# =========================================================
# Hugging Face Client
# =========================================================

client = InferenceClient(
    provider="auto",
    api_key=HUGGINGFACE_API_KEY
)


# =========================================================
# Configuration
# =========================================================

IMAGE_MODEL = (
    "black-forest-labs/FLUX.1-schnell"
)


# =========================================================
# Image Generation
# =========================================================

def generate_image(
    prompt: str
) -> dict:
    """
    Generate an image using Hugging Face and
    return it as a base64 data URL.
    No disk writes required.
    """

    image = client.text_to_image(
        prompt=prompt,
        model=IMAGE_MODEL
    )

    # Save image to an in-memory buffer
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    # Encode as base64 data URL
    image_b64 = base64.b64encode(
        buffer.read()
    ).decode("utf-8")

    data_url = f"data:image/png;base64,{image_b64}"

    return {
        "type": "image",
        "url": data_url,
        "prompt": prompt,
        "model": IMAGE_MODEL
    }