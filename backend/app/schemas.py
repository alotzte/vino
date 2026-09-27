from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class Achievement(BaseModel):
    id: str
    title: str
    description: str
    icon: str
    threshold: int
    progress: int
    unlocked: bool
    unlocked_at: Optional[str] = None


class Wine(BaseModel):
    slug: str
    name: str
    url: Optional[str] = None
    manufacturer: Optional[str] = None
    region: Optional[str] = None
    grapes: List[str] = Field(default_factory=list)
    category: Optional[str] = None
    color: Optional[str] = None
    serving_temperature: Optional[str] = None
    abv: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    image: Optional[str] = None


class Candidate(BaseModel):
    slug: str
    name: str
    score: float
    f1: float
    image: Optional[str] = None


class ScanResponse(BaseModel):
    slug: Optional[str]
    found: bool
    confidence: float
    f1_top1: float
    f1_top5: float
    elapsed_ms: int
    engine: str
    wine: Optional[Wine] = None
    candidates: List[Candidate] = Field(default_factory=list)
    new_achievements: List[Achievement] = Field(default_factory=list)


class FlatScanResponse(BaseModel):
    slug: str


class SommelierRequest(BaseModel):
    slug: str
    answers: List[str] = Field(default_factory=list)


class SommelierResponse(BaseModel):
    slug: str
    verdict: str
    pairings: List[str] = Field(default_factory=list)
    alternatives: List[Candidate] = Field(default_factory=list)
    stub: bool = True


class HistoryItem(BaseModel):
    slug: Optional[str]
    found: bool
    confidence: float
    region: Optional[str] = None
    color: Optional[str] = None
    rating: Optional[int] = None
    created_at: str
    wine: Optional[Wine] = None


class HistoryResponse(BaseModel):
    items: List[HistoryItem] = Field(default_factory=list)


class RatingRequest(BaseModel):
    rating: int = Field(ge=1, le=5)


class RatingResponse(BaseModel):
    slug: str
    rating: Optional[int] = None


class AchievementsResponse(BaseModel):
    items: List[Achievement] = Field(default_factory=list)


class MeStats(BaseModel):
    total_scans: int
    found_scans: int
    distinct_regions: int
    rated_wines: int
    avg_rating: Optional[float] = None


class MeResponse(BaseModel):
    created_at: str
    stats: MeStats


class Winery(BaseModel):
    manufacturer: str
    region: Optional[str] = None
    wine_count: int
    lat: Optional[float] = None
    lon: Optional[float] = None
    visited: bool = False
    checked_in: bool = False


class WineriesResponse(BaseModel):
    items: List[Winery] = Field(default_factory=list)


class WineBrowseResponse(BaseModel):
    items: List[Wine] = Field(default_factory=list)
    total: int
    limit: int
    offset: int


class LessonCard(BaseModel):
    id: str
    title: str
    body: str
    icon: str


class LeagueMember(BaseModel):
    name: str
    xp: int
    is_user: bool
    rank: int


class LeagueResponse(BaseModel):
    week: str
    members: List[LeagueMember] = Field(default_factory=list)


class LearningStatus(BaseModel):
    lesson: LessonCard
    completed_today: bool
    streak: int
    league: LeagueResponse


class MenuMatch(BaseModel):
    slug: str
    name: str
    manufacturer: Optional[str] = None
    match_confidence: float
    expert_score: int
    retail_price: int
    menu_price: int
    markup_percent: int
    image: Optional[str] = None


class MenuScanResponse(BaseModel):
    items: List[MenuMatch] = Field(default_factory=list)
    engine: str = "stub"


class CheckinRequest(BaseModel):
    manufacturer: str


class QuizQuestion(BaseModel):
    id: str
    text: str
    options: List[str]


class QuizToday(BaseModel):
    date: str
    questions: List[QuizQuestion] = Field(default_factory=list)
    completed_today: bool
    score: Optional[int] = None


class QuizSubmitRequest(BaseModel):
    answers: Dict[str, int] = Field(default_factory=dict)


class QuizCheckRequest(BaseModel):
    question_id: str
    selected_index: int


class QuizCheckResult(BaseModel):
    correct: bool
    correct_index: int


class QuizResult(BaseModel):
    score: int
    total: int
    correct_ids: List[str] = Field(default_factory=list)
    already_submitted: bool


class BonusTier(BaseModel):
    id: str
    title: str
    description: str
    icon: str
    threshold: int
    progress: int
    unlocked: bool


class PointsStatus(BaseModel):
    points: int
    reviews: int
    checkins: int
    bonuses: List[BonusTier] = Field(default_factory=list)


class RelatedQuestion(BaseModel):
    id: str
    question: str
    answer: str


class RelatedQuestionsResponse(BaseModel):
    items: List[RelatedQuestion] = Field(default_factory=list)


class WineScores(BaseModel):
    crowd: float
    expert: int
