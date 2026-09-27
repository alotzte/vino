import WineMini from "./WineMini";
import type { Candidate } from "../types";

interface Props {
  candidates: Candidate[];
  wrap?: boolean;
  emptyLabel?: string;
  onSelect: (slug: string) => void;
}

export default function WineRail({ candidates, wrap, emptyLabel, onSelect }: Props) {
  if (candidates.length === 0) {
    return emptyLabel ? <span className="chip">{emptyLabel}</span> : null;
  }
  return (
    <div className={`rail${wrap ? " rail--wrap" : ""}`}>
      {candidates.map((c) => (
        <WineMini key={c.slug} candidate={c} onSelect={onSelect} />
      ))}
    </div>
  );
}
