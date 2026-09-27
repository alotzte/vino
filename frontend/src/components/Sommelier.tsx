import { useState } from "react";
import { askSommelier, getSommelierQuestions } from "../api";
import type { SommelierQuestion, SommelierResponse } from "../types";

interface Props {
  slug: string;
}

type Stage = "idle" | "questions" | "verdict";

export default function Sommelier({ slug }: Props) {
  const [stage, setStage] = useState<Stage>("idle");
  const [questions, setQuestions] = useState<SommelierQuestion[]>([]);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [verdict, setVerdict] = useState<SommelierResponse | null>(null);
  const [thinking, setThinking] = useState(false);

  async function start() {
    const { questions } = await getSommelierQuestions();
    setQuestions(questions);
    setAnswers({});
    setStage("questions");
  }

  async function ask() {
    setThinking(true);
    const data = await askSommelier(slug, Object.values(answers));
    setVerdict(data);
    setThinking(false);
    setStage("verdict");
  }

  if (stage === "idle") {
    return (
      <button className="btn btn--primary btn--sm" onClick={start}>
        Задать пару вопросов
      </button>
    );
  }

  if (stage === "questions") {
    return (
      <>
        {questions.map((q) => (
          <div className="q" key={q.id}>
            <div className="q__title">{q.title}</div>
            <div className="q__opts">
              {q.options.map((o) => (
                <button
                  key={o.id}
                  className={`opt${answers[q.id] === o.id ? " is-on" : ""}`}
                  onClick={() => setAnswers((prev) => ({ ...prev, [q.id]: o.id }))}
                >
                  {o.label}
                </button>
              ))}
            </div>
          </div>
        ))}
        <button className="btn btn--primary btn--sm" onClick={ask} disabled={thinking}>
          {thinking ? "Думаем…" : "Показать рекомендацию"}
        </button>
      </>
    );
  }

  return (
    <>
      <p className="verdict">{verdict?.verdict}</p>
      <div className="q__title">Подойдёт к столу</div>
      <div className="pairings">
        {(verdict?.pairings || []).map((p) => (
          <span className="pairing" key={p}>
            {p}
          </span>
        ))}
      </div>
      <button className="btn btn--primary btn--sm" onClick={start}>
        Спросить заново
      </button>
    </>
  );
}
