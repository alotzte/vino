from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse

from .. import achievements, appdb, catalog, demo_scores, lessons, menu_scan, points, quiz, regions, related_questions, scan_log
from ..auth import optional_user_id, require_user_id
from ..config import settings
from ..pipeline import search_by_image
from ..pipeline.remote import CvUnavailable
from ..pipeline import remote
from ..schemas import (
    AchievementsResponse,
    CheckinRequest,
    HistoryItem,
    HistoryResponse,
    LearningStatus,
    MenuScanResponse,
    MeResponse,
    MeStats,
    PointsStatus,
    QuizCheckRequest,
    QuizCheckResult,
    QuizQuestion,
    QuizResult,
    QuizSubmitRequest,
    QuizToday,
    RatingRequest,
    RatingResponse,
    RelatedQuestionsResponse,
    WineScores,
    ScanResponse,
    SommelierRequest,
    SommelierResponse,
    WineBrowseResponse,
    Winery,
    WineriesResponse,
    Wine,
)
from . import sommelier

router = APIRouter(prefix="/api")

MAX_UPLOAD_BYTES = 15 * 1024 * 1024


@router.get("/health")
def health():
    body = {
        "status": "ok",
        "engine": settings.engine,
        "catalog_size": catalog.count(),
        "stub": settings.engine == "stub",
        "max_bot_name": settings.max_bot_name or None,
    }
    if settings.engine == "remote":
        cv = remote.health()
        body["cv"] = {k: cv.get(k) for k in ("status", "load_s", "gpu_mem_mb", "index", "error") if k in cv}
        if cv.get("status") != "ok":
            body["stub"] = True
            body["status"] = "degraded"
        body["cv_fallbacks"] = remote.fallbacks
    return body


# Не async: блокирующее распознавание FastAPI уведёт в threadpool, а не в event loop
@router.post("/scan", response_model=None)
def scan(
    request: Request,
    image: UploadFile | None = File(None, description="Поле скрипта оценки кейсодержателя"),
    file: UploadFile | None = File(None, description="Псевдоним поля image (наш фронтенд)"),
    flat: bool = Query(False, description="Плоский ответ {\"slug\": \"...\"} для скрипта оценки"),
    user_id: Optional[int] = Depends(optional_user_id),
):
    # participant_test.sh шлёт `image`, фронтенд - `file`; 422 на приёмке обнуляет прогон
    upload = image or file
    if upload is None:
        raise HTTPException(status_code=400, detail="Нужен файл в поле image")

    raw = upload.file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Пустой файл")
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Файл больше 15 МБ")

    status, result = 200, None
    try:
        result = search_by_image(raw)
    except OSError:
        status = 415
        raise HTTPException(status_code=415, detail="Не удалось прочитать изображение")
    except CvUnavailable as exc:
        status = 503
        raise HTTPException(status_code=503, detail=f"Распознавание недоступно: {exc}")
    finally:
        scan_log.record(
            raw,
            endpoint="scan",
            status=status,
            filename=upload.filename,
            flat=flat,
            user_id=user_id,
            user_agent=request.headers.get("user-agent"),
            result=result,
        )

    wine = catalog.get(result.slug) if result.slug else None

    new_achievements = []
    if user_id is not None:
        appdb.record_scan(
            user_id,
            result.slug,
            result.found,
            result.confidence,
            wine.region if wine else None,
            wine.color if wine else None,
            wine.grapes if wine else [],
        )
        new_achievements, _ = achievements.evaluate(user_id)

    if flat:
        # Без порога отказа: все вина приватного набора есть в каталоге, пустой slug - всегда промах
        return JSONResponse({"slug": result.top_slug or ""})

    return ScanResponse(
        slug=result.slug,
        found=result.found,
        confidence=result.confidence,
        f1_top1=result.f1_top1,
        f1_top5=result.f1_top5,
        elapsed_ms=result.elapsed_ms,
        engine=result.engine,
        wine=wine,
        candidates=result.candidates,
        new_achievements=new_achievements,
    )


