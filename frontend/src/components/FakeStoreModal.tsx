import { useMemo } from "react";

const STORE_NAMES = [
  "Магнит WineStyle",
  "Ашан Винотека",
  "Пятёрочка Wine&Spirits",
  "Перекрёсток. Вина мира",
  "Лента Cave de Vin",
  "SimpleWine",
];

function seedFromString(s: string): number {
  let h = 0;
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) >>> 0;
  return h;
}

function fakeStores(slug: string) {
  const seed = seedFromString(slug);
  const count = 2 + (seed % 2);
  const stores = [];
  for (let i = 0; i < count; i++) {
    const idx = (seed + i * 7) % STORE_NAMES.length;
    const distance = 150 + ((seed + i * 91) % 850);
    stores.push({ name: STORE_NAMES[idx], distance });
  }
  return stores.sort((a, b) => a.distance - b.distance);
}

interface Props {
  slug: string;
  onClose: () => void;
}

export default function FakeStoreModal({ slug, onClose }: Props) {
  const stores = useMemo(() => fakeStores(slug), [slug]);

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal__head">
          <b>Где купить рядом</b>
          <button className="modal__close" onClick={onClose} aria-label="Закрыть">
            ×
          </button>
        </div>
        <div className="modal__body">
          {stores.map((s, i) => (
            <div className="store-row" key={i}>
              <span>{s.name}</span>
              <span className="store-row__dist">{s.distance} м</span>
            </div>
          ))}
        </div>
        <p className="modal__note">Демо-данные</p>
      </div>
    </div>
  );
}
