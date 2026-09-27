# Своё Вино: сканер этикеток российских вин

Решение кейса РСХБ на хакатоне "Лидеры цифровой трансформации" 2026. Пользователь
фотографирует этикетку, сервис находит вино в каталоге "Своё Вино" и показывает
карточку, а дальше предлагает сомелье, ачивки, уроки и карту виноделен.

- Демо: https://app.nektarum.ru/vino/
- Swagger: https://app.nektarum.ru/vino/docs
- ТЗ: `RSHB_Svoe_Vino_TZ.md`, архитектура: `ARCHITECTURE.md`

## Результаты

Замер официальным скриптом организаторов (`participant_test.sh`), `VINO_ENGINE=remote`,
GPU NVIDIA RTX A6000.

| Набор | Результат |
|---|---|
| 3 контрольных фото организаторов | 3/3 непустых slug, 816-1080 мс |
| 267 наших фото с полки магазина | ни одного пустого ответа и ни одного дольше 10 с |
| из них 127 фото вин, которые есть в каталоге (разметили вручную) | top-1 0.874 (111/127) |
| задержка на 267 фото | p50 533 мс, p95 591 мс, max 651 мс |

Ответы воспроизводимы: сид RANSAC фиксирован, два полных прогона совпали 267/267.
Холодный старт CV около 4 с, VRAM 1.8 ГБ.

Поля `f1_top1` и `f1_top5` в ответе `/api/scan` считаются из скора (косинус top-1 и
средний по top-5). Это не F1 на валидации, реальная точность в таблице выше.

## Как это работает

```
фото -> api (FastAPI) -> cv (GPU)
                          ├─ нормализация: EXIF, HEIC, альфа, сторона ≤ 2048
                          ├─ кроп бутылки: YOLO11m-seg
                          ├─ эмбеддинг: SigLIP 2 so400m + LoRA-адаптер (1152-d)
                          ├─ поиск: косинус по 2009 эталонам, top-20
                          └─ переранжирование: DISK + LightGlue + degensac
      api <- top-k (slug, скор)
       ├─ порог "не найдено" (только для UI): карточка или похожие вина
       └─ flat=1: {"slug": "..."} для скрипта оценки, всегда лучший кандидат
```

Подробнее в `ARCHITECTURE.md`.

## Требования

- Docker и Docker Compose, NVIDIA GPU и NVIDIA Container Toolkit. Без GPU CV-контейнер
  не запустится, CPU-версии нет.
- Около 6 ГБ под веса и индекс (`cv-assets/`) и 4.3 ГБ под каталог (`data/`).
  В git их нет, см. раздел про данные.

## Запуск

```bash
cp .env.example .env              # локально: VINO_ROOT_PATH=
docker compose up -d --build      # api стартует после того, как cv станет healthy
curl http://127.0.0.1:109/api/health
```

В health должно быть `"engine": "remote"`, `"stub": false` и `"cv": {"status": "ok"}`.
`stub: true` значит, что CV не отвечает и сервис работает на заглушке.

Интерфейс открывается на http://127.0.0.1:8109/, Swagger на http://127.0.0.1:8109/docs.
Порт 109 Chrome и Edge не открывают (`ERR_UNSAFE_PORT`), поэтому для браузера проброшен
8109. `curl` и скрипт оценки ходят на 109.

### Без Docker (API и интерфейс, без CV)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
(cd frontend && npm install && npm run build)
VINO_ENGINE=stub VINO_DATA_DIR=./data/wines-svoe VINO_ROOT_PATH= \
  uvicorn app.main:app --app-dir backend --reload --port 8000
```

Фронтенд с горячей перезагрузкой (порт 5173, `/api` проксируется на `:8000`):

```bash
cd frontend && npm run dev
```

## Данные и веса

Каталог лежит в `data/wines-svoe/`: `wines.db` (2011 позиций) и `images/` (2009 эталонных
`.webp`). Собран из выгрузки организаторов и монтируется только на чтение.

Веса и индекс лежат в `cv-assets/` и монтируются в CV-контейнер как `/assets:ro`.
Контейнер работает без сети (`HF_HUB_OFFLINE=1`, `YOLO_OFFLINE=1`), так что всё должно
быть скачано заранее:

```
cv-assets/
├── models/
│   ├── hf/                  # HF_HOME: google/siglip2-so400m-patch14-384 (4.3 ГБ)
│   ├── torch-hub/           # TORCH_HOME: веса DISK (depth) и LightGlue (disk)
│   ├── lora_l12r8.pt        # наш LoRA-адаптер SigLIP 2, 5.7 МБ
│   └── yolo11m-seg.pt       # Ultralytics YOLO11m-seg
└── index/                   # собирается командой ниже
```

SigLIP 2, DISK/LightGlue и YOLO публичные, скачиваются с Hugging Face, kornia и
Ultralytics при первом запуске с сетью. `lora_l12r8.pt` мы дообучили сами, он
раздаётся отдельно.

Индекс эталонов собирается один раз и пересобирается при смене каталога или адаптера
(около 70 с на A6000). В рантайме том read-only, поэтому сборка идёт отдельным запуском:

```bash
docker compose run --rm --no-deps -v "$PWD/cv-assets:/assets" \
  cv python -m app.build_index --data /srv/data/wines-svoe
