from datetime import date, datetime, timedelta
from typing import List, Optional

from sqlalchemy import ForeignKey, JSON, create_engine, event, func, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from .config import settings

settings.app_db_path.parent.mkdir(parents=True, exist_ok=True)
engine = create_engine(f"sqlite:///{settings.app_db_path}", connect_args={"check_same_thread": False})


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, _):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    device_id: Mapped[str] = mapped_column(unique=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class Scan(Base):
    __tablename__ = "scans"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    slug: Mapped[Optional[str]]
    found: Mapped[bool]
    confidence: Mapped[float]
    region: Mapped[Optional[str]]
    color: Mapped[Optional[str]]
    grapes: Mapped[Optional[list]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class Rating(Base):
    __tablename__ = "ratings"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    slug: Mapped[str] = mapped_column(primary_key=True)
    rating: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)


class UserAchievement(Base):
    __tablename__ = "user_achievements"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    achievement_id: Mapped[str] = mapped_column(primary_key=True)
    unlocked_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class LessonCompletion(Base):
    __tablename__ = "lesson_completions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    lesson_id: Mapped[str]
    completed_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class QuizCompletion(Base):
    __tablename__ = "quiz_completions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    quiz_date: Mapped[str]
    score: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class WineryCheckin(Base):
    __tablename__ = "winery_checkins"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    manufacturer: Mapped[str]
    region: Mapped[Optional[str]]
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


def init_db() -> None:
    Base.metadata.create_all(engine)


def get_or_create_user(device_id: str) -> int:
    with SessionLocal() as session:
        user = session.scalar(select(User).where(User.device_id == device_id))
        if user:
            return user.id
        user = User(device_id=device_id)
        session.add(user)
        session.commit()
        return user.id


def get_user(user_id: int) -> Optional[dict]:
    with SessionLocal() as session:
        user = session.get(User, user_id)
        return {"id": user.id, "device_id": user.device_id, "created_at": user.created_at.isoformat()} if user else None


def record_scan(
    user_id: int,
    slug: Optional[str],
    found: bool,
    confidence: float,
    region: Optional[str],
    color: Optional[str],
    grapes: List[str],
) -> None:
    with SessionLocal() as session:
        session.add(Scan(
            user_id=user_id, slug=slug, found=found, confidence=confidence,
            region=region, color=color, grapes=grapes,
        ))
        session.commit()


def history(user_id: int, limit: int = 100) -> List[dict]:
    with SessionLocal() as session:
        rows = session.execute(
            select(Scan, Rating.rating)
            .outerjoin(Rating, (Rating.user_id == Scan.user_id) & (Rating.slug == Scan.slug))
            .where(Scan.user_id == user_id)
            .order_by(Scan.created_at.desc())
            .limit(limit)
        ).all()
        return [
            {
                "slug": s.slug,
                "found": s.found,
                "confidence": s.confidence,
                "region": s.region,
                "color": s.color,
                "rating": rating,
                "created_at": s.created_at.isoformat(),
            }
            for s, rating in rows
        ]


def stats(user_id: int) -> dict:
    with SessionLocal() as session:
        total_scans = session.scalar(select(func.count()).select_from(Scan).where(Scan.user_id == user_id)) or 0
        found_scans = session.scalar(
            select(func.count()).select_from(Scan).where(Scan.user_id == user_id, Scan.found.is_(True))
        ) or 0
        distinct_regions = session.scalar(
            select(func.count(func.distinct(Scan.region)))
            .where(Scan.user_id == user_id, Scan.found.is_(True), Scan.region.is_not(None))
        ) or 0
        rated_wines = session.scalar(select(func.count()).select_from(Rating).where(Rating.user_id == user_id)) or 0
        avg_rating = session.scalar(select(func.avg(Rating.rating)).where(Rating.user_id == user_id))
        return {
            "total_scans": total_scans,
            "found_scans": found_scans,
            "distinct_regions": distinct_regions,
            "rated_wines": rated_wines,
            "avg_rating": round(avg_rating, 2) if avg_rating else None,
        }


def upsert_rating(user_id: int, slug: str, rating: int) -> None:
    with SessionLocal() as session:
        existing = session.get(Rating, {"user_id": user_id, "slug": slug})
        if existing:
            existing.rating = rating
            existing.updated_at = datetime.utcnow()
        else:
            session.add(Rating(user_id=user_id, slug=slug, rating=rating))
        session.commit()


def get_rating(user_id: int, slug: str) -> Optional[int]:
    with SessionLocal() as session:
        rating = session.get(Rating, {"user_id": user_id, "slug": slug})
        return rating.rating if rating else None


def lesson_completed_today(user_id: int, lesson_id: str) -> bool:
    with SessionLocal() as session:
        row = session.scalar(
            select(LessonCompletion).where(
                LessonCompletion.user_id == user_id,
                LessonCompletion.lesson_id == lesson_id,
                func.date(LessonCompletion.completed_at) == date.today().isoformat(),
            )
        )
        return row is not None


def complete_lesson(user_id: int, lesson_id: str) -> None:
    if lesson_completed_today(user_id, lesson_id):
        return
    with SessionLocal() as session:
        session.add(LessonCompletion(user_id=user_id, lesson_id=lesson_id))
        session.commit()


def lesson_dates(user_id: int) -> List[date]:
    with SessionLocal() as session:
        rows = session.scalars(
            select(func.date(LessonCompletion.completed_at))
            .where(LessonCompletion.user_id == user_id)
            .distinct()
        ).all()
        return [date.fromisoformat(r) for r in rows]


def learning_streak(user_id: int) -> int:
    dates = set(lesson_dates(user_id))
    if not dates:
        return 0
    today = date.today()
    anchor = today if today in dates else today - timedelta(days=1)
    if anchor not in dates:
        return 0
    streak = 0
    d = anchor
    while d in dates:
        streak += 1
        d -= timedelta(days=1)
    return streak


def lessons_completed_since(user_id: int, since: datetime) -> int:
    with SessionLocal() as session:
        return session.scalar(
            select(func.count()).select_from(LessonCompletion).where(
                LessonCompletion.user_id == user_id, LessonCompletion.completed_at >= since
            )
        ) or 0


def record_checkin(user_id: int, manufacturer: str, region: Optional[str]) -> None:
    with SessionLocal() as session:
        session.add(WineryCheckin(user_id=user_id, manufacturer=manufacturer, region=region))
        session.commit()


def checked_in_manufacturers(user_id: int) -> set:
    with SessionLocal() as session:
        rows = session.scalars(
            select(WineryCheckin.manufacturer).where(WineryCheckin.user_id == user_id).distinct()
        ).all()
        return set(rows)


def checkin_count(user_id: int) -> int:
    with SessionLocal() as session:
        return session.scalar(
            select(func.count(func.distinct(WineryCheckin.manufacturer))).where(WineryCheckin.user_id == user_id)
        ) or 0


def get_quiz_result_today(user_id: int) -> Optional[int]:
    with SessionLocal() as session:
        row = session.scalar(
            select(QuizCompletion).where(
                QuizCompletion.user_id == user_id, QuizCompletion.quiz_date == date.today().isoformat()
            )
        )
        return row.score if row else None


def record_quiz_result(user_id: int, score: int) -> None:
    with SessionLocal() as session:
        session.add(QuizCompletion(user_id=user_id, quiz_date=date.today().isoformat(), score=score))
        session.commit()


def quiz_score_since(user_id: int, since: datetime) -> int:
    with SessionLocal() as session:
        return session.scalar(
            select(func.sum(QuizCompletion.score)).where(
                QuizCompletion.user_id == user_id, QuizCompletion.created_at >= since
            )
        ) or 0
