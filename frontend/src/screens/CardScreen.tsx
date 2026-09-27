import { useEffect, useState } from "react";
import { askSommelier, assetUrl } from "../api";
import FakeStoreModal from "../components/FakeStoreModal";
import RatingStars from "../components/RatingStars";
import RelatedQuestions from "../components/RelatedQuestions";
import Sommelier from "../components/Sommelier";
import WineRail from "../components/WineRail";
import WineScores from "../components/WineScores";
import { inMax, openExternal, shareWine, wineDeepLink } from "../max";
import type { Candidate, ScanResponse } from "../types";

interface Props {
  data: ScanResponse;
  botName: string | null;
  onBack: () => void;
  onOpenWine: (slug: string) => void;
}

function chip(text: string | null | undefined, accent?: boolean) {
  return text ? <span className={`chip${accent ? " chip--accent" : ""}`}>{text}</span> : null;
}

const SPEC_ICONS: Record<string, string> = {
  Категория: "🍇",
  Крепость: "🌡️",
  Цвет: "🎨",
  Подача: "❄️",
};

function spec(label: string, value: string | null | undefined) {
  return value ? (
    <div className="spec">
      <i>
        <span className="spec__icon" aria-hidden="true">{SPEC_ICONS[label]}</span>
        {label}
      </i>
      <b>{value}</b>
    </div>
  ) : null;
}

function AlternativesRail({ slug, onOpenWine }: { slug: string; onOpenWine: (slug: string) => void }) {
  const [candidates, setCandidates] = useState<Candidate[] | null>(null);

  useEffect(() => {
    setCandidates(null);
    askSommelier(slug, [])
      .then((data) => setCandidates(data.alternatives || []))
      .catch(() => setCandidates([]));
  }, [slug]);

  if (candidates === null) return <span className="chip">Подбираем…</span>;
  return <WineRail candidates={candidates} emptyLabel="Пока нет аналогов" onSelect={onOpenWine} />;
}

export default function CardScreen({ data, botName, onBack, onOpenWine }: Props) {
  const w = data.wine!;
  const [storesOpen, setStoresOpen] = useState(false);
  const [shareNote, setShareNote] = useState<string | null>(null);

  async function share() {
    const link = botName
      ? wineDeepLink(botName, w.slug)
      : `${location.origin}${location.pathname}?startapp=w_${w.slug}`;
    const text = `${w.name}${w.manufacturer ? " - " + w.manufacturer : ""}`;
    const res = await shareWine(text, link);
    if (res === "copied") setShareNote("Ссылка скопирована");
    else if (res === "failed") setShareNote("Не удалось поделиться");
    if (res === "copied" || res === "failed") setTimeout(() => setShareNote(null), 1800);
  }

  return (
    <section className="screen screen--card is-active">
      <div className="hero">
        <button className="hero__back" aria-label="Назад" onClick={onBack}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        {w.image && <img src={assetUrl(w.image)} alt={w.name} />}
        <div className="hero__fade"></div>
        <span className="hero__badge">совпадение {Math.round(data.confidence * 100)}%</span>
      </div>

      <div className="card">
        <p className="card__maker">{w.manufacturer || "Винодельня не указана"}</p>
        <h1 className="card__title">{w.name}</h1>

        <div className="chips">
          {chip(w.region, true)}
          {(w.grapes || []).map((g) => (
            <span className="chip" key={g}>
              {g}
            </span>
          ))}
        </div>

        <div className="specs">
          {spec("Категория", w.category)}
          {spec("Крепость", w.abv)}
          {spec("Цвет", w.color)}
          {spec("Подача", w.serving_temperature)}
        </div>

        <div className="rating">
          <span>Ваша оценка</span>
          <RatingStars slug={w.slug} key={w.slug} />
        </div>

        <WineScores slug={w.slug} key={w.slug} />

        <button className="btn btn--ghost btn--sm store-btn" onClick={() => setStoresOpen(true)}>
          Найти в магазинах
        </button>
        <button className="btn btn--ghost btn--sm store-btn" onClick={share}>
          {shareNote ?? (inMax ? "Поделиться в MAX" : "Поделиться")}
        </button>
        {storesOpen && <FakeStoreModal slug={w.slug} onClose={() => setStoresOpen(false)} />}

        <h2 className="section-title">Описание</h2>
        <p className="card__descr">{w.description || "-"}</p>

        <h2 className="section-title">Вопросы по теме</h2>
        <RelatedQuestions slug={w.slug} key={w.slug} />

        <div className="sommelier">
          <div className="sommelier__head">
            <span className="sommelier__icon" aria-hidden="true">
              ✦
            </span>
            <div>
              <b>Цифровой сомелье</b>
              <i>Подскажем, к чему подать и чем заменить</i>
            </div>
          </div>
          <div className="sommelier__body">
            <Sommelier slug={w.slug} key={w.slug} />
          </div>
        </div>

        <h2 className="section-title">Похожие вина других виноделен</h2>
        <AlternativesRail slug={w.slug} onOpenWine={onOpenWine} />

        {w.url && (
          <a
            className="card__link"
            href={w.url}
            target="_blank"
            rel="noopener"
            onClick={(e) => {
              if (openExternal(w.url!)) e.preventDefault();
            }}
          >
            Открыть на vino-svoe.ru →
          </a>
        )}
      </div>
    </section>
  );
}