@router.get("/wines/{slug}", response_model=Wine)
def wine_card(slug: str):
    wine = catalog.get(slug)
    if not wine:
        raise HTTPException(status_code=404, detail="Вино не найдено")
    return wine


@router.get("/wines/{slug}/questions", response_model=RelatedQuestionsResponse)
def wine_questions(slug: str):
    return RelatedQuestionsResponse(items=related_questions.for_wine(slug))


@router.get("/wines/{slug}/scores", response_model=WineScores)
def wine_scores(slug: str):
    if not catalog.get(slug):
        raise HTTPException(status_code=404, detail="Вино не найдено")
    crowd, expert = demo_scores.for_slug(slug)
    return WineScores(crowd=crowd, expert=expert)


@router.get("/wines", response_model=WineBrowseResponse)
def wine_list(
    q: str = Query("", min_length=0),
    region: Optional[str] = Query(None),
    color: Optional[str] = Query(None),
    manufacturer: Optional[str] = Query(None),
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
):
    if q:
        items = catalog.search(q, limit)
        return WineBrowseResponse(items=items, total=len(items), limit=limit, offset=0)
    items, total = catalog.browse(region=region, color=color, manufacturer=manufacturer, limit=limit, offset=offset)
    return WineBrowseResponse(items=items, total=total, limit=limit, offset=offset)


@router.get("/wineries", response_model=WineriesResponse)
def winery_list(user_id: Optional[int] = Depends(optional_user_id)):
    visited_manufacturers: set = set()
    checked_in_manufacturers: set = set()
    if user_id is not None:
        rows = appdb.history(user_id, limit=1000)
        slugs = [r["slug"] for r in rows if r["found"] and r["slug"]]
        visited_manufacturers = {
            w.manufacturer for w in catalog.get_many(slugs).values() if w.manufacturer
        }
        checked_in_manufacturers = appdb.checked_in_manufacturers(user_id)

    items = []
    for w in catalog.wineries():
        coords = regions.winery_coords(w["manufacturer"], w["region"])
        items.append(
            Winery(
                manufacturer=w["manufacturer"],
                region=w["region"],
                wine_count=w["wine_count"],
                lat=coords[0] if coords else None,
                lon=coords[1] if coords else None,
                visited=w["manufacturer"] in visited_manufacturers,
                checked_in=w["manufacturer"] in checked_in_manufacturers,
            )
        )
    return WineriesResponse(items=items)


@router.post("/wineries/checkin")
def winery_checkin(payload: CheckinRequest, user_id: int = Depends(require_user_id)):
    winery = next((w for w in catalog.wineries() if w["manufacturer"] == payload.manufacturer), None)
    if not winery:
        raise HTTPException(status_code=404, detail="Винодельня не найдена")
    appdb.record_checkin(user_id, winery["manufacturer"], winery["region"])
    return {"ok": True}


@router.get("/wines/{slug}/rating", response_model=RatingResponse)
def get_rating(slug: str, user_id: int = Depends(require_user_id)):
    return RatingResponse(slug=slug, rating=appdb.get_rating(user_id, slug))


@router.post("/wines/{slug}/rating", response_model=RatingResponse)
def set_rating(slug: str, payload: RatingRequest, user_id: int = Depends(require_user_id)):
    if not catalog.get(slug):
        raise HTTPException(status_code=404, detail="Вино не найдено")
    appdb.upsert_rating(user_id, slug, payload.rating)
    return RatingResponse(slug=slug, rating=payload.rating)


