import { useEffect, useState } from "react";
import { getWineScores } from "../api";
import type { WineScores as Scores } from "../types";

export default function WineScores({ slug }: { slug: string }) {
  const [scores, setScores] = useState<Scores | null>(null);

  useEffect(() => {
    setScores(null);
    getWineScores(slug)
      .then(setScores)
      .catch(() => {});
  }, [slug]);

  if (!scores) return null;

  return (
    <div className="scores">
      <div className="score">
        <i>Народная оценка</i>
        <b>
          {scores.crowd.toFixed(1)}
          <span>/5</span>
        </b>
        <span className="score__bar">
          <span style={{ width: `${(scores.crowd / 5) * 100}%` }} />
        </span>
      </div>
      <div className="score">
        <i>Оценка экспертов</i>
        <b>
          {scores.expert}
          <span>/100</span>
        </b>
        <span className="score__bar">
          <span style={{ width: `${scores.expert}%` }} />
        </span>
      </div>
    </div>
  );
}
