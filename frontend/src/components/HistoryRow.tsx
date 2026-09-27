import { assetUrl } from "../api";
import type { HistoryItem } from "../types";

interface Props {
  item: HistoryItem;
  onSelect: (slug: string) => void;
}

export default function HistoryRow({ item, onSelect }: Props) {
  const wine = item.wine;
  const date = new Date(item.created_at).toLocaleString("ru-RU", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });

  return (
    <div className="history-item" onClick={() => wine && onSelect(wine.slug)}>
      {wine?.image && <img src={assetUrl(wine.image)} alt="" loading="lazy" />}
      <div className="history-item__body">
        <div className="history-item__name">{wine?.name || "Не найдено"}</div>
        <div className="history-item__meta">
          {date}
          {item.region ? ` · ${item.region}` : ""}
        </div>
      </div>
      {item.rating ? <span className="history-item__rating">{"🍷".repeat(item.rating)}</span> : null}
    </div>
  );
}
