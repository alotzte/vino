import hashlib
from typing import Optional, Tuple

REGION_COORDS: dict[str, Tuple[float, float]] = {
    "Кубань": (45.0, 37.4),
    "Крым": (44.9521, 34.1024),
    "Дагестан": (42.0678, 48.2899),
    "Долина Дона": (47.6461, 42.0972),
    "Ставрополье": (45.0428, 41.9734),
    "Нижняя Волга": (48.7080, 44.5133),
    "Самара": (53.2001, 50.1500),
    "Северная Осетия — Алания": (43.0241, 44.6820),
    "Дальневосточная зона": (43.1198, 131.8869),
}

JITTER_DEGREES = 0.18


def winery_coords(manufacturer: str, region: Optional[str]) -> Optional[Tuple[float, float]]:
    base = REGION_COORDS.get(region or "")
    if base is None:
        return None
    digest = hashlib.sha256(manufacturer.encode("utf-8")).digest()
    dx = (digest[0] / 255 - 0.5) * 2 * JITTER_DEGREES
    dy = (digest[1] / 255 - 0.5) * 2 * JITTER_DEGREES
    return round(base[0] + dx, 5), round(base[1] + dy, 5)
