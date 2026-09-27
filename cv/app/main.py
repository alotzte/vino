from __future__ import annotations

import logging

from fastapi import FastAPI, File, HTTPException, UploadFile
from PIL import UnidentifiedImageError

from .config import settings
from .pipeline import Pipeline

log = logging.getLogger("vino.cv")
app = FastAPI(title="vino-cv", docs_url="/docs")

PIPE: Pipeline | None = None


@app.on_event("startup")
def _load():
    global PIPE
    PIPE = Pipeline()
    log.warning("каскад готов за %s с, эталонов %s", PIPE.load_s, len(PIPE.index))


@app.get("/health")
def health():
    if PIPE is None:
        raise HTTPException(status_code=503, detail="модели ещё грузятся")
    return PIPE.health()


@app.post("/recognize")
def recognize(image: UploadFile = File(...)):
    if PIPE is None:
        raise HTTPException(status_code=503, detail="модели ещё грузятся")

    raw = image.file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Пустой файл")
    if len(raw) > settings.max_bytes:
        raise HTTPException(status_code=413, detail="Файл слишком большой")

    try:
        result = PIPE.run(raw)
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise HTTPException(status_code=415, detail=f"Не удалось прочитать изображение: {exc}")

    return {
        "candidates": result.candidates,
        "crop_conf": result.crop_conf,
        "sat": result.sat,
        "rotation": result.rotation,
        "stages_ms": result.stages_ms,
    }