@router.get("/history", response_model=HistoryResponse)
def scan_history(user_id: int = Depends(require_user_id), limit: int = Query(100, le=200)):
    rows = appdb.history(user_id, limit)
    slugs = [r["slug"] for r in rows if r["slug"]]
    wines = catalog.get_many(slugs)
    items = [
        HistoryItem(
            slug=r["slug"],
            found=bool(r["found"]),
            confidence=r["confidence"],
            region=r["region"],
            color=r["color"],
            rating=r["rating"],
            created_at=r["created_at"],
            wine=wines.get(r["slug"]) if r["slug"] else None,
        )
        for r in rows
    ]
    return HistoryResponse(items=items)


@router.get("/achievements", response_model=AchievementsResponse)
def list_achievements(user_id: int = Depends(require_user_id)):
    _, all_items = achievements.evaluate(user_id)
    return AchievementsResponse(items=all_items)


@router.get("/me", response_model=MeResponse)
def me(user_id: int = Depends(require_user_id)):
    user = appdb.get_user(user_id)
    return MeResponse(created_at=user["created_at"], stats=MeStats(**appdb.stats(user_id)))


@router.get("/image/{slug}")
def wine_image(slug: str):
    path = catalog.image_path(slug)
    if not path:
        raise HTTPException(status_code=404, detail="Изображение не найдено")
    return FileResponse(path, media_type="image/webp", headers={"Cache-Control": "public, max-age=86400"})


@router.get("/sommelier/questions")
def sommelier_questions():
    return {"questions": sommelier.QUESTIONS}


@router.post("/sommelier", response_model=SommelierResponse)
def sommelier_advice(payload: SommelierRequest):
    return sommelier.advise(payload.slug, payload.answers)


@router.get("/learning", response_model=LearningStatus)
def learning_status(user_id: int = Depends(require_user_id)):
    return lessons.status(user_id)


@router.post("/learning/complete", response_model=LearningStatus)
def learning_complete(user_id: int = Depends(require_user_id)):
    return lessons.complete_today(user_id)


@router.post("/menu-scan", response_model=MenuScanResponse)
def scan_menu(request: Request, image: UploadFile = File(...)):
    raw = image.file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Пустой файл")
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Файл больше 15 МБ")
    scan_log.record(
        raw,
        endpoint="menu-scan",
        status=200,
        filename=image.filename,
        user_agent=request.headers.get("user-agent"),
    )
    return MenuScanResponse(items=menu_scan.scan(raw), engine="stub")


@router.get("/quiz/today", response_model=QuizToday)
def quiz_today(user_id: int = Depends(require_user_id)):
    today_items = quiz.today_quiz()
    score = appdb.get_quiz_result_today(user_id)
    return QuizToday(
        date=date.today().isoformat(),
        questions=[QuizQuestion(id=q["id"], text=q["text"], options=q["options"]) for q in today_items],
        completed_today=score is not None,
        score=score,
    )


@router.post("/quiz/check", response_model=QuizCheckResult)
def quiz_check(payload: QuizCheckRequest, user_id: int = Depends(require_user_id)):
    result = quiz.check_answer(payload.question_id, payload.selected_index)
    if result is None:
        raise HTTPException(status_code=404, detail="Вопрос не найден в сегодняшнем тесте")
    return QuizCheckResult(**result)


@router.post("/quiz/submit", response_model=QuizResult)
def quiz_submit(payload: QuizSubmitRequest, user_id: int = Depends(require_user_id)):
    today_items = quiz.today_quiz()
    total = len(today_items)

    existing = appdb.get_quiz_result_today(user_id)
    if existing is not None:
        return QuizResult(score=existing, total=total, correct_ids=[], already_submitted=True)

    correct_ids = []
    score = 0
    for q in today_items:
        if payload.answers.get(q["id"]) == q["correct_index"]:
            score += 1
            correct_ids.append(q["id"])

    appdb.record_quiz_result(user_id, score)
    return QuizResult(score=score, total=total, correct_ids=correct_ids, already_submitted=False)


@router.get("/points", response_model=PointsStatus)
def points_status(user_id: int = Depends(require_user_id)):
    return points.status(user_id)
