import { useState } from "react";

interface Props {
  onConfirm: () => void;
}

export default function AgeGate({ onConfirm }: Props) {
  const [denied, setDenied] = useState(false);

  if (denied) {
    return (
      <div className="age-gate">
        <div className="age-gate__card">
          <span className="age-gate__icon">🔞</span>
          <h1>Доступ ограничен</h1>
          <p>Сервис содержит информацию об алкогольной продукции и доступен только совершеннолетним пользователям.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="age-gate">
      <div className="age-gate__card">
        <span className="age-gate__icon">🍷</span>
        <h1>Вам есть 18 лет?</h1>
        <p>Сервис содержит информацию об алкогольной продукции. Подтвердите возраст, чтобы продолжить.</p>
        <div className="age-gate__actions">
          <button className="btn btn--primary" onClick={onConfirm}>
            Да, мне есть 18
          </button>
          <button className="btn btn--ghost" onClick={() => setDenied(true)}>
            Мне нет 18
          </button>
        </div>
      </div>
    </div>
  );
}
