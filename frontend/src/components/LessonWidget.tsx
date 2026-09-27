import { useEffect, useState } from "react";
import { completeLesson, getLearningStatus } from "../api";
import type { LearningStatus } from "../types";

function daysWord(n: number): string {
  const mod10 = n % 10;
  const mod100 = n % 100;
  if (mod10 === 1 && mod100 !== 11) return "день";
  if ([2, 3, 4].includes(mod10) && ![12, 13, 14].includes(mod100)) return "дня";
  return "дней";
}

export default function LessonWidget() {
  const [status, setStatus] = useState<LearningStatus | null>(null);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    getLearningStatus()
      .then(setStatus)
      .catch(() => {});
  }, []);

  async function complete() {
    try {
      setStatus(await completeLesson());
    } catch {}
  }

  if (!status) return null;

  return (
    <>
      <button className="lesson-card" onClick={() => setOpen(true)}>
        <span className="lesson-card__icon">{status.lesson.icon}</span>
        <span className="lesson-card__body">
          <b>Минута винной грамотности</b>
          <i>
            {status.lesson.title}
            {status.streak > 0 ? ` · 🔥 ${status.streak} ${daysWord(status.streak)}` : ""}
          </i>
        </span>
        {status.completed_today && <span className="lesson-card__done">✓</span>}
      </button>

      {open && (
        <div className="modal-backdrop" onClick={() => setOpen(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal__head">
              <b>
                {status.lesson.icon} {status.lesson.title}
              </b>
              <button className="modal__close" onClick={() => setOpen(false)} aria-label="Закрыть">
                ×
              </button>
            </div>
            <p className="lesson-body">{status.lesson.body}</p>

            {status.completed_today ? (
              <p className="lesson-done-note">
                Урок на сегодня пройден · стрик {status.streak} {daysWord(status.streak)}
              </p>
            ) : (
              <button className="btn btn--primary btn--sm" onClick={complete}>
                Я прошёл(а) урок
              </button>
            )}

            <h2 className="section-title">Лига недели</h2>
            <div className="league">
              {status.league.members.map((m) => (
                <div key={m.name} className={`league-row${m.is_user ? " is-user" : ""}`}>
                  <span className="league-row__rank">{m.rank}</span>
                  <span className="league-row__name">{m.name}</span>
                  <span className="league-row__xp">{m.xp} XP</span>
                </div>
              ))}
            </div>
            <p className="modal__note">Лига учебная - соперники здесь демо-боты, не реальные пользователи</p>
          </div>
        </div>
      )}
    </>
  );
}
