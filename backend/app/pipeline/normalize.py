import io
from dataclasses import dataclass
from typing import Tuple

from PIL import Image, ImageOps

TARGET_SIZE = 768


@dataclass
class NormalizedImage:
    image: Image.Image
    original_size: Tuple[int, int]
    label_bbox: Tuple[int, int, int, int] | None = None
    notes: str = "stub: resize + exif-transpose"


def normalize(raw: bytes) -> NormalizedImage:
    img = Image.open(io.BytesIO(raw))
    original_size = img.size
    img = ImageOps.exif_transpose(img).convert("RGB")
    img.thumbnail((TARGET_SIZE, TARGET_SIZE), Image.LANCZOS)

    return NormalizedImage(image=img, original_size=original_size)
