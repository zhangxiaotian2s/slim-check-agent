import base64
import io
from typing import Optional
from PIL import Image
from src.utils.logger import logger

def load_image_from_file(file_path: str) -> Optional[bytes]:
    """Load image from file and return as bytes."""
    try:
        with open(file_path, "rb") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to load image from {file_path}: {e}")
        return None

def image_to_base64(image_bytes: bytes, max_size: int = 1000) -> str:
    """Convert image bytes to base64, resizing if needed for API."""
    try:
        # Open image with PIL
        image = Image.open(io.BytesIO(image_bytes))

        # Resize if larger than max_size while preserving aspect ratio
        if image.width > max_size or image.height > max_size:
            ratio = min(max_size / image.width, max_size / image.height)
            new_width = int(image.width * ratio)
            new_height = int(image.height * ratio)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            logger.debug(f"Resized image to {new_width}x{new_height}")

        # Convert to JPEG and get bytes
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=85)
        resized_bytes = buffer.getvalue()

        # Encode to base64
        return base64.b64encode(resized_bytes).decode("utf-8")

    except Exception as e:
        logger.error(f"Failed to convert image to base64: {e}")
        # Fallback: just encode original bytes
        return base64.b64encode(image_bytes).decode("utf-8")

def get_image_dimensions(image_bytes: bytes) -> tuple[int, int]:
    """Get image dimensions (width, height)."""
    try:
        image = Image.open(io.BytesIO(image_bytes))
        return image.width, image.height
    except Exception as e:
        logger.error(f"Failed to get image dimensions: {e}")
        return 0, 0
