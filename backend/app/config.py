import os
from pathlib import Path


class Settings:
    data_dir: Path = Path(os.getenv("VINO_DATA_DIR", "/srv/data/wines-svoe"))
    db_path: Path = Path(os.getenv("VINO_DB_PATH", "")) if os.getenv("VINO_DB_PATH") else data_dir / "wines.db"
    images_dir: Path = Path(os.getenv("VINO_IMAGES_DIR", "")) if os.getenv("VINO_IMAGES_DIR") else data_dir / "images"

    root_path: str = os.getenv("VINO_ROOT_PATH", "")

    app_db_path: Path = Path(os.getenv("VINO_APP_DB_PATH", "var/app.db"))

    scan_log_enabled: bool = os.getenv("VINO_SCAN_LOG", "1") == "1"
    scan_log_dir: Path = Path(os.getenv("VINO_SCAN_LOG_DIR", "var/scan-log"))

    engine: str = os.getenv("VINO_ENGINE", "stub")

    cv_url: str = os.getenv("VINO_CV_URL", "http://cv:8000").rstrip("/")
    # Меньше 10 с жёсткого таймаута скрипта оценки, с запасом на сеть и разбор ответа
    cv_timeout: float = float(os.getenv("VINO_CV_TIMEOUT", "8"))
    cv_fallback_stub: bool = os.getenv("VINO_CV_FALLBACK_STUB", "1") == "1"

    confidence_threshold: float = float(os.getenv("VINO_CONFIDENCE_THRESHOLD", "0.35"))

    top_k: int = int(os.getenv("VINO_TOP_K", "5"))

    llm_api_key: str = os.getenv("VINO_LLM_API_KEY", "")

    max_bot_token: str = os.getenv("VINO_MAX_BOT_TOKEN", "")
    max_bot_name: str = os.getenv("VINO_MAX_BOT_NAME", "")
    max_init_data_ttl: int = int(os.getenv("VINO_MAX_INIT_DATA_TTL", "86400"))


settings = Settings()
