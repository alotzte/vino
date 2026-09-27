import hashlib
import random
from typing import List, Optional

from . import catalog
from .api.sommelier import pairings as gastro_pairings
from .schemas import RelatedQuestion, Wine

QUESTION_COUNT = 4


def _grapes_answer(wine: Wine) -> Optional[RelatedQuestion]:
    if not wine.grapes:
        return None
    grapes = ", ".join(wine.grapes)
    kind = "моносортовое вино" if len(wine.grapes) == 1 else f"купаж из {len(wine.grapes)} сортов"
    return RelatedQuestion(
        id="grapes",
        question=f'Какой сорт винограда в "{wine.name}"?',
        answer=f"{wine.name} делают из {grapes} - это {kind}.",
    )


def _region_answer(wine: Wine) -> Optional[RelatedQuestion]:
    if not wine.region:
        return None
    subject = f'Винодельня "{wine.manufacturer}"' if wine.manufacturer else "Производитель"
    return RelatedQuestion(
        id="region",
        question=f'Из какого региона "{wine.name}"?',
        answer=f"{subject} находится в регионе {wine.region} - одном из винодельческих регионов России.",
    )


def _pairing_answer(wine: Wine) -> RelatedQuestion:
    pairs = gastro_pairings(wine.category)
    temp = wine.serving_temperature or "12–14°C"
    return RelatedQuestion(
        id="pairing",
        question=f'С чем подавать "{wine.name}"?',
        answer=f"Хорошо сочетается с: {', '.join(pairs)}. Подавать охлаждённым до {temp}.",
    )


def _abv_answer(wine: Wine) -> Optional[RelatedQuestion]:
    if not wine.abv and not wine.category:
        return None
    parts = []
    if wine.category:
        parts.append(f"категория - {wine.category.lower()}")
    if wine.abv:
        parts.append(f"крепость - {wine.abv}")
    return RelatedQuestion(
        id="abv",
        question=f'Какая крепость у "{wine.name}"?',
        answer="У этого вина " + ", ".join(parts) + ".",
    )


def _color_answer(wine: Wine) -> Optional[RelatedQuestion]:
    if not wine.color:
        return None
    return RelatedQuestion(
        id="color",
        question=f'Какого цвета "{wine.name}"?',
        answer=f'У "{wine.name}" цвет - {wine.color}.',
    )


def _storage_answer(wine: Wine) -> RelatedQuestion:
    sparkling = "игрист" in (wine.category or "").lower() or "шампан" in (wine.category or "").lower()
    answer = (
        "Игристое лучше хранить в вертикальном положении, в темноте, при 10–15°C - так пробка не рассыхается неравномерно."
        if sparkling
        else "Храните в тёмном прохладном месте при 10–15°C, бутылку с пробкой - лёжа, чтобы пробка не пересыхала."
    )
    return RelatedQuestion(id="storage", question=f'Как хранить "{wine.name}"?', answer=answer)


def _decanting_answer(wine: Wine) -> RelatedQuestion:
    is_red = "красн" in (wine.category or "").lower()
    answer = (
        f'"{wine.name}" - красное: декантация на 20–30 минут перед подачей раскроет аромат и смягчит танины.'
        if is_red
        else f'"{wine.name}" декантировать не обязательно - это больше нужно плотным выдержанным красным.'
    )
    return RelatedQuestion(id="decanting", question=f'Нужно ли декантировать "{wine.name}"?', answer=answer)


def _glass_answer(wine: Wine) -> RelatedQuestion:
    category = (wine.category or "").lower()
    if "игрист" in category or "шампан" in category:
        answer = "Узкий высокий бокал-флюте - так пузырьки дольше держатся, а аромат медленнее выветривается."
    elif "красн" in category:
        answer = "Бокал с широкой чашей - даёт вину раскрыться и насытиться кислородом."
    elif "бел" in category:
        answer = "Бокал поуже и чуть меньше, чем для красного - так вино медленнее нагревается от руки."
    else:
        answer = "Универсальный бокал на тонкой ножке - держите его за ножку, чтобы не греть вино рукой."
    return RelatedQuestion(id="glass", question=f'В каком бокале подавать "{wine.name}"?', answer=answer)


def _price_answer(wine: Wine) -> RelatedQuestion:
    return RelatedQuestion(
        id="price",
        question=f'Сколько стоит "{wine.name}"?',
        answer="Точной цены в каталоге нет - она отличается от магазина к магазину. "
        'Ориентир смотрите в блоке "Найти в магазинах" на этой карточке.',
    )


def for_wine(slug: str) -> List[RelatedQuestion]:
    wine = catalog.get(slug)
    if not wine:
        return []

    candidates = [
        q
        for q in (
            _grapes_answer(wine),
            _region_answer(wine),
            _pairing_answer(wine),
            _abv_answer(wine),
            _color_answer(wine),
            _storage_answer(wine),
            _decanting_answer(wine),
            _glass_answer(wine),
            _price_answer(wine),
        )
        if q is not None
    ]
    rng = random.Random(int(hashlib.sha256(slug.encode("utf-8")).hexdigest(), 16))
    rng.shuffle(candidates)
    return candidates[:QUESTION_COUNT]