```

В `index/meta.json` записаны хеш `wines.db` и конфиг LoRA. Если индекс собран от
другого каталога, CV не стартует.

## Переменные окружения

Шаблон в `.env.example`. Значения по умолчанию взяты из `docker-compose.yml`, в скобках
дефолт в коде, если он другой.

### API (`backend/app/config.py`)

| Переменная | По умолчанию | Назначение |
|---|---|---|
| `VINO_ENGINE` | `remote` (код: `stub`) | `remote` ходит в CV-контейнер, `stub` работает без распознавания |
| `VINO_CV_URL` | `http://cv:8000` | Адрес CV-сервиса |
| `VINO_CV_TIMEOUT` | `8` | Таймаут запроса в CV, с. Скрипт оценки обрывает соединение на 10 с |
| `VINO_CV_FALLBACK_STUB` | `1` | Если CV недоступен, отвечать заглушкой, а не ошибкой |
| `VINO_CONFIDENCE_THRESHOLD` | `0.680` (код: `0.35`) | Ниже этого косинуса top-1 показывается "не найдено". В `flat=1` не применяется |
| `VINO_TOP_K` | `5` | Сколько кандидатов отдавать в ответе |
| `VINO_DATA_DIR` | `/srv/data/wines-svoe` | Папка с `wines.db` и `images/` |
| `VINO_DB_PATH` / `VINO_IMAGES_DIR` | внутри `VINO_DATA_DIR` | Явные пути, если они лежат отдельно |
| `VINO_APP_DB_PATH` | `/srv/app-state/app.db` (код: `var/app.db`) | БД профиля, истории и ачивок |
| `VINO_ROOT_PATH` | `/vino` (код: пусто) | Префикс за обратным прокси, нужен только для Swagger |
| `VINO_MAX_BOT_TOKEN` | пусто | Токен бота MAX для проверки подписи мини-приложения (`docs/MAX.md`) |
| `VINO_MAX_BOT_NAME` | пусто | Имя бота MAX для диплинков |
| `VINO_MAX_INIT_DATA_TTL` | `86400` | Срок жизни подписи MAX, с |
| `VINO_LLM_API_KEY` | пусто | Задел под LLM-сомелье, пока не используется |

### CV (`cv/app/config.py`)

| Переменная | По умолчанию | Назначение |
|---|---|---|
| `VINO_CV_ASSETS` | `/assets` | Папка с весами и индексом |
| `VINO_CV_DEVICE` | `cuda` | Устройство инференса |
| `VINO_CV_LORA` / `VINO_CV_YOLO` / `VINO_CV_INDEX` | внутри `VINO_CV_ASSETS` | Явные пути к адаптеру, YOLO и индексу |
| `VINO_CV_TOP_K` | `20` | Сколько кандидатов идёт на геометрическую проверку |
| `VINO_CV_GEO_W` / `VINO_CV_GEO_CAP` | `0.5` / `200` | `score = cos + W·min(inliers, CAP)/CAP` |
| `VINO_CV_RANSAC_SEED` | `20260920` | Сид degensac, чтобы ответы были воспроизводимы |
| `VINO_CV_SAT_GATE` | `0` | Отказ на чёрно-белых кадрах, 0 выключает |
| `VINO_CV_ROTATION_PROBE` | `0` | Проба поворотов 90/180/270° при низком косинусе |
| `VINO_CV_ROTATION_PROBE_BELOW` | `0.68` | Порог косинуса для пробы поворотов |
| `VINO_CV_MAX_SIDE` | `2048` | Длинная сторона после нормализации |
| `VINO_CV_MAX_BYTES` | `31457280` | Максимальный размер загрузки |
| `CUDA_VISIBLE_DEVICES` | `1` (в compose) | Какая видеокарта отдана CV |

## Прогон скрипта оценки

```bash
# сначала проверить, что "stub": false и cv.status == "ok"
curl -s http://127.0.0.1:109/api/health

# официальный скрипт, копия без изменений (нужен jq; падает, если --output уже существует)
cd data/mostech-share/eval && rm -f predictions.jsonl && ../../../scripts/participant_test.sh \
  --images-dir ./queries --manifest ./queries.tsv \
  --endpoint 'http://127.0.0.1:109/api/scan?flat=1' --output ./predictions.jsonl
```

## API

