import { assetUrl } from "../api";
import type { Candidate } from "../types";

interface Props {
  candidate: Candidate;
  onSelect: (slug: string) => void;
}

export default function WineMini({ candidate, onSelect }: Props) {
  return (
    <div className="mini" onClick={() => onSelect(candidate.slug)}>
      <img src={candidate.image ? assetUrl(candidate.image) : ""} alt="" loading="lazy" />
      <span>{candidate.name}</span>
    </div>
  );
}
