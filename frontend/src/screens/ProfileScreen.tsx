import { useEffect, useState } from "react";
import { checkinWinery, getAchievements, getHistory, getMe, getPoints, getWineries } from "../api";
import AchievementCard from "../components/AchievementCard";
import BonusCard from "../components/BonusCard";
import HistoryRow from "../components/HistoryRow";
import WineryMap from "../components/WineryMap";
import type { Achievement, HistoryItem, MeResponse, PointsStatus, Winery } from "../types";

interface Props {
  onOpenWine: (slug: string) => void;
  onSelectWinery: (manufacturer: string) => void;
}

type Tab = "history" | "achievements" | "map" | "points";

export default function ProfileScreen({ onOpenWine, onSelectWinery }: Props) {
  const [tab, setTab] = useState<Tab>("history");
  const [me, setMe] = useState<MeResponse | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [achievements, setAchievements] = useState<Achievement[]>([]);
  const [wineries, setWineries] = useState<Winery[]>([]);
  const [points, setPoints] = useState<PointsStatus | null>(null);

  function loadWineries() {
    getWineries().then((r) => setWineries(r.items)).catch(() => {});
  }

  useEffect(() => {
    getMe().then(setMe).catch(() => {});
    getHistory().then((r) => setHistory(r.items)).catch(() => {});
    getAchievements().then((r) => setAchievements(r.items)).catch(() => {});
    getPoints().then(setPoints).catch(() => {});
    loadWineries();
  }, []);

  async function handleCheckin(manufacturer: string) {
    await checkinWinery(manufacturer).catch(() => {});
    loadWineries();
    getPoints().then(setPoints).catch(() => {});
  }

  const engagedWineries = wineries.filter((w) => w.visited || w.checked_in);

  return (
    <section className="screen screen--profile is-active">
      <div className="profile-head">
        <h1 className="card__title">Профиль</h1>
      </div>

      <div className="profile-stats">
        <div className="profile-stat">
          <b>{me?.stats.total_scans ?? "-"}</b>
          <i>сканов</i>
        </div>
        <div className="profile-stat">
          <b>{me?.stats.distinct_regions ?? "-"}</b>
          <i>регионов</i>
        </div>
        <div className="profile-stat">
          <b>{me?.stats.rated_wines ?? "-"}</b>
          <i>оценено</i>
        </div>
        <div className="profile-stat">
          <b>{points?.points ?? "-"}</b>
          <i>баллов</i>
        </div>
      </div>

      <div className="tabs">
        <button className={`tab${tab === "history" ? " is-on" : ""}`} onClick={() => setTab("history")}>
          История
        </button>
        <button className={`tab${tab === "achievements" ? " is-on" : ""}`} onClick={() => setTab("achievements")}>
          Ачивки
        </button>
        <button className={`tab${tab === "map" ? " is-on" : ""}`} onClick={() => setTab("map")}>
          Карта
        </button>
        <button className={`tab${tab === "points" ? " is-on" : ""}`} onClick={() => setTab("points")}>
          Баллы
        </button>
      </div>

      <div className="profile-body">
        <div className={`tab-panel${tab === "history" ? " is-on" : ""}`}>
          {history.length === 0 ? (
            <p className="empty-note">Пока нет сканирований</p>
          ) : (
            history.map((item, i) => <HistoryRow item={item} onSelect={onOpenWine} key={item.created_at + i} />)
          )}
        </div>
        <div className={`tab-panel${tab === "achievements" ? " is-on" : ""}`}>
          <div className="achievement-grid">
            {achievements.map((a) => (
              <AchievementCard a={a} key={a.id} />
            ))}
          </div>
        </div>
        <div className={`tab-panel tab-panel--map${tab === "map" ? " is-on" : ""}`}>
          {tab === "map" &&
            (engagedWineries.length === 0 ? (
              <p className="empty-note">Пока нет пройденных виноделен - отсканируйте вино или отметьтесь на карте</p>
            ) : (
              <WineryMap wineries={engagedWineries} onSelectWinery={onSelectWinery} onCheckin={handleCheckin} />
            ))}
        </div>
        <div className={`tab-panel${tab === "points" ? " is-on" : ""}`}>
          <p className="points-note">
            Баллы начисляются за отзывы (+15) и чекины на винодельнях (+25). {points?.reviews ?? 0}{" "}
            отзывов · {points?.checkins ?? 0} чекинов.
          </p>
          <div className="achievement-grid">
            {(points?.bonuses ?? []).map((b) => (
              <BonusCard b={b} key={b.id} />
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
