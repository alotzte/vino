import json
import sqlite3
import threading
from typing import Dict, List, Optional

from .config import settings
from .schemas import Wine

_local = threading.local()


def _conn() -> sqlite3.Connection:
    conn = getattr(_local, "conn", None)
    if conn is None:
        # WAL-база на read-only томе без -wal/-shm открывается только с immutable=1
        conn = sqlite3.connect(
            f"file:{settings.db_path}?mode=ro&immutable=1", uri=True, check_same_thread=False
        )
        conn.row_factory = sqlite3.Row
        _local.conn = conn
    return conn


def _row_to_wine(row: sqlite3.Row) -> Wine:
    try:
        grapes = json.loads(row["grapes"]) if row["grapes"] else []
    except (json.JSONDecodeError, TypeError):
        grapes = [g.strip() for g in (row["grapes"] or "").split(",") if g.strip()]

    return Wine(
        slug=row["slug"],
        name=row["name"],
        url=row["url"],
        manufacturer=row["manufacturer"],
        region=row["region"],
        grapes=grapes,
        category=row["category"],
        color=row["color"],
        serving_temperature=row["serving_temperature"],
        abv=row["abv"],
        description=row["description"],
        image_url=row["image_url"],
        image=f"api/image/{row['slug']}",
    )


def count() -> int:
    return _conn().execute("SELECT COUNT(*) FROM wines").fetchone()[0]


def get(slug: str) -> Optional[Wine]:
    row = _conn().execute("SELECT * FROM wines WHERE slug = ?", (slug,)).fetchone()
    return _row_to_wine(row) if row else None


def get_many(slugs: List[str]) -> Dict[str, Wine]:
    if not slugs:
        return {}
    marks = ",".join("?" * len(slugs))
    rows = _conn().execute(f"SELECT * FROM wines WHERE slug IN ({marks})", slugs)
    return {r["slug"]: _row_to_wine(r) for r in rows}


def all_slugs() -> List[str]:
    return [r[0] for r in _conn().execute("SELECT slug FROM wines ORDER BY slug")]


def search(query: str, limit: int = 20) -> List[Wine]:
    like = f"%{query.strip()}%"
    rows = _conn().execute(
        "SELECT * FROM wines WHERE name LIKE ? OR manufacturer LIKE ? LIMIT ?",
        (like, like, limit),
    )
    return [_row_to_wine(r) for r in rows]


def browse(
    region: Optional[str] = None,
    color: Optional[str] = None,
    manufacturer: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
):
    where = []
    params: list = []
    if region:
        where.append("region = ?")
        params.append(region)
    if color:
        where.append("color = ?")
        params.append(color)
    if manufacturer:
        where.append("manufacturer = ?")
        params.append(manufacturer)
    clause = f"WHERE {' AND '.join(where)}" if where else ""

    total = _conn().execute(f"SELECT COUNT(*) FROM wines {clause}", params).fetchone()[0]
    rows = _conn().execute(
        f"SELECT * FROM wines {clause} ORDER BY manufacturer, name LIMIT ? OFFSET ?",
        (*params, limit, offset),
    )
    return [_row_to_wine(r) for r in rows], total


def wineries() -> List[Dict]:
    rows = _conn().execute(
        """SELECT manufacturer, region, COUNT(*) AS wine_count
           FROM wines WHERE manufacturer IS NOT NULL
           GROUP BY manufacturer, region ORDER BY manufacturer"""
    )
    return [{"manufacturer": r["manufacturer"], "region": r["region"], "wine_count": r["wine_count"]} for r in rows]


def image_path(slug: str):
    for ext in (".webp", ".jpg", ".jpeg", ".png"):
        p = settings.images_dir / f"{slug}{ext}"
        if p.exists():
            return p
    return None
