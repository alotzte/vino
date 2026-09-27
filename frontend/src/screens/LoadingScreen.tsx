import { useEffect, useState } from "react";

const STAGES = ["Нормализуем фотографию…", "Извлекаем признаки этикетки…", 'Ищем по каталогу "Своё Вино"…'];

export default function LoadingScreen({ errorMessage }: { errorMessage?: string | null }) {
  const [stage, setStage] = useState(0);

  useEffect(() => {
    if (errorMessage) return;
    const t = setInterval(() => setStage((i) => (i + 1) % STAGES.length), 700);
    return () => clearInterval(t);
  }, [errorMessage]);

  return (
    <section className="screen screen--loading is-active">
      <div className="loader">
        <div className="loader__bottle">
          <i></i>
        </div>
        <p className="loader__stage">{errorMessage || STAGES[stage]}</p>
        <div className="loader__bar">
          <span></span>
        </div>
      </div>
    </section>
  );
}
