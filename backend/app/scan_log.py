import hashlib
import json
import logging
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional

from .config import settings
from .pipeline import SearchResult

log = logging.getLogger(__name__)

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif", ".bmp", ".gif", ".tif", ".tiff"}

SCHEMA = """
CREATE TABLE IF NOT EXISTS uploads (
    id INTEGER PRIMARY KEY,
    created_at TEXT NOT NULL,
    endpoint TEXT NOT NULL,
    flat INTEGER NOT NULL DEFAULT 0,
    status INTEGER NOT NULL,
    user_id INTEGER,
    user_agent TEXT,
    filename TEXT,
    size INTEGER NOT NULL,
    sha256 TEXT NOT NULL,
    image_path TEXT NOT NULL,
    slug TEXT,
    top_slug TEXT,
    found INTEGER,
    confidence REAL,
    engine TEXT,
    elapsed_ms INTEGER,
    candidates TEXT
);
CREATE INDEX IF NOT EXISTS uploads_created_at ON uploads (created_at);
CREATE INDEX IF NOT EXISTS uploads_sha256 ON uploads (sha256);
"""

_lock = threading.Lock()
_conn: Optional[sqlite3.Connection] = None


def _connect() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        settings.scan_log_dir.mkdir(parents=True, exist_ok=True)
        _conn = sqlite3.connect(settings.scan_log_dir / "uploads.db", check_same_thread=False)
        _conn.execute("PRAGMA journal_mode=WAL")
        _conn.execute("PRAGMA synchronous=NORMAL")
        _conn.executescript(SCHEMA)
    return _conn


def _save_image(raw: bytes, digest: str, filename: Optional[str]) -> str:
    suffix = Path(filename or "").suffix.lower()
    if suffix not in IMAGE_SUFFIXES:
        suffix = ".bin"
    # по хешу: скрипт оценки шлёт одни и те же фото на каждом прогоне
    rel = Path("images") / digest[:2] / f"{digest}{suffix}"
    path = settings.scan_log_dir / rel
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".part")
        tmp.write_bytes(raw)
        tmp.replace(path)
    return str(rel)


def record(
    raw: bytes,
    *,
    endpoint: str,
    status: int,
    filename: Optional[str] = None,
    flat: bool = False,
    user_id: Optional[int] = None,
    user_agent: Optional[str] = None,
    result: Optional[SearchResult] = None,
) -> None:
    if not settings.scan_log_enabled:
        return
    try:
        digest = hashlib.sha256(raw).hexdigest()
        row = {
            "created_at": datetime.now().isoformat(timespec="milliseconds"),
            "endpoint": endpoint,
            "flat": int(flat),
            "status": status,
            "user_id": user_id,
            "user_agent": user_agent,
            "filename": filename,
            "size": len(raw),
            "sha256": digest,
            "image_path": _save_image(raw, digest, filename),
        }
        if result is not None:
            row.update(
                slug=result.slug,
                top_slug=result.top_slug,
                found=int(result.found),
                confidence=result.confidence,
                engine=result.engine,
                elapsed_ms=result.elapsed_ms,
                candidates=json.dumps([{"slug": c.slug, "score": c.score} for c in result.candidates]),
            )
        columns = ", ".join(row)
        placeholders = ", ".join(f":{k}" for k in row)
        with _lock:
            conn = _connect()
            conn.execute(f"INSERT INTO uploads ({columns}) VALUES ({placeholders})", row)
            conn.commit()
    except Exception:
        # журнал не должен ронять скан
        log.exception("Не удалось сохранить загрузку в журнал")
