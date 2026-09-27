import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { useEffect, useRef } from "react";
import type { Winery } from "../types";

interface Props {
  wineries: Winery[];
  onSelectWinery?: (manufacturer: string) => void;
  onCheckin?: (manufacturer: string) => void;
}

const RUSSIA_CENTER: [number, number] = [46.5, 40];

export default function WineryMap({ wineries, onSelectWinery, onCheckin }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const layerRef = useRef<L.LayerGroup | null>(null);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    const map = L.map(containerRef.current, { attributionControl: false }).setView(RUSSIA_CENTER, 6);
    L.control.attribution({ prefix: false, position: "bottomright" }).addTo(map);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "© OpenStreetMap",
      maxZoom: 18,
    }).addTo(map);
    layerRef.current = L.layerGroup().addTo(map);
    mapRef.current = map;
    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const layer = layerRef.current;
    const map = mapRef.current;
    if (!layer || !map) return;
    layer.clearLayers();

    const points: L.LatLngExpression[] = [];
    for (const w of wineries) {
      if (w.lat == null || w.lon == null) continue;
      points.push([w.lat, w.lon]);
      const engaged = w.visited || w.checked_in;
      const icon = L.divIcon({
        className: "",
        html: `<span class="map-pin${engaged ? " map-pin--visited" : ""}"></span>`,
        iconSize: [16, 16],
        iconAnchor: [8, 8],
        popupAnchor: [0, -8],
      });

      const statusLine = w.checked_in
        ? " · вы отметились здесь"
        : w.visited
        ? " · вы уже пробовали"
        : "";
      const selectBtn = onSelectWinery ? '<button class="popup-btn">Смотреть вина →</button>' : "";
      const checkinBtn =
        onCheckin && !w.checked_in ? '<button class="popup-btn popup-btn--checkin">Я здесь →</button>' : "";

      const marker = L.marker([w.lat, w.lon], { icon })
        .addTo(layer)
        .bindPopup(
          `<b>${w.manufacturer}</b><br>${w.region ?? ""}<br>${w.wine_count} вин в каталоге${statusLine}<br>${selectBtn}${checkinBtn}`
        );

      marker.on("popupopen", (e) => {
        const el = e.popup.getElement();
        if (onSelectWinery) {
          el?.querySelector(".popup-btn:not(.popup-btn--checkin)")?.addEventListener("click", () => onSelectWinery(w.manufacturer));
        }
        if (onCheckin) {
          el?.querySelector(".popup-btn--checkin")?.addEventListener("click", () => onCheckin(w.manufacturer));
        }
      });
    }
    if (points.length > 0) {
      map.fitBounds(L.latLngBounds(points), { padding: [24, 24], maxZoom: 8 });
    }
  }, [wineries, onSelectWinery, onCheckin]);

  return <div className="winery-map" ref={containerRef} />;
}
