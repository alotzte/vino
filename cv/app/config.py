import os
from pathlib import Path


class Settings:
    assets: Path = Path(os.getenv("VINO_CV_ASSETS", "/assets"))
    device: str = os.getenv("VINO_CV_DEVICE", "cuda")

    lora_ckpt: Path = Path(os.getenv("VINO_CV_LORA", "")) if os.getenv("VINO_CV_LORA") else assets / "models/lora_l12r8.pt"
    yolo_weights: Path = Path(os.getenv("VINO_CV_YOLO", "")) if os.getenv("VINO_CV_YOLO") else assets / "models/yolo11m-seg.pt"
    index_dir: Path = Path(os.getenv("VINO_CV_INDEX", "")) if os.getenv("VINO_CV_INDEX") else assets / "index"

    top_k: int = int(os.getenv("VINO_CV_TOP_K", "20"))
    # score = cos + geo_w * min(inliers, geo_cap) / geo_cap
    geo_w: float = float(os.getenv("VINO_CV_GEO_W", "0.5"))
    geo_cap: float = float(os.getenv("VINO_CV_GEO_CAP", "200"))
    # Без фиксированного сида RANSAC один и тот же снимок даёт разные ответы
    ransac_seed: int = int(os.getenv("VINO_CV_RANSAC_SEED", "20260920"))

    # Ч/б-гейт выключен: на фото с витрины режет 9% кадров
    sat_gate: float = float(os.getenv("VINO_CV_SAT_GATE", "0"))
    # Проба поворотов на фото с витрины точность не поднимает, а p95 растёт
    rotation_probe: bool = os.getenv("VINO_CV_ROTATION_PROBE", "0") == "1"
    rotation_probe_below: float = float(os.getenv("VINO_CV_ROTATION_PROBE_BELOW", "0.68"))

    max_side: int = int(os.getenv("VINO_CV_MAX_SIDE", "2048"))
    max_bytes: int = int(os.getenv("VINO_CV_MAX_BYTES", str(30 * 2 ** 20)))


settings = Settings()
