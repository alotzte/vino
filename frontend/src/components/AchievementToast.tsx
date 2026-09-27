import { useEffect } from "react";
import type { Achievement } from "../types";

interface Props {
  achievements: Achievement[];
  onDone: () => void;
}

export default function AchievementToast({ achievements, onDone }: Props) {
  useEffect(() => {
    if (achievements.length === 0) return;
    const t = setTimeout(onDone, 3500);
    return () => clearTimeout(t);
  }, [achievements, onDone]);

  if (achievements.length === 0) return null;

  return (
    <div className="toast">
      <span className="toast__icon">{achievements[0].icon}</span>
      <span>Новая ачивка: {achievements.map((a) => a.title).join(", ")}</span>
    </div>
  );
}
