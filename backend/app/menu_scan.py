"""Заглушка сканера винной карты: позиции выбираются по хэшу фото, цены и оценки - демо."""
import hashlib
import random
from typing import List

from . import catalog
from .schemas import MenuMatch

MATCH_COUNT = 5


def scan(raw: bytes) -> List[MenuMatch]:
    seed = int(hashlib.sha256(raw).hexdigest(), 16)
    rng = random.Random(seed)

    slugs = catalog.all_slugs()
    picked = rng.sample(slugs, min(MATCH_COUNT, len(slugs)))
    wines = catalog.get_many(picked)

    items = []
    for slug in picked:
        wine = wines.get(slug)
        if not wine:
            continue
        wine_rng = random.Random(int(hashlib.sha256(slug.encode("utf-8")).hexdigest(), 16))
        retail = wine_rng.randrange(600, 3500, 50)
        markup = wine_rng.randrange(40, 180, 10)
        items.append(MenuMatch(
            slug=slug,
            name=wine.name,
            manufacturer=wine.manufacturer,
            match_confidence=round(rng.uniform(0.55, 0.95), 2),
            expert_score=wine_rng.randrange(82, 98),
            retail_price=retail,
            menu_price=int(retail * (1 + markup / 100)),
            markup_percent=markup,
            image=wine.image,
        ))

    items.sort(key=lambda m: m.expert_score, reverse=True)
    return items
