import { useEffect, useRef, useState } from "react";
import { getHealth, getWine, scanImage } from "./api";
import AchievementToast from "./components/AchievementToast";
import AgeGate from "./components/AgeGate";
import BottomTabs from "./components/BottomTabs";
import MetricsBar from "./components/MetricsBar";
import TopBar from "./components/TopBar";
import CardScreen from "./screens/CardScreen";
import CatalogScreen from "./screens/CatalogScreen";
import EmptyScreen from "./screens/EmptyScreen";
import LoadingScreen from "./screens/LoadingScreen";
import MapScreen from "./screens/MapScreen";
import ProfileScreen from "./screens/ProfileScreen";
import ScanScreen from "./screens/ScanScreen";
import type { Achievement, ScanResponse, ScanStage, Tab } from "./types";
import { haptic, maxReady, parseStartParam, setBackButton } from "./max";

function isAgeConfirmed(): boolean {
  try {
    return localStorage.getItem("vino_age_confirmed") === "1";
  } catch {
    return false;
  }
}

export default function App() {
  const [ageConfirmed, setAgeConfirmed] = useState(isAgeConfirmed);
  const [activeTab, setActiveTab] = useState<Tab>("scan");
  const [scanStage, setScanStage] = useState<ScanStage>("idle");
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [result, setResult] = useState<ScanResponse | null>(null);
  const [loadingError, setLoadingError] = useState<string | null>(null);
  const [catalogLabel, setCatalogLabel] = useState("-");
  const [metricsHidden, setMetricsHidden] = useState(true);
  const [metrics, setMetrics] = useState<{ f1: number; f5: number; ms: number; engine: string } | null>(null);
  const [toastAchievements, setToastAchievements] = useState<Achievement[]>([]);
  const [catalogManufacturer, setCatalogManufacturer] = useState<string | null>(null);
  const [botName, setBotName] = useState<string | null>(null);
  const previousPreview = useRef<string | null>(null);

  useEffect(() => {
    maxReady();
    getHealth()
      .then((h) => {
        setBotName(h.max_bot_name);
        setCatalogLabel(`${h.catalog_size} вин`);
        setMetrics((m) => ({ f1: m?.f1 ?? 0, f5: m?.f5 ?? 0, ms: m?.ms ?? 0, engine: h.engine }));
      })
      .catch(() => setCatalogLabel("офлайн"));
  }, []);

  const startHandled = useRef(false);
  useEffect(() => {
    if (!ageConfirmed || startHandled.current) return;
    startHandled.current = true;
    const target = parseStartParam();
    if (target?.kind === "wine") openWine(target.slug).catch(() => setScanStage("idle"));
    if (target?.kind === "tab") setActiveTab(target.tab);
  }, [ageConfirmed]);

  const backHandler =
    activeTab === "scan" && (scanStage === "card" || scanStage === "empty")
      ? () => setScanStage("idle")
      : activeTab !== "scan"
        ? () => setActiveTab("scan")
        : null;
  useEffect(() => setBackButton(backHandler), [activeTab, scanStage]);

  async function handleFile(file: File) {
    if (previousPreview.current) URL.revokeObjectURL(previousPreview.current);
    const url = URL.createObjectURL(file);
    previousPreview.current = url;
    setPreviewUrl(url);
    setLoadingError(null);
    setScanStage("loading");

    try {
      const data = await scanImage(file);
      setMetrics({ f1: data.f1_top1, f5: data.f1_top5, ms: data.elapsed_ms, engine: data.engine });
      setResult(data);
      setScanStage(data.found && data.wine ? "card" : "empty");
      haptic(data.found && data.wine ? "success" : "warning");
      if (data.new_achievements.length > 0) setToastAchievements(data.new_achievements);
    } catch (e) {
      console.error(e);
      haptic("error");
      setLoadingError("Не удалось распознать. Попробуйте ещё раз.");
      setTimeout(() => {
        setLoadingError(null);
        setScanStage("idle");
      }, 1600);
    }
  }

  async function openWine(slug: string) {
    const wine = await getWine(slug);
    setResult({
      slug: wine.slug,
      found: true,
      confidence: 1,
      f1_top1: 1,
      f1_top5: 1,
      elapsed_ms: 0,
      engine: "catalog",
      wine,
      candidates: [],
      new_achievements: [],
    });
    setScanStage("card");
    setActiveTab("scan");
  }

  function openWinery(manufacturer: string) {
    setCatalogManufacturer(manufacturer);
    setActiveTab("catalog");
  }

  function changeTab(tab: Tab) {
    if (tab === "catalog") setCatalogManufacturer(null);
    setActiveTab(tab);
  }

  if (!ageConfirmed) {
    return (
      <AgeGate
        onConfirm={() => {
          try {
            localStorage.setItem("vino_age_confirmed", "1");
          } catch {}
          setAgeConfirmed(true);
        }}
      />
    );
  }

  return (
    <div className="phone">
      <TopBar catalogLabel={catalogLabel} onToggleMetrics={() => setMetricsHidden((h) => !h)} />
      <MetricsBar hidden={metricsHidden} metrics={metrics} />

      {activeTab === "scan" && scanStage === "idle" && (
        <ScanScreen previewUrl={previewUrl} onFile={handleFile} onOpenWine={openWine} />
      )}
      {activeTab === "scan" && scanStage === "loading" && <LoadingScreen errorMessage={loadingError} />}
      {activeTab === "scan" && scanStage === "card" && result?.wine && (
        <CardScreen data={result} botName={botName} onBack={() => setScanStage("idle")} onOpenWine={openWine} />
      )}
      {activeTab === "scan" && scanStage === "empty" && result && (
        <EmptyScreen candidates={result.candidates} onBack={() => setScanStage("idle")} onOpenWine={openWine} />
      )}
      {activeTab === "catalog" && <CatalogScreen onOpenWine={openWine} initialManufacturer={catalogManufacturer} />}
      {activeTab === "map" && <MapScreen onSelectWinery={openWinery} />}
      {activeTab === "profile" && <ProfileScreen onOpenWine={openWine} onSelectWinery={openWinery} />}

      <BottomTabs active={activeTab} onChange={changeTab} />
      <AchievementToast achievements={toastAchievements} onDone={() => setToastAchievements([])} />
    </div>
  );
}
