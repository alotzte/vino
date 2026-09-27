import type { Tab } from "../types";

interface Props {
  active: Tab;
  onChange: (tab: Tab) => void;
}

const ITEMS: { tab: Tab; label: string; icon: JSX.Element }[] = [
  {
    tab: "scan",
    label: "Скан",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
        <rect x="2.5" y="6" width="19" height="14" rx="3" />
        <circle cx="12" cy="13" r="4" />
      </svg>
    ),
  },
  {
    tab: "catalog",
    label: "Каталог",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3.5" y="4" width="17" height="4" rx="1" />
        <rect x="3.5" y="10" width="17" height="4" rx="1" />
        <rect x="3.5" y="16" width="17" height="4" rx="1" />
      </svg>
    ),
  },
  {
    tab: "map",
    label: "Карта",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
        <path d="M9 4 3 6.5v13.5L9 17l6 3.5 6-2.5V4.5L15 7 9 4Z" />
        <path d="M9 4v13" />
        <path d="M15 7v13.5" />
      </svg>
    ),
  },
  {
    tab: "profile",
    label: "Профиль",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="8" r="3.5" />
        <path d="M5 20c1.4-3.6 4.2-5.5 7-5.5s5.6 1.9 7 5.5" />
      </svg>
    ),
  },
];

export default function BottomTabs({ active, onChange }: Props) {
  return (
    <nav className="tabbar">
      {ITEMS.map((item) => (
        <button
          key={item.tab}
          className={`tabbar__item${active === item.tab ? " is-on" : ""}`}
          onClick={() => onChange(item.tab)}
        >
          {item.icon}
          <span>{item.label}</span>
        </button>
      ))}
    </nav>
  );
}
