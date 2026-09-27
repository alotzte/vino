import { useEffect, useState } from "react";
import { assetUrl, browseWines } from "../api";
import type { Wine } from "../types";

const REGIONS = [
  "Кубань",
  "Крым",
  "Дагестан",
  "Долина Дона",
  "Ставрополье",
  "Нижняя Волга",
  "Самара",
  "Северная Осетия — Алания",
  "Дальневосточная зона",
];

const PAGE_SIZE = 24;

interface Props {
  onOpenWine: (slug: string) => void;
  initialManufacturer?: string | null;
}

export default function CatalogScreen({ onOpenWine, initialManufacturer = null }: Props) {
  const [manufacturer, setManufacturer] = useState<string | null>(initialManufacturer);
  const [region, setRegion] = useState<string | null>(null);
  const [items, setItems] = useState<Wine[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(false);

  async function load(nextOffset: number, r: string | null, m: string | null) {
    setLoading(true);
    const data = await browseWines({
      region: m ? undefined : r ?? undefined,
      manufacturer: m ?? undefined,
      limit: PAGE_SIZE,
      offset: nextOffset,
    });
    setItems((prev) => (nextOffset === 0 ? data.items : [...prev, ...data.items]));
    setTotal(data.total);
    setOffset(nextOffset + data.items.length);
    setLoading(false);
  }

  useEffect(() => {
    load(0, region, manufacturer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [region, manufacturer]);

  return (
    <section className="screen screen--catalog is-active">
      <div className="catalog-head">
        <h1 className="card__title">Каталог</h1>
        {manufacturer ? (
          <div className="winery-badge">
            <span>{manufacturer}</span>
            <button onClick={() => setManufacturer(null)}>× показать все винодельни</button>
          </div>
        ) : (
          <div className="catalog-filters">
            <button className={`filter-chip${region === null ? " is-on" : ""}`} onClick={() => setRegion(null)}>
              Все
            </button>
            {REGIONS.map((r) => (
              <button key={r} className={`filter-chip${region === r ? " is-on" : ""}`} onClick={() => setRegion(r)}>
                {r}
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="catalog-list">
        {items.map((w) => (
          <div className="catalog-card" key={w.slug} onClick={() => onOpenWine(w.slug)}>
            {w.image && <img src={assetUrl(w.image)} alt="" loading="lazy" />}
            <div className="catalog-card__body">
              <div className="catalog-card__name">{w.name}</div>
              <div className="catalog-card__meta">
                {w.manufacturer}
                {w.region ? ` · ${w.region}` : ""}
              </div>
            </div>
          </div>
        ))}
      </div>

      {offset < total && (
        <button className="btn btn--ghost btn--sm" onClick={() => load(offset, region, manufacturer)} disabled={loading}>
          {loading ? "Загружаем…" : `Показать ещё (${total - offset})`}
        </button>
      )}
    </section>
  );
}
