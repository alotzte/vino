import { useEffect, useState } from "react";
import { getRelatedQuestions } from "../api";
import type { RelatedQuestion } from "../types";

export default function RelatedQuestions({ slug }: { slug: string }) {
  const [items, setItems] = useState<RelatedQuestion[]>([]);
  const [openId, setOpenId] = useState<string | null>(null);

  useEffect(() => {
    setItems([]);
    setOpenId(null);
    getRelatedQuestions(slug)
      .then((r) => setItems(r.items))
      .catch(() => {});
  }, [slug]);

  if (items.length === 0) return null;

  return (
    <div className="paa">
      {items.map((q) => (
        <div className={`paa-item${openId === q.id ? " is-open" : ""}`} key={q.id}>
          <button className="paa-item__q" onClick={() => setOpenId(openId === q.id ? null : q.id)}>
            <span>{q.question}</span>
            <span className="paa-item__chev">⌄</span>
          </button>
          {openId === q.id && <p className="paa-item__a">{q.answer}</p>}
        </div>
      ))}
    </div>
  );
}
