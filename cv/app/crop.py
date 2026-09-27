from __future__ import annotations

import io
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps

# iPhone по умолчанию снимает в HEIC, а организаторы шлют исходники с телефонов
try:
    from pillow_heif import register_heif_opener

    register_heif_opener()
except ImportError:
    pass

MAX_SIDE = 2048


class BottleCropper:
    # book - этикетка во весь кадр; внутри бутылки отбрасываем, эталоны - целые бутылки

    BOTTLE, BOOK = 39, 73

    def __init__(self, weights: str, device: str):
        from ultralytics import YOLO

        self.model = YOLO(weights)
        self.device = device

    def __call__(self, im: Image.Image, pad: float = 0.04) -> tuple[Image.Image, float]:
        W, H = im.size
        small = im.copy()
        small.thumbnail((1024, 1024))
        k = W / small.size[0]
        res = self.model.predict(small, classes=[self.BOTTLE, self.BOOK], conf=0.15,
                                 verbose=False, device=self.device)[0]
        if res.boxes is None or len(res.boxes) == 0:
            return im, 0.0
        boxes = res.boxes.xyxy.cpu().numpy() * k
        confs, classes = res.boxes.conf.cpu().numpy(), res.boxes.cls.cpu().numpy().astype(int)
        bottles = boxes[(classes == self.BOTTLE) & (confs >= 0.3)]

        def inside_bottle(b):
            for x1, y1, x2, y2 in bottles:
                iw = max(0, min(b[2], x2) - max(b[0], x1))
                ih = max(0, min(b[3], y2) - max(b[1], y1))
                if iw * ih >= 0.8 * (b[2] - b[0]) * (b[3] - b[1]):
                    return True
            return False

        best, best_score, best_conf = None, -1.0, 0.0
        for (x1, y1, x2, y2), conf, cls in zip(boxes, confs, classes):
            if cls == self.BOOK and inside_bottle((x1, y1, x2, y2)):
                continue
            area = (x2 - x1) * (y2 - y1) / (W * H)
            cx, cy = (x1 + x2) / 2 / W, (y1 + y2) / 2 / H
            centrality = 1.0 - min(1.0, np.hypot(cx - 0.5, cy - 0.5) / 0.7)
            score = float(conf) * np.sqrt(area) * centrality ** 2
            if score > best_score:
                best, best_score, best_conf = (x1, y1, x2, y2), score, float(conf)
        if best is None:
            return im, 0.0
        x1, y1, x2, y2 = best
        px, py = (x2 - x1) * pad, (y2 - y1) * pad
        box = (max(0, x1 - px), max(0, y1 - py), min(W, x2 + px), min(H, y2 + py))
        return im.crop(tuple(int(v) for v in box)), best_conf


def load_reference(path: Path, fill=(255, 255, 255)) -> Image.Image:
    im = Image.open(path).convert("RGBA")
    bbox = im.getchannel("A").point(lambda a: 255 if a > 10 else 0).getbbox()
    if bbox:
        im = im.crop(bbox)
    bg = Image.new("RGBA", im.size, fill + (255,))
    bg.alpha_composite(im)
    return bg.convert("RGB")


def decode(raw: bytes, max_side: int = MAX_SIDE) -> Image.Image:
    im = Image.open(io.BytesIO(raw))
    im.draft("RGB", (max_side, max_side))
    im = ImageOps.exif_transpose(im)
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
        bg.alpha_composite(im)
        im = bg
    im = im.convert("RGB")
    im.thumbnail((max_side, max_side), Image.LANCZOS)
    return im


def rgb_side(im: Image.Image, side: int) -> Image.Image:
    # Не thumbnail: он только уменьшает, и мелкие эталоны проигрывали переранжирование
    k = side / max(im.size)
    return im.resize((max(1, round(im.size[0] * k)), max(1, round(im.size[1] * k))), Image.LANCZOS)


def saturation(im: Image.Image) -> float:
    import cv2

    a = np.asarray(im.convert("RGB"))
    return float(cv2.cvtColor(a, cv2.COLOR_RGB2HSV)[..., 1].mean() / 255)
