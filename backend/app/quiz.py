import hashlib
import random
from dataclasses import dataclass
from datetime import date
from typing import List, Optional

XP_PER_CORRECT = 4
QUIZ_SIZE = 5


@dataclass
class Question:
    id: str
    text: str
    options: List[str]
    correct_index: int


QUESTIONS: List[Question] = [
    Question("tannins", "Танины сильнее всего ощущаются в винах:", ["молодых красных", "игристых белых", "лёгких розовых", "десертных"], 0),
    Question("terroir", "Терруар - это:", ["сочетание почвы, климата и рельефа", "крепость вина в градусах", "название бочки", "сорт винограда"], 0),
    Question("white-temp", "При какой температуре обычно подают белое вино?", ["8–12°C", "25–30°C", "0°C", "18–20°C"], 0),
    Question("saperavi", "Саперави - сорт винограда родом из региона:", ["Кавказ", "Бордо", "Тоскана", "Риоха"], 0),
    Question("muscat", "Вино из муската чаще всего:", ["ароматное, часто полусладкое", "крепкое и без аромата", "только игристое брют", "только красное сухое"], 0),
    Question("decanting", "Декантация нужна, чтобы:", ["насытить вино кислородом и отделить осадок", "быстрее охладить вино", "снизить крепость", "подкрасить вино"], 0),
    Question("oak", "Выдержка в дубе обычно добавляет вину ноты:", ["ванили и специй", "только цитрусовой кислинки", "соли", "мяты"], 0),
    Question("acidity", "Кислотность вина особенно высокая у:", ["белых вин из прохладного климата", "крепких десертных вин", "вин с долгой выдержкой в дубе", "полусладких розовых"], 0),
    Question("cabernet", "Каберне Совиньон обычно даёт вино с:", ["плотным телом и высокими танинами", "лёгким телом без танинов", "только сладким вкусом", "почти без аромата"], 0),
    Question("crimea", "Виноделие в Крыму ведётся:", ["больше двух тысяч лет", "только с XX века", "с 1990-х годов", "с 2014 года"], 0),
    Question("rose", "Розовое вино получает свой цвет за счёт:", ["короткого контакта сока с кожицей красных сортов", "добавления красителя", "смешивания красного и белого вина", "выдержки в окрашенной бочке"], 0),
    Question("sparkling", "Пузырьки в игристом вине появляются благодаря:", ["вторичному брожению", "добавлению газа из баллона", "взбиванию", "заморозке"], 0),
    Question("body", '"Телом" вина (body) называют:', ["ощущение плотности и насыщенности во рту", "крепость в градусах", "цвет вина", "форму бутылки"], 0),
    Question("dagestan", "Дагестан как регион виноделия связан с традициями:", ["Кавказа и Персии", "Бордо", "Шампани", "Риохи"], 0),
    Question("serving-red", "Красное вино подают теплее белого, потому что так:", ["лучше раскрывается аромат и смягчаются танины", "вино дольше хранится", "быстрее выветривается алкоголь", "того требует этикет"], 0),
]


def _daily_seed(today: date) -> int:
    return int(hashlib.sha256(f"quiz:{today.isoformat()}".encode("utf-8")).hexdigest(), 16)


def today_quiz(today: Optional[date] = None) -> List[dict]:
    today = today or date.today()
    rng = random.Random(_daily_seed(today))
    picked = rng.sample(QUESTIONS, min(QUIZ_SIZE, len(QUESTIONS)))

    result = []
    for q in picked:
        order = list(range(len(q.options)))
        rng.shuffle(order)
        result.append({
            "id": q.id,
            "text": q.text,
            "options": [q.options[i] for i in order],
            "correct_index": order.index(q.correct_index),
        })
    return result


def check_answer(question_id: str, selected_index: int, today: Optional[date] = None) -> Optional[dict]:
    for q in today_quiz(today):
        if q["id"] == question_id:
            return {"correct": selected_index == q["correct_index"], "correct_index": q["correct_index"]}
    return None