| Метод | Путь | Назначение |
|---|---|---|
| `GET` | `/api/health` | Статус, движок, размер каталога, состояние CV |
| `POST` | `/api/scan` | Фото (`multipart/form-data`, поле `image` или `file`), полный ответ |
| `POST` | `/api/scan?flat=1` | Формат скрипта оценки: `{"slug": "wine-slug"}` |
| `GET` | `/api/wines` | Каталог с поиском и фильтрами |
| `GET` | `/api/wines/{slug}` | Карточка вина |
| `GET` | `/api/wines/{slug}/scores` | Народная и экспертная оценки (демо) |
| `GET` | `/api/wines/{slug}/questions` | "Вопросы по теме" к карточке |
| `GET`/`POST` | `/api/wines/{slug}/rating` | Оценка вина 1-5 от текущего профиля |
| `GET` | `/api/image/{slug}` | Эталонное фото |
| `GET` | `/api/sommelier/questions` | Вопросы цифрового сомелье |
| `POST` | `/api/sommelier` | Рекомендация, гастропары, аналоги из других виноделен |
| `GET` | `/api/wineries` | Карта виноделен с отметками посещений |
| `POST` | `/api/wineries/checkin` | Чекин на винодельне |
| `GET` | `/api/learning`, `POST` `/api/learning/complete` | Урок дня и стрик |
| `GET` | `/api/quiz/today`, `POST` `/api/quiz/check`, `/api/quiz/submit` | Тест дня |
| `GET` | `/api/points` | Баллы за отзывы и чекины |
| `GET` | `/api/achievements` | Ачивки |
| `GET` | `/api/history` | История сканов |
| `GET` | `/api/me` | Сводка профиля |
| `POST` | `/api/menu-scan` | Скан винной карты ресторана (демо) |

Для эндпоинтов профиля нужен заголовок `X-Device-Id` (фронтенд создаёт его сам), а внутри
мини-приложения MAX - `X-Max-Init-Data`.

Пример ответа `/api/scan`:

```json
{
  "slug": "fanagoriya-dekanter-riesling-2020-...",
  "found": true,
  "confidence": 0.93,
  "f1_top1": 0.93,
  "f1_top5": 0.71,
  "elapsed_ms": 540,
  "engine": "remote",
  "wine": { "name": "...", "manufacturer": "...", "region": "...", "grapes": ["..."] },
  "candidates": [{ "slug": "...", "name": "...", "score": 0.93, "f1": 0.93 }],
  "new_achievements": []
}
```

## Структура

```
backend/app/
  main.py              точка входа, раздача собранного фронтенда
  config.py            настройки из переменных окружения
  schemas.py           схемы API
  api/routes.py        HTTP-слой
  api/sommelier.py     цифровой сомелье
  pipeline/
    search.py          выбор движка, порог, метрики
    remote.py          запросы в CV-контейнер и откат на заглушку
    normalize.py, embedder.py, index.py   путь engine=stub
  catalog.py           каталог (SQLite, только чтение)
  appdb.py, auth.py    БД профиля и определение пользователя
  achievements.py, lessons.py, quiz.py, points.py,
  regions.py, related_questions.py, menu_scan.py, demo_scores.py
cv/app/
  main.py              FastAPI CV-сервиса (наружу не публикуется)
  pipeline.py          каскад целиком
  crop.py              нормализация фото и кроп YOLO
  lora.py              SigLIP 2 + LoRA
  local.py             DISK + LightGlue + degensac
  index.py             индекс эталонов
  build_index.py       сборка индекса
frontend/src/          React + TypeScript + Vite
  screens/             экраны
  components/          переиспользуемые компоненты
  api.ts               сетевые запросы
  max.ts               интеграция с MAX
scripts/               deploy.sh, participant_test.sh (скрипт оценки организаторов)
docs/                  DEPLOY.md, MAX.md
```

## Ограничения

- Нужен GPU. Без него сервис запустится только с `VINO_ENGINE=stub`, без распознавания.
- Если CV не отвечает, `/api/scan` продолжает работать на заглушке (slug по хешу
  пикселей). Интерфейс при этом работает, но ответы случайные, и прогон оценки провалится.
  Видно в `/api/health`: `stub: true`, `status: degraded`, счётчик `cv_fallbacks`.
- Одна и та же этикетка разных годов визуально не различается, каскад выберет одну из них.
  Организаторы исключили такие вина из оценки.
- Этикетку, закрытую наполовину, каскад пока путает.
- Для вин вне каталога идеального порога нет: скоры своих и чужих вин на полке
  пересекаются. Поэтому экран "не найдено" всегда показывает похожие вина.
- Сомелье, "вопросы по теме" и скан меню работают на правилах, без LLM. Скан меню - демо.
- Народная и экспертная оценки в карточке - демо, считаются из хеша slug.
- Палитра и шрифты приближены к порталу "Своё Вино", но это не официальный гайдлайн.
