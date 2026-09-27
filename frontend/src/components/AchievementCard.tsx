import type { Achievement } from "../types";

export default function AchievementCard({ a }: { a: Achievement }) {
  const pct = Math.round((a.progress / a.threshold) * 100);
  return (
    <div className={`achievement-card${a.unlocked ? " is-unlocked" : ""}`}>
      <span className="achievement-card__icon">{a.icon}</span>
      <span className="achievement-card__title">{a.title}</span>
      <span className="achievement-card__descr">{a.description}</span>
      <span className="achievement-card__bar">
        <span style={{ width: `${pct}%` }} />
      </span>
      <span className="achievement-card__descr">
        {a.progress}/{a.threshold}
      </span>
    </div>
  );
}
