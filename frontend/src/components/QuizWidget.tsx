import { useEffect, useState } from "react";
import { checkQuizAnswer, getQuizToday, submitQuiz } from "../api";
import type { QuizCheckResult, QuizResult, QuizToday } from "../types";

type Phase = "answering" | "revealed";

function tier(score: number, total: number): { emoji: string; text: string } {
  const pct = total > 0 ? score / total : 0;
  if (pct === 1) return { emoji: "🏆", text: "Идеальный результат!" };
  if (pct >= 0.8) return { emoji: "🎉", text: "Отличный результат!" };
  if (pct >= 0.5) return { emoji: "👍", text: "Неплохо!" };
  return { emoji: "📚", text: "Есть куда расти - новый тест завтра" };
}

export default function QuizWidget() {
  const [quiz, setQuiz] = useState<QuizToday | null>(null);
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [result, setResult] = useState<QuizResult | null>(null);
  const [open, setOpen] = useState(false);
  const [step, setStep] = useState(0);
  const [phase, setPhase] = useState<Phase>("answering");
  const [feedback, setFeedback] = useState<QuizCheckResult | null>(null);

  useEffect(() => {
    getQuizToday()
      .then(setQuiz)
      .catch(() => {});
  }, []);

  function openModal() {
    setStep(0);
    setPhase("answering");
    setFeedback(null);
    setResult(null);
    setOpen(true);
  }

  function pick(questionId: string, optionIndex: number) {
    if (phase !== "answering") return;
    setAnswers((prev) => ({ ...prev, [questionId]: optionIndex }));
  }

  async function reveal() {
    if (!question || picked === undefined) return;
    const r = await checkQuizAnswer(question.id, picked);
    setFeedback(r);
    setPhase("revealed");
  }

  async function advance() {
    if (!quiz) return;
    setFeedback(null);
    setPhase("answering");
    if (step + 1 >= quiz.questions.length) {
      setResult(await submitQuiz(answers));
    } else {
      setStep((s) => s + 1);
    }
  }

  if (!quiz) return null;

  const done = quiz.completed_today || result !== null;
  const score = result?.score ?? quiz.score ?? 0;
  const total = result?.total ?? quiz.questions.length ?? 5;
  const question = quiz.questions[step];
  const picked = question ? answers[question.id] : undefined;
  const t = tier(score, total);

  return (
    <>
      <button className="lesson-card lesson-card--quiz" onClick={openModal}>
        <span className="lesson-card__icon">🧠</span>
        <span className="lesson-card__body">
          <b>Тест дня</b>
          <i>{done ? `Пройден · ${score}/${total}` : "5 вопросов · 4 варианта"}</i>
        </span>
        {done && <span className="lesson-card__done">✓</span>}
      </button>

      {open && (
        <div className="modal-backdrop" onClick={() => setOpen(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal__head">
              <b>🧠 Тест дня</b>
              <button className="modal__close" onClick={() => setOpen(false)} aria-label="Закрыть">
                ×
              </button>
            </div>

            {done ? (
              <div className="quiz-result">
                <span className="quiz-result__emoji">{t.emoji}</span>
                <div className="quiz-result__score">
                  {score}
                  <span>/{total}</span>
                </div>
                <p className="quiz-result__text">{t.text}</p>
              </div>
            ) : question ? (
              <>
                <div className="quiz-progress">
                  <span className="quiz-progress__bar">
                    <span style={{ width: `${((step + 1) / quiz.questions.length) * 100}%` }} />
                  </span>
                  <span className="quiz-progress__label">
                    Вопрос {step + 1} из {quiz.questions.length}
                  </span>
                </div>

                <div className="quiz-q">
                  <div className="quiz-q__title">{question.text}</div>
                  <div className="quiz-q__opts">
                    {question.options.map((opt, i) => {
                      let cls = "quiz-opt";
                      if (picked === i) cls += " is-on";
                      if (phase === "revealed" && feedback) {
                        if (i === feedback.correct_index) cls += " is-correct";
                        else if (i === picked) cls += " is-wrong";
                      }
                      return (
                        <button key={i} className={cls} onClick={() => pick(question.id, i)}>
                          <span>{opt}</span>
                          {phase === "revealed" && feedback && i === feedback.correct_index && <b className="quiz-opt__mark">✓</b>}
                          {phase === "revealed" && feedback && i === picked && !feedback.correct && (
                            <b className="quiz-opt__mark">✗</b>
                          )}
                        </button>
                      );
                    })}
                  </div>
                </div>

                {phase === "answering" ? (
                  <button className="btn btn--primary btn--sm" disabled={picked === undefined} onClick={reveal}>
                    Ответить
                  </button>
                ) : (
                  <button className="btn btn--primary btn--sm" onClick={advance}>
                    {step + 1 === quiz.questions.length ? "Посмотреть результат" : "Дальше"}
                  </button>
                )}
              </>
            ) : null}
          </div>
        </div>
      )}
    </>
  );
}
