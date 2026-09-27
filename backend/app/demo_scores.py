"""Демо-оценки вина (народная и экспертов) - псевдослучайные, но постоянные: считаются от slug."""
import hashlib
from typing import Tuple

CROWD_MIN, CROWD_MAX = 1.0, 5.0
EXPERT_MIN, EXPERT_MAX = 60, 91


def for_slug(slug: str) -> Tuple[float, int]:
    digest = hashlib.sha256(slug.encode("utf-8")).digest()
    crowd = CROWD_MIN + int.from_bytes(digest[:2], "big") / 65535 * (CROWD_MAX - CROWD_MIN)
    expert = EXPERT_MIN + int.from_bytes(digest[2:4], "big") % (EXPERT_MAX - EXPERT_MIN + 1)
    return round(crowd, 1), expert
