import type { BonusTier } from "../types";

export default function BonusCard({ b }: { b: BonusTier }) {
  const pct = Math.round((b.progress / b.threshold) * 100);
  return (
    <div className={`achievement-card${b.unlocked ? " is-unlocked" : ""}`}>
      <span className="achievement-card__icon">{b.icon}</span>
      <span className="achievement-card__title">{b.title}</span>
      <span className="achievement-card__descr">{b.description}</span>
      <span className="achievement-card__bar">
        <span style={{ width: `${pct}%` }} />
      </span>
      <span className="achievement-card__descr">
        {b.progress}/{b.threshold} баллов
      </span>
    </div>
  );
}
