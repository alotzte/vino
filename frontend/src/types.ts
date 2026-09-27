export interface Wine {
  slug: string;
  name: string;
  url?: string | null;
  manufacturer?: string | null;
  region?: string | null;
  grapes: string[];
  category?: string | null;
  color?: string | null;
  serving_temperature?: string | null;
  abv?: string | null;
  description?: string | null;
  image_url?: string | null;
  image?: string | null;
}

export interface Candidate {
  slug: string;
  name: string;
  score: number;
  f1: number;
  image?: string | null;
}

export interface Achievement {
  id: string;
  title: string;
  description: string;
  icon: string;
  threshold: number;
  progress: number;
  unlocked: boolean;
  unlocked_at?: string | null;
}

export interface ScanResponse {
  slug: string | null;
  found: boolean;
  confidence: number;
  f1_top1: number;
  f1_top5: number;
  elapsed_ms: number;
  engine: string;
  wine?: Wine | null;
  candidates: Candidate[];
  new_achievements: Achievement[];
}

export interface HistoryItem {
  slug: string | null;
  found: boolean;
  confidence: number;
  region?: string | null;
  color?: string | null;
  rating?: number | null;
  created_at: string;
  wine?: Wine | null;
}

export interface MeStats {
  total_scans: number;
  found_scans: number;
  distinct_regions: number;
  rated_wines: number;
  avg_rating?: number | null;
}

export interface MeResponse {
  created_at: string;
  stats: MeStats;
}

export interface SommelierQuestionOption {
  id: string;
  label: string;
}

export interface SommelierQuestion {
  id: string;
  title: string;
  options: SommelierQuestionOption[];
}

export interface SommelierResponse {
  slug: string;
  verdict: string;
  pairings: string[];
  alternatives: Candidate[];
  stub: boolean;
}

export interface Winery {
  manufacturer: string;
  region?: string | null;
  wine_count: number;
  lat?: number | null;
  lon?: number | null;
  visited: boolean;
  checked_in: boolean;
}

export interface WineBrowseResponse {
  items: Wine[];
  total: number;
  limit: number;
  offset: number;
}

export type Tab = "scan" | "catalog" | "map" | "profile";
export type ScanStage = "idle" | "loading" | "card" | "empty";

export interface LessonCard {
  id: string;
  title: string;
  body: string;
  icon: string;
}

export interface LeagueMember {
  name: string;
  xp: number;
  is_user: boolean;
  rank: number;
}

export interface LeagueResponse {
  week: string;
  members: LeagueMember[];
}

export interface LearningStatus {
  lesson: LessonCard;
  completed_today: boolean;
  streak: number;
  league: LeagueResponse;
}

export interface MenuMatch {
  slug: string;
  name: string;
  manufacturer?: string | null;
  match_confidence: number;
  expert_score: number;
  retail_price: number;
  menu_price: number;
  markup_percent: number;
  image?: string | null;
}

export interface MenuScanResponse {
  items: MenuMatch[];
  engine: string;
}

export interface QuizQuestion {
  id: string;
  text: string;
  options: string[];
}

export interface QuizToday {
  date: string;
  questions: QuizQuestion[];
  completed_today: boolean;
  score?: number | null;
}

export interface QuizResult {
  score: number;
  total: number;
  correct_ids: string[];
  already_submitted: boolean;
}

export interface QuizCheckResult {
  correct: boolean;
  correct_index: number;
}

export interface BonusTier {
  id: string;
  title: string;
  description: string;
  icon: string;
  threshold: number;
  progress: number;
  unlocked: boolean;
}

export interface PointsStatus {
  points: number;
  reviews: number;
  checkins: number;
  bonuses: BonusTier[];
}

export interface WineScores {
  crowd: number;
  expert: number;
}

export interface RelatedQuestion {
  id: string;
  question: string;
  answer: string;
}
