import type {
  Achievement,
  HistoryItem,
  LearningStatus,
  MeResponse,
  MenuScanResponse,
  PointsStatus,
  QuizCheckResult,
  QuizResult,
  QuizToday,
  RelatedQuestion,
  WineScores,
  ScanResponse,
  SommelierQuestion,
  SommelierResponse,
  WineBrowseResponse,
  Winery,
  Wine,
} from "./types";
import { maxInitData } from "./max";

export const BASE = (() => {
  const p = location.pathname.replace(/index\.html$/, "");
  return p.endsWith("/") ? p : p + "/";
})();

export const assetUrl = (path: string) => BASE + path.replace(/^\//, "");

const DEVICE_ID = (() => {
  try {
    let id = localStorage.getItem("vino_device_id");
    if (!id) {
      id = crypto.randomUUID();
      localStorage.setItem("vino_device_id", id);
    }
    return id;
  } catch {
    return crypto.randomUUID();
  }
})();

async function apiFetch<T>(path: string, opts: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = { "X-Device-Id": DEVICE_ID, ...((opts.headers as Record<string, string>) || {}) };
  if (maxInitData) headers["X-Max-Init-Data"] = encodeURIComponent(maxInitData);
  const res = await fetch(BASE + "api/" + path.replace(/^\//, ""), { ...opts, headers });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export const getHealth = () => apiFetch<{ catalog_size: number; engine: string; stub: boolean; max_bot_name: string | null }>("health");

export function scanImage(file: File): Promise<ScanResponse> {
  const body = new FormData();
  body.append("file", file);
  return apiFetch<ScanResponse>("scan", { method: "POST", body });
}

export const getWine = (slug: string) => apiFetch<Wine>("wines/" + slug);

export const getRating = (slug: string) => apiFetch<{ slug: string; rating: number | null }>("wines/" + slug + "/rating");

export const setRating = (slug: string, rating: number) =>
  apiFetch<{ slug: string; rating: number | null }>("wines/" + slug + "/rating", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ rating }),
  });

export const getHistory = () => apiFetch<{ items: HistoryItem[] }>("history");

export const getAchievements = () => apiFetch<{ items: Achievement[] }>("achievements");

export const getMe = () => apiFetch<MeResponse>("me");

export const getSommelierQuestions = () => apiFetch<{ questions: SommelierQuestion[] }>("sommelier/questions");

export const askSommelier = (slug: string, answers: string[]) =>
  apiFetch<SommelierResponse>("sommelier", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ slug, answers }),
  });

export const getWineries = () => apiFetch<{ items: Winery[] }>("wineries");

export function browseWines(params: { region?: string; manufacturer?: string; limit?: number; offset?: number }) {
  const q = new URLSearchParams();
  if (params.region) q.set("region", params.region);
  if (params.manufacturer) q.set("manufacturer", params.manufacturer);
  q.set("limit", String(params.limit ?? 20));
  q.set("offset", String(params.offset ?? 0));
  return apiFetch<WineBrowseResponse>("wines?" + q.toString());
}

export const getLearningStatus = () => apiFetch<LearningStatus>("learning");

export const completeLesson = () => apiFetch<LearningStatus>("learning/complete", { method: "POST" });

export function scanMenu(file: File): Promise<MenuScanResponse> {
  const body = new FormData();
  body.append("image", file);
  return apiFetch<MenuScanResponse>("menu-scan", { method: "POST", body });
}

export const checkinWinery = (manufacturer: string) =>
  apiFetch<{ ok: boolean }>("wineries/checkin", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ manufacturer }),
  });

export const getQuizToday = () => apiFetch<QuizToday>("quiz/today");

export const checkQuizAnswer = (questionId: string, selectedIndex: number) =>
  apiFetch<QuizCheckResult>("quiz/check", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question_id: questionId, selected_index: selectedIndex }),
  });

export const submitQuiz = (answers: Record<string, number>) =>
  apiFetch<QuizResult>("quiz/submit", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ answers }),
  });

export const getPoints = () => apiFetch<PointsStatus>("points");

export const getWineScores = (slug: string) => apiFetch<WineScores>("wines/" + slug + "/scores");

export const getRelatedQuestions =(slug: string) => apiFetch<{ items: RelatedQuestion[] }>("wines/" + slug + "/questions");
