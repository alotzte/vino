from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from . import appdb
from .api.routes import router
from .config import settings

_HERE = Path(__file__).resolve()
FRONTEND_DIR = next(
    (
        c
        for c in (
            _HERE.parent.parent / "frontend",
            _HERE.parent.parent.parent / "frontend" / "dist",
            _HERE.parent.parent.parent / "frontend",
        )
        if (c / "index.html").exists()
    ),
    _HERE.parent.parent / "frontend",
)

app = FastAPI(
    title="Своё Вино - сканер этикеток",
    version="0.1.0",
    root_path=settings.root_path,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.on_event("startup")
def _init_app_db():
    appdb.init_db()


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/static/{path:path}", include_in_schema=False)
def static_files(path: str):
    """Отдаём фронтенд явным роутом: StaticFiles-mount конфликтует с root_path."""
    static_root = (FRONTEND_DIR / "static").resolve()
    target = (static_root / path).resolve()
    if not target.is_file() or static_root not in target.parents:
        raise HTTPException(status_code=404, detail="Not Found")
    return FileResponse(target, headers={"Cache-Control": "public, max-age=300"})
