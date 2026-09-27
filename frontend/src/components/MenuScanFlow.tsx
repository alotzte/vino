import { useState } from "react";
import { assetUrl, scanMenu } from "../api";
import type { MenuMatch } from "../types";

interface Props {
  onOpenWine: (slug: string) => void;
}

type Stage = "idle" | "loading" | "result";

export default function MenuScanFlow({ onOpenWine }: Props) {
  const [stage, setStage] = useState<Stage>("idle");
  const [items, setItems] = useState<MenuMatch[]>([]);

  async function onPick(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    setStage("loading");
    try {
      const data = await scanMenu(file);
      setItems(data.items);
      setStage("result");
    } catch {
      setStage("idle");
    }
  }

  function openWine(slug: string) {
    setStage("idle");
    onOpenWine(slug);
  }

  return (
    <>
      <label className="btn btn--ghost menu-scan-btn">
        Сканер винной карты ресторана
        <input type="file" accept="image/*" hidden onChange={onPick} />
      </label>

      {stage !== "idle" && (
        <div className="modal-backdrop" onClick={() => stage === "result" && setStage("idle")}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal__head">
              <b>Винная карта ресторана</b>
              <button className="modal__close" onClick={() => setStage("idle")} aria-label="Закрыть">
                ×
              </button>
            </div>

            {stage === "loading" ? (
              <p className="empty-note">Распознаём меню…</p>
            ) : (
              <>
                <div className="menu-results">
                  {items.map((m) => (
                    <div className="menu-result" key={m.slug} onClick={() => openWine(m.slug)}>
                      {m.image && <img src={assetUrl(m.image)} alt="" loading="lazy" />}
                      <div className="menu-result__body">
                        <b>{m.name}</b>
                        <i>{m.manufacturer}</i>
                        <span className="menu-result__score">
                          Оценка {m.expert_score}/100 · совпадение {Math.round(m.match_confidence * 100)}%
                        </span>
                        <span className="menu-result__price">
                          В меню ~{m.menu_price} ₽ · в рознице ~{m.retail_price} ₽ (наценка +{m.markup_percent}%)
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
                <p className="modal__note">Демо-данные</p>
              </>
            )}
          </div>
        </div>
      )}
    </>
  );
}
