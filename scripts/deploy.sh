#!/usr/bin/env bash
# Пересборка и перезапуск сервиса на home-pc (порт 109 -> FRP -> HAProxy).
# CV читает 4.3 ГБ весов, поэтому ждём health, а не спим фиксированно.
set -euo pipefail
cd "$(dirname "$0")/.."

docker compose up -d --build

printf 'жду api'
for _ in $(seq 1 120); do
  if curl -fsS -o /dev/null http://127.0.0.1:109/api/health; then echo " готов"; break; fi
  printf '.'
  sleep 2
done

docker compose ps
echo "--- локальная проверка:"
curl -fsS http://127.0.0.1:109/api/health && echo

# engine=remote без живого cv - это молчаливый откат на заглушку
if curl -fsS http://127.0.0.1:109/api/health | grep -q '"stub": *true'; then
  echo "ВНИМАНИЕ: сервис отвечает заглушкой, распознавания нет"
  docker compose logs --tail 40 cv
fi

echo "--- публично: https://app.nektarum.ru/vino/"
