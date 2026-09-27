# Деплой

Сервис крутится в Docker на домашнем сервере, наружу выходит через FRP-туннель и HAProxy.

| Что | Значение |
|---|---|
| Адрес | https://app.nektarum.ru/vino/ |
| Порт | 109 (8109 для локального браузера) |
| FRP-прокси | `vino`, 127.0.0.1:109 -> 109 |
| HAProxy backend | `vino`, срезает префикс `/vino` |

## Настройка

Docker:

```bash
cd ~/vino && docker compose up -d --build
curl http://127.0.0.1:109/api/health
```

FRP, в `/opt/frp/frpc.toml`:

```toml
[[proxies]]
name = "vino"
type = "tcp"
localIP = "127.0.0.1"
localPort = 109
remotePort = 109
```

```bash
sudo systemctl restart frpc
```

HAProxy, в `frontend https_in` (строка должна стоять выше `use_backend app_default`):

```
    acl is_vino path_beg /vino
    use_backend vino if is_app is_vino
```

и в конец файла:

```
backend vino
    http-request replace-path ^/vino$ /
    http-request replace-path ^/vino/(.*) /\1
    http-request set-header X-Forwarded-Proto https
    server vino1 127.0.0.1:109 check
```

```bash
sudo haproxy -c -f /etc/haproxy/haproxy.cfg && sudo systemctl reload haproxy
```

Приложение внутри живёт на `/`, поэтому `replace-path` обязателен. Отдельный сертификат
не нужен, поддиректория покрыта сертификатом `app.nektarum.ru`.

## CV-контейнер

В compose два сервиса: `api` (порты 109 и 8109) и `cv` с GPU, который наружу не
публикуется.

Веса и индекс монтируются томом `./cv-assets:/assets:ro` (4.6 ГБ), в образ они не
попадают:

```
cv-assets/
├── models/
│   ├── hf/hub/models--google--siglip2-so400m-patch14-384/   # 4.3 ГБ, HF_HOME
│   ├── torch-hub/hub/checkpoints/{depth-save.pth, disk_lightglue_v0-1_arxiv-pth}
│   ├── lora_l12r8.pt                                        # адаптер, 5.7 МБ
│   └── yolo11m-seg.pt                                       # 43 МБ
└── index/  ref_lora.npy, ref_disk512.npz, catalog.json, meta.json
```

Индекс пересобирается при смене каталога или адаптера LoRA (около 70 с на A6000).
Во время работы том read-only, поэтому сборка запускается отдельно:

```bash
docker compose run --rm --no-deps \
  -v "$PWD/cv-assets:/assets" \
  cv python -m app.build_index --data /srv/data/wines-svoe
```

В `meta.json` лежат хеш `wines.db` и конфиг LoRA, с чужим каталогом сервис не стартует.

- CV отдана вторая видеокарта (`CUDA_VISIBLE_DEVICES=1`), первую занимают другие процессы.
- Холодный старт - это чтение 4.3 ГБ весов, поэтому в healthcheck `start_period: 120s`.
  Поднимать сервис надо заранее, перезапуск во время приёмки недопустим.
- Если CV не поднялся, API отвечает заглушкой (`VINO_CV_FALLBACK_STUB=1`), чтобы каталог,
  профиль и карта продолжали работать. В `/api/health` это видно как `"stub": true` и
  `cv.status != "ok"`, `deploy.sh` это проверяет.

## Известные проблемы

- База каталога в режиме WAL не открывается из `:ro`-тома обычным `sqlite3.connect`,
  нужен `file:...?mode=ro&immutable=1`.
- С `root_path="/vino"` mount `/static` отдавал 404, поэтому статика отдаётся явным роутом
  в `main.py`.
- Диск на сервере уже забивался до 100% по inode (очередь postfix и логи). Перед правкой
  конфигов стоит проверить `df -h / && df -i /`.

## Обновление

```bash
cd ~/vino && ./scripts/deploy.sh
```

## Диагностика

```bash
# домашний сервер
docker compose ps && docker compose logs --tail 50
docker compose logs --tail 50 cv
curl -s http://127.0.0.1:109/api/health | python3 -m json.tool
sudo systemctl status frpc

# nektarum
ssh nektarum 'curl -I http://127.0.0.1:109/api/health'
ssh nektarum 'df -h / && df -i /'
ssh nektarum 'journalctl -u haproxy -n 30 --no-pager'
```
