from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import List

import httpx

from ..config import settings


@dataclass
class RemoteHit:
    slug: str
    score: float
    cos: float
    inliers: int


class CvUnavailable(RuntimeError):
    pass


_client: httpx.Client | None = None
_lock = threading.Lock()

fallbacks = 0


def _get_client() -> httpx.Client:
    global _client
    if _client is None:
        with _lock:
            if _client is None:
                # После перезапуска cv в пуле остаются мёртвые сокеты - без retries ConnectError
                _client = httpx.Client(
                    base_url=settings.cv_url,
                    timeout=settings.cv_timeout,
                    transport=httpx.HTTPTransport(retries=2),
                )
    return _client


def recognize(raw: bytes) -> List[RemoteHit]:
    try:
        r = _get_client().post("/recognize", files={"image": ("upload.jpg", raw)})
    except httpx.HTTPError as exc:
        raise CvUnavailable(str(exc)) from exc

    if r.status_code in (400, 415):
        raise OSError(_detail(r))
    if r.status_code != 200:
        raise CvUnavailable(f"CV вернул {r.status_code}: {_detail(r)}")

    return [RemoteHit(c["slug"], float(c["score"]), float(c["cos"]), int(c["inliers"]))
            for c in r.json().get("candidates", [])]


def health() -> dict:
    try:
        r = _get_client().get("/health", timeout=2.0)
        return r.json() if r.status_code == 200 else {"status": "error", "code": r.status_code}
    except httpx.HTTPError as exc:
        return {"status": "down", "error": type(exc).__name__}


def _detail(r: httpx.Response) -> str:
    try:
        return str(r.json().get("detail", r.text))
    except ValueError:
        return r.text[:200]
