import { useEffect, useState } from "react";
import { checkinWinery, getWineries } from "../api";
import WineryMap from "../components/WineryMap";
import type { Winery } from "../types";

interface Props {
  onSelectWinery: (manufacturer: string) => void;
}

export default function MapScreen({ onSelectWinery }: Props) {
  const [wineries, setWineries] = useState<Winery[]>([]);

  function load() {
    getWineries()
      .then((r) => setWineries(r.items))
      .catch(() => {});
  }

  useEffect(load, []);

  async function handleCheckin(manufacturer: string) {
    await checkinWinery(manufacturer).catch(() => {});
    load();
  }

  const visited = wineries.filter((w) => w.visited || w.checked_in).length;

  return (
    <section className="screen screen--map is-active">
      <div className="map-head">
        <h1 className="card__title">Карта виноделен</h1>
        <p className="map-head__descr">
          {wineries.length} виноделен из каталога · открыто для себя {visited}. Расположение приближённое, по региону.
        </p>
      </div>
      <WineryMap wineries={wineries} onSelectWinery={onSelectWinery} onCheckin={handleCheckin} />
    </section>
  );
}
