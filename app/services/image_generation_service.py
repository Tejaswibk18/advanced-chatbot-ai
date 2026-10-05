from pathlib import Path

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


BASE_DIR = Path(__file__).resolve().parents[2]

GENERATED_IMAGES_DIR = (
    BASE_DIR / "generated_images"
)


GENERATED_IMAGES_DIR.mkdir(
    exist_ok=True
)


# =========================================================
# Image Generation
# =========================================================

def generate_image(
    prompt: str
) -> dict:
    """
    Generate an image using Hugging Face
    and save it locally.
    """

    image = client.text_to_image(
        prompt=prompt,
        model=IMAGE_MODEL
    )

    # Generate a simple unique filename.
    existing_images = list(
        GENERATED_IMAGES_DIR.glob(
            "generated_*.png"
        )
    )

    image_number = (
        len(existing_images) + 1
    )

    file_name = (
        f"generated_{image_number}.png"
    )

    file_path = (
        GENERATED_IMAGES_DIR / file_name
    )

    image.save(
        file_path
    )

    return {
        "type": "image",
        "file_name": file_name,
        "url": (
            f"/generated-images/"
            f"{file_name}"
        ),
        "prompt": prompt,
        "model": IMAGE_MODEL
    }