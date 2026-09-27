import { useState } from "react";
import WineRail from "../components/WineRail";
import type { Candidate } from "../types";

const PREVIEW_COUNT = 6;

interface Props {
  candidates: Candidate[];
  onBack: () => void;
  onOpenWine: (slug: string) => void;
}

export default function EmptyScreen({ candidates, onBack, onOpenWine }: Props) {
  const [showAll, setShowAll] = useState(false);
  const shown = showAll ? candidates : candidates.slice(0, PREVIEW_COUNT);
  const hidden = candidates.length - shown.length;

  return (
    <section className="screen screen--empty is-active">
      <div className="empty">
        <span className="empty__icon">🔍</span>
        <h2>Точного совпадения нет</h2>
        <p>Этого вина пока нет в каталоге "Своё Вино". Вот ближайшие по стилю позиции:</p>
        <WineRail candidates={shown} wrap onSelect={onOpenWine} />
        {hidden > 0 && (
          <button className="btn btn--ghost btn--sm" onClick={() => setShowAll(true)}>
            Показать ещё ({hidden})
          </button>
        )}
        <button className="btn btn--ghost btn--sm" onClick={onBack}>
          Сканировать заново
        </button>
      </div>
    </section>
  );
}
