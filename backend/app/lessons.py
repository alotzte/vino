import hashlib
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import List, Optional

from . import appdb, catalog, quiz

XP_PER_LESSON = 10
BOT_NAMES = ["Соня", "Артём", "Марго", "Дима", "Лена", "Игорь", "Настя"]


@dataclass
class Lesson:
    id: str
    title: str
    body: str
    icon: str


STATIC_LESSONS: List[Lesson] = [
    Lesson("tannins", "Танины", 'Танины - вещества из кожицы, косточек и дубовой бочки. Они дают то самое "вяжущее" ощущение во рту и обычно сильнее выражены в молодых красных винах.', "🍇"),
    Lesson("terroir", "Терруар", "Терруар - сочетание почвы, климата и рельефа виноградника. Одинаковый сорт винограда в разных терруарах даёт вина с разным характером.", "🌍"),
    Lesson("serving-temp", "Температура подачи", "Красное вино подают теплее белого (16–18°C против 8–12°C) - так лучше раскрывается аромат, а танины не кажутся жёсткими.", "🌡️"),
    Lesson("decanting", "Декантация", "Переливание вина в графин перед подачей насыщает его кислородом и отделяет от осадка - особенно полезно для плотных выдержанных красных.", "🫗"),
    Lesson("cabernet", "Каберне Совиньон", "Один из самых распространённых красных сортов в мире: плотное тело, высокие танины, ноты чёрной смородины. В нашем каталоге он тоже часто встречается.", "🍷"),
    Lesson("saperavi", "Саперави", "Кавказский автохтонный сорт с окрашенной мякотью (тейнтюр) - отсюда густой цвет вина. Высокая кислотность позволяет ему хорошо стареть.", "🍇"),
    Lesson("muscat", "Мускат", "Группа ароматных сортов винограда - вино из муската легко узнать по выраженному цветочно-фруктовому аромату, часто используется для полусладких вин.", "🌸"),
    Lesson("oak-aging", "Выдержка в дубе", '"Выдержанное в дубе" вино получает ноты ванили, специй и дыма от бочки, а также становится мягче за счёт медленного контакта с воздухом.', "🛢️"),
    Lesson("crimea-history", "Виноделие Крыма", "Виноградарство в Крыму ведётся больше двух тысяч лет - ещё с античных греческих колоний. Сегодня это один из ключевых регионов российского виноделия.", "🏛️"),
    Lesson("kuban-scale", "Кубань - винная столица России", "Краснодарский край даёт больше российского вина, чем любой другой регион страны - благодаря мягкому климату и близости к Чёрному морю.", "🍾"),
    Lesson("dagestan", "Дагестан", "Один из старейших винодельческих регионов Кавказа: виноградарство здесь развивалось параллельно с кавказской и персидской традициями.", "⛰️"),
    Lesson("acidity", "Кислотность", 'Кислотность - то, что делает вино "свежим" и заставляет выделяться слюну. Она особенно высокая у белых вин из прохладного климата.', "🍋"),
]


def _data_driven_lessons() -> List[Lesson]:
    wineries = catalog.wineries()
    if not wineries:
        return []
    by_region: dict = {}
    for w in wineries:
        key = w["region"] or "-"
        by_region[key] = by_region.get(key, 0) + w["wine_count"]
    top_region, top_count = max(by_region.items(), key=lambda kv: kv[1])

    return [
        Lesson(
            "fact-top-region",
            "Регион-лидер каталога",
            f'Сейчас в каталоге "Своё Вино" больше всего позиций из региона "{top_region}" - {top_count} вин.',
            "📊",
        ),
        Lesson(
            "fact-wineries",
            "Сколько виноделен в каталоге",
            f"В каталоге представлено {len(wineries)} виноделен - от небольших крафтовых хозяйств до крупных производителей.",
            "🏭",
        ),
        Lesson(
            "fact-regions-count",
            "География каталога",
            f"Вина в каталоге представляют {len(by_region)} винодельческих регионов России - от Кубани и Крыма до Дальнего Востока.",
            "🗺️",
        ),
    ]


def all_lessons() -> List[Lesson]:
    return STATIC_LESSONS + _data_driven_lessons()


def lesson_of_the_day(today: Optional[date] = None) -> Lesson:
    lessons = all_lessons()
    today = today or date.today()
    return lessons[today.toordinal() % len(lessons)]


def _iso_week_key(today: date) -> str:
    year, week, _ = today.isocalendar()
    return f"{year}-W{week:02d}"


def _week_start(today: date) -> datetime:
    monday = today - timedelta(days=today.weekday())
    return datetime.combine(monday, datetime.min.time())


def _bot_xp(name: str, week_key: str) -> int:
    digest = hashlib.sha256(f"{name}:{week_key}".encode("utf-8")).digest()
    return 20 + (digest[0] % 180)


def league(user_id: int, today: Optional[date] = None) -> dict:
    today = today or date.today()
    week_key = _iso_week_key(today)
    week_start = _week_start(today)
    lesson_xp = appdb.lessons_completed_since(user_id, week_start) * XP_PER_LESSON
    quiz_xp = appdb.quiz_score_since(user_id, week_start) * quiz.XP_PER_CORRECT
    user_xp = lesson_xp + quiz_xp

    members = [{"name": name, "xp": _bot_xp(name, week_key), "is_user": False} for name in BOT_NAMES]
    members.append({"name": "Вы", "xp": user_xp, "is_user": True})
    members.sort(key=lambda m: m["xp"], reverse=True)
    for i, m in enumerate(members, start=1):
        m["rank"] = i

    return {"week": week_key, "members": members}


def status(user_id: int) -> dict:
    lesson = lesson_of_the_day()
    return {
        "lesson": {"id": lesson.id, "title": lesson.title, "body": lesson.body, "icon": lesson.icon},
        "completed_today": appdb.lesson_completed_today(user_id, lesson.id),
        "streak": appdb.learning_streak(user_id),
        "league": league(user_id),
    }


def complete_today(user_id: int) -> dict:
    lesson = lesson_of_the_day()
    appdb.complete_lesson(user_id, lesson.id)
    return status(user_id)
