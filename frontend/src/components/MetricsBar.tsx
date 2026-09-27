interface Metrics {
  f1: number;
  f5: number;
  ms: number;
  engine: string;
}

interface Props {
  hidden: boolean;
  metrics: Metrics | null;
}

export default function MetricsBar({ hidden, metrics }: Props) {
  if (hidden) return null;
  return (
    <div className="metrics">
      <span>
        F1 top-1 <b>{metrics ? metrics.f1.toFixed(3) : "-"}</b>
      </span>
      <span>
        F1 top-5 <b>{metrics ? metrics.f5.toFixed(3) : "-"}</b>
      </span>
      <span>
        ответ <b>{metrics ? metrics.ms + " мс" : "-"}</b>
      </span>
      <span>
        движок <b>{metrics?.engine ?? "-"}</b>
      </span>
    </div>
  );
}
