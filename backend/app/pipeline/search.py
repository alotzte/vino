import logging
import time
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from ..config import settings
from ..schemas import Candidate
from .. import catalog
from .embedder import get_embedder
from .index import get_index
from .normalize import normalize
from . import remote
from .remote import CvUnavailable, recognize

log = logging.getLogger("vino.search")


@dataclass
class SearchResult:
    slug: Optional[str]
    found: bool
    confidence: float
    f1_top1: float
    f1_top5: float
    elapsed_ms: int
    engine: str
    candidates: List[Candidate] = field(default_factory=list)
    top_slug: Optional[str] = None


def _f1(score: float) -> float:
    """Пока скор и есть прокси F1. Реальная метрика считается на валидации."""
    return round(min(max(score, 0.0), 1.0), 4)


def _local_hits(raw: bytes, top_k: int) -> Tuple[List[Tuple[str, float]], List[float]]:
    normalized = normalize(raw)
    vector = get_embedder(settings.engine).embed(normalized)
    hits = get_index(settings.engine).query(vector, top_k=top_k)
    return hits, [score for _, score in hits]


def search_by_image(raw: bytes, top_k: int | None = None) -> SearchResult:
    started = time.perf_counter()
    top_k = top_k or settings.top_k
    engine = settings.engine

    if engine == "remote":
        try:
            remote_hits = recognize(raw)
            hits = [(h.slug, h.score) for h in remote_hits]
            confidences = [h.cos for h in remote_hits]
        except CvUnavailable as exc:
            if not settings.cv_fallback_stub:
                raise
            remote.fallbacks += 1
            log.error("CV недоступен (%s), отвечаю заглушкой - ответ не настоящий", exc)
            engine = "stub"
            hits, confidences = _local_hits(raw, top_k)
    else:
        hits, confidences = _local_hits(raw, top_k)

    wines = catalog.get_many([slug for slug, _ in hits])
    candidates, conf_by_slug = [], {}
    for (slug, score), conf in zip(hits, confidences):
        if slug not in wines:
            continue
        candidates.append(Candidate(
            slug=slug,
            name=wines[slug].name,
            score=score,
            f1=_f1(score),
            image=f"api/image/{slug}",
        ))
        conf_by_slug[slug] = conf

    elapsed_ms = int((time.perf_counter() - started) * 1000)
    if not candidates:
        return SearchResult(None, False, 0.0, 0.0, 0.0, elapsed_ms, engine, [])

    top = candidates[0]
    confidence = conf_by_slug[top.slug]
    found = confidence >= settings.confidence_threshold
    return SearchResult(
        slug=top.slug if found else None,
        found=found,
        confidence=confidence,
        f1_top1=_f1(confidence),
        f1_top5=_f1(sum(c.score for c in candidates[:5]) / len(candidates[:5])),
        elapsed_ms=elapsed_ms,
        engine=engine,
        candidates=candidates,
        top_slug=top.slug,
    )
