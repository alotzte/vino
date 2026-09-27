import { useRef } from "react";
import LessonWidget from "../components/LessonWidget";
import MenuScanFlow from "../components/MenuScanFlow";
import QuizWidget from "../components/QuizWidget";

interface Props {
  previewUrl: string | null;
  onFile: (file: File) => void;
  onOpenWine: (slug: string) => void;
}

export default function ScanScreen({ previewUrl, onFile, onOpenWine }: Props) {
  const cameraRef = useRef<HTMLInputElement>(null);
  const galleryRef = useRef<HTMLInputElement>(null);

  function pick(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) onFile(file);
    e.target.value = "";
  }

  return (
    <section className="screen screen--scan is-active">
      <div className="lesson-row">
        <LessonWidget />
        <QuizWidget />
      </div>

      <div className="viewfinder">
        <div className="viewfinder__frame">
          <svg className="viewfinder__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.3">
            <rect x="2.5" y="6" width="19" height="14" rx="3" />
            <circle cx="12" cy="13" r="4" />
            <path d="M8.5 6l1.3-2.2h4.4L15.5 6" />
          </svg>
          <p>
            Наведите камеру
            <br />
            на этикетку бутылки
          </p>
        </div>
        {previewUrl && <img className="viewfinder__preview" src={previewUrl} alt="" />}
      </div>

      <div className="actions">
        <label className="btn btn--primary">
          Сфотографировать
          <input ref={cameraRef} type="file" accept="image/*" capture="environment" hidden onChange={pick} />
        </label>
        <label className="btn btn--ghost">
          Загрузить из галереи
          <input ref={galleryRef} type="file" accept="image/*" hidden onChange={pick} />
        </label>
        <MenuScanFlow onOpenWine={onOpenWine} />
      </div>

      <ol className="steps">
        <li>
          <b>1</b> Снимите этикетку целиком
        </li>
        <li>
          <b>2</b> Сервис сверит фото с каталогом "Своё Вино"
        </li>
        <li>
          <b>3</b> Откроется карточка вина и цифровой сомелье
        </li>
      </ol>
    </section>
  );
}
