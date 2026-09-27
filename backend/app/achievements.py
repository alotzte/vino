from dataclasses import dataclass
from typing import Dict, List, Tuple

from sqlalchemy import func, select

from . import appdb
from .appdb import Rating, Scan, SessionLocal, UserAchievement


@dataclass
class Definition:
    id: str
    title: str
    description: str
    icon: str
    threshold: int
    metric: str


DEFINITIONS: List[Definition] = [
    Definition("regions_3", "Путешественник", "Найдите вина из 3 разных регионов", "🗺️", 3, "regions"),
    Definition("regions_5", "Исследователь регионов", "Найдите вина из 5 разных регионов", "🧭", 5, "regions"),
    Definition("colors_3", "Вся палитра", "Найдите красное, белое и розовое вино", "🎨", 3, "colors"),
    Definition("grapes_5", "Знаток сортов", "Найдите вина из 5 разных сортов винограда", "🍇", 5, "grapes"),
    Definition("ratings_5", "Критик", "Оцените 5 вин", "⭐", 5, "ratings"),
    Definition("ratings_5star_3", "Ценитель", "Поставьте оценку 5 трём винам", "🌟", 3, "five_star"),
    Definition("checkins_1", "Первый визит", "Отметьтесь на винодельне на карте", "📍", 1, "checkins"),
    Definition("checkins_3", "Завсегдатай", "Отметьтесь на 3 разных винодельнях", "🚩", 3, "checkins"),
    Definition("lesson_streak_3", "Прилежный ученик", "Проходите уроки винной грамотности 3 дня подряд", "🔥", 3, "lesson_streak"),
    Definition("lesson_streak_7", "Неделя знаний", "Проходите уроки винной грамотности 7 дней подряд", "📚", 7, "lesson_streak"),
]


def _metrics(session, user_id: int) -> Dict[str, int]:
    regions = session.scalar(
        select(func.count(func.distinct(Scan.region))).where(
            Scan.user_id == user_id, Scan.found.is_(True), Scan.region.is_not(None)
        )
    ) or 0
    colors = session.scalar(
        select(func.count(func.distinct(Scan.color))).where(
            Scan.user_id == user_id, Scan.found.is_(True), Scan.color.is_not(None)
        )
    ) or 0
    ratings = session.scalar(select(func.count()).select_from(Rating).where(Rating.user_id == user_id)) or 0
    five_star = session.scalar(
        select(func.count()).select_from(Rating).where(Rating.user_id == user_id, Rating.rating == 5)
    ) or 0
    grape_lists = session.scalars(
        select(Scan.grapes).where(Scan.user_id == user_id, Scan.found.is_(True), Scan.grapes.is_not(None))
    ).all()
    grapes = len({g for lst in grape_lists for g in (lst or [])})
    return {
        "regions": regions,
        "colors": colors,
        "grapes": grapes,
        "ratings": ratings,
        "five_star": five_star,
        "checkins": appdb.checkin_count(user_id),
        "lesson_streak": appdb.learning_streak(user_id),
    }


def evaluate(user_id: int) -> Tuple[List[dict], List[dict]]:
    with SessionLocal() as session:
        metrics = _metrics(session, user_id)
        already = set(session.scalars(select(UserAchievement.achievement_id).where(UserAchievement.user_id == user_id)))

        newly_unlocked_ids = []
        items = []
        for d in DEFINITIONS:
            progress = metrics[d.metric]
            is_unlocked = progress >= d.threshold
            if is_unlocked and d.id not in already:
                newly_unlocked_ids.append(d.id)
            items.append({
                "id": d.id,
                "title": d.title,
                "description": d.description,
                "icon": d.icon,
                "threshold": d.threshold,
                "progress": min(progress, d.threshold),
                "unlocked": is_unlocked,
                "unlocked_at": None,
            })

        if newly_unlocked_ids:
            session.add_all([UserAchievement(user_id=user_id, achievement_id=a) for a in newly_unlocked_ids])
            session.commit()

        unlocked_at = dict(session.execute(
            select(UserAchievement.achievement_id, UserAchievement.unlocked_at).where(UserAchievement.user_id == user_id)
        ).all())
        for item in items:
            ts = unlocked_at.get(item["id"])
            item["unlocked_at"] = ts.isoformat() if ts else None

        new_achievements = [i for i in items if i["id"] in newly_unlocked_ids]
        return new_achievements, items
