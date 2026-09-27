interface Props {
  catalogLabel: string;
  onToggleMetrics: () => void;
}

export default function TopBar({ catalogLabel, onToggleMetrics }: Props) {
  return (
    <header className="topbar">
      <div className="brand">
        <span className="brand__mark" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <path d="M8 3h8l-.7 6.2A3.4 3.4 0 0 1 12 12.3a3.4 3.4 0 0 1-3.3-3.1L8 3Z" />
            <path d="M12 12.3V19" />
            <path d="M8.5 21h7" />
          </svg>
        </span>
        <span className="brand__text">
          <b>Своё&nbsp;Вино</b>
          <i>сканер этикеток</i>
        </span>
      </div>
      <button className="topbar__meta" title="Показать метрики" onClick={onToggleMetrics}>
        <span>{catalogLabel}</span>
      </button>
    </header>
  );
}
