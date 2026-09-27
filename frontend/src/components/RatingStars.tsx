import { useEffect, useState } from "react";
import { getRating, setRating as postRating } from "../api";

interface Props {
  slug: string;
}

function GlassIcon({ filled }: { filled: boolean }) {
  return (
    <svg
      viewBox="0 0 24 24"
      width="22"
      height="22"
      fill={filled ? "currentColor" : "none"}
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M8 3h8l-.7 6.2A3.4 3.4 0 0 1 12 12.3a3.4 3.4 0 0 1-3.3-3.1L8 3Z" />
      <path d="M12 12.3V19" />
      <path d="M8.5 21h7" />
    </svg>
  );
}

export default function RatingStars({ slug }: Props) {
  const [rating, setLocalRating] = useState(0);
  const [justPicked, setJustPicked] = useState<number | null>(null);

  useEffect(() => {
    setLocalRating(0);
    getRating(slug)
      .then((r) => setLocalRating(r.rating || 0))
      .catch(() => {});
  }, [slug]);

  async function pick(n: number) {
    setLocalRating(n);
    setJustPicked(n);
    setTimeout(() => setJustPicked(null), 320);
    await postRating(slug, n).catch(() => {});
  }

  return (
    <div className="rating__stars">
      {[1, 2, 3, 4, 5].map((n) => (
        <button
          key={n}
          className={`star${n <= rating ? " is-on" : ""}${justPicked === n ? " is-pop" : ""}`}
          onClick={() => pick(n)}
          aria-label={`${n} из 5`}
        >
          <GlassIcon filled={n <= rating} />
        </button>
      ))}
    </div>
  );
}
