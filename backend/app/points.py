from dataclasses import dataclass
from typing import List

from . import appdb

POINTS_PER_REVIEW = 15
POINTS_PER_CHECKIN = 25


@dataclass
class Bonus:
    id: str
    title: str
    description: str
    threshold: int
    icon: str


BONUSES: List[Bonus] = [
    Bonus("bonus_50", "Скидка 5% на дегустацию", 'У винодельни-партнёра "Своё Вино" - по экрану с баллами', 50, "🎫"),
    Bonus("bonus_150", "Бесплатная дегустация 3 вин", "На винодельне-партнёре при визите", 150, "🍷"),
    Bonus("bonus_300", "Экскурсия по винодельне со скидкой 50%", "На выбранной винодельне-партнёре", 300, "🚗"),
    Bonus("bonus_500", 'Статус "Друг Своего Вина"', "Именной статус в каталоге и приоритетная поддержка", 500, "🏅"),
]


def total_points(user_id: int) -> int:
    reviews = appdb.stats(user_id)["rated_wines"]
    checkins = appdb.checkin_count(user_id)
    return reviews * POINTS_PER_REVIEW + checkins * POINTS_PER_CHECKIN


def status(user_id: int) -> dict:
    reviews = appdb.stats(user_id)["rated_wines"]
    checkins = appdb.checkin_count(user_id)
    points = reviews * POINTS_PER_REVIEW + checkins * POINTS_PER_CHECKIN

    bonuses = [
        {
            "id": b.id,
            "title": b.title,
            "description": b.description,
            "icon": b.icon,
            "threshold": b.threshold,
            "progress": min(points, b.threshold),
            "unlocked": points >= b.threshold,
        }
        for b in BONUSES
    ]
    return {"points": points, "reviews": reviews, "checkins": checkins, "bonuses": bonuses}
