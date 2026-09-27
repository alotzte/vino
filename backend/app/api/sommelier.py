from typing import List

from .. import catalog
from ..schemas import Candidate, SommelierResponse

QUESTIONS = [
    {
        "id": "occasion",
        "title": "Повод",
        "options": [
            {"id": "dinner", "label": "Ужин дома"},
            {"id": "gift", "label": "В подарок"},
            {"id": "party", "label": "Компания друзей"},
        ],
    },
    {
        "id": "dish",
        "title": "К чему подаёте",
        "options": [
            {"id": "meat", "label": "Мясо"},
            {"id": "fish", "label": "Рыба и морепродукты"},
            {"id": "cheese", "label": "Сыр"},
            {"id": "solo", "label": "Без еды"},
        ],
    },
]

_PAIRINGS = {
    "Красное": ["Стейк рибай", "Баранина на углях", "Выдержанные твёрдые сыры"],
    "Белое": ["Дорадо на гриле", "Козий сыр", "Паста с морепродуктами"],
    "Розовое": ["Салат с креветками", "Брускетта с томатами", "Лёгкие закуски"],
    "Оранжевое": ["Плов", "Пряные овощи", "Азиатская кухня"],
}


def pairings(category: str | None) -> List[str]:
    for key, items in _PAIRINGS.items():
        if category and category.startswith(key):
            return items
    return ["Сырная тарелка", "Лёгкие закуски"]


def alternatives(slug: str, limit: int = 3) -> List[Candidate]:
    wine = catalog.get(slug)
    if not wine:
        return []

    rows = catalog._conn().execute(
        """
        SELECT slug, name FROM wines
        WHERE category = ? AND manufacturer IS NOT ? AND slug != ?
        LIMIT ?
        """,
        (wine.category, wine.manufacturer, slug, limit),
    ).fetchall()

    return [
        Candidate(slug=r["slug"], name=r["name"], score=0.0, f1=0.0, image=f"api/image/{r['slug']}")
        for r in rows
    ]


def advise(slug: str, answers: List[str]) -> SommelierResponse:
    wine = catalog.get(slug)
    if not wine:
        return SommelierResponse(slug=slug, verdict="Вино не найдено в каталоге.")

    occasion = "ужина" if "dinner" in answers else "встречи с друзьями" if "party" in answers else "повода"
    verdict = (
        f"{wine.name} - {(wine.category or 'вино').lower()} из региона "
        f"{wine.region or '-'}. Для {occasion} подойдёт: подавайте при "
        f"{wine.serving_temperature or '12-14°C'}."
    )

    return SommelierResponse(
        slug=slug,
        verdict=verdict,
        pairings=pairings(wine.category),
        alternatives=alternatives(slug),
        stub=True,
    )
