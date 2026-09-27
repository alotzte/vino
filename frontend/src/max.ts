// Вне MAX Bridge тоже грузится, но с пустой initData - по ней и отличаем мессенджер

interface MaxBackButton {
  show(): void;
  hide(): void;
  onClick(cb: () => void): void;
  offClick(cb: () => void): void;
}

interface MaxWebApp {
  initData: string;
  initDataUnsafe: {
    start_param?: string;
    user?: { id: number; first_name?: string; last_name?: string; username?: string };
  };
  platform: "ios" | "android" | "desktop" | "web";
  ready?(): void;
  BackButton?: MaxBackButton;
  HapticFeedback?: {
    impactOccurred(style: "light" | "medium" | "heavy" | "rigid" | "soft"): void;
    notificationOccurred(type: "success" | "warning" | "error"): void;
  };
  openLink?(url: string): void;
  shareMaxContent?(params: { text?: string; link?: string }): Promise<unknown>;
}

declare global {
  interface Window {
    WebApp?: MaxWebApp;
  }
}

const webApp: MaxWebApp | undefined = window.WebApp?.initData ? window.WebApp : undefined;

export const inMax = !!webApp;

export const maxInitData = webApp?.initData ?? "";

export function maxReady() {
  webApp?.ready?.();
}

export type StartTarget = { kind: "wine"; slug: string } | { kind: "tab"; tab: "catalog" | "map" | "profile" } | null;

export function parseStartParam(): StartTarget {
  const raw = webApp?.initDataUnsafe.start_param ?? new URLSearchParams(location.search).get("startapp") ?? "";
  if (raw.startsWith("w_") && raw.length > 2) return { kind: "wine", slug: raw.slice(2) };
  if (raw === "catalog" || raw === "map" || raw === "profile") return { kind: "tab", tab: raw };
  return null;
}

export function wineDeepLink(botName: string, slug: string): string {
  return `https://max.ru/${botName}?startapp=w_${slug}`;
}

export function setBackButton(handler: (() => void) | null): () => void {
  const bb = webApp?.BackButton;
  if (!bb) return () => {};
  if (!handler) {
    bb.hide();
    return () => {};
  }
  bb.onClick(handler);
  bb.show();
  return () => bb.offClick(handler);
}

export function haptic(type: "success" | "warning" | "error" | "tap") {
  const h = webApp?.HapticFeedback;
  if (!h) return;
  try {
    if (type === "tap") h.impactOccurred("light");
    else h.notificationOccurred(type);
  } catch {}
}

// В webview MAX target=_blank может не сработать; true - ссылку открыл клиент
export function openExternal(url: string): boolean {
  if (!webApp?.openLink) return false;
  webApp.openLink(url);
  return true;
}

export async function shareWine(text: string, link: string): Promise<"max" | "native" | "copied" | "failed"> {
  try {
    if (webApp?.shareMaxContent) {
      await webApp.shareMaxContent({ text, link });
      return "max";
    }
    if (navigator.share) {
      await navigator.share({ text, url: link });
      return "native";
    }
    await navigator.clipboard.writeText(`${text}\n${link}`);
    return "copied";
  } catch {
    return "failed";
  }
}
