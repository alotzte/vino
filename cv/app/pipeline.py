# Отказ здесь не решается: порог применяет бэкенд, иначе flat=1 не сможет всегда отвечать
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field

import numpy as np
import torch
from PIL import Image

from . import crop as C
from . import local, lora
from .config import settings
from .index import Index


@dataclass
class Result:
    candidates: list[dict]
    crop_conf: float
    sat: float
    rotation: int
    stages_ms: dict[str, int] = field(default_factory=dict)


class Pipeline:
    def __init__(self):
        t0 = time.perf_counter()
        self.device = settings.device
        self.index = Index(settings.index_dir, self.device)
        self.cropper = C.BottleCropper(str(settings.yolo_weights), self.device)
        self.model, self.proc, self.lora_cfg = lora.load(settings.lora_ckpt, self.device)
        self.verifier = local.Verifier(self.device)
        self.lock = threading.Lock()
        self._warmup()
        self.load_s = round(time.perf_counter() - t0, 1)
        self.started = time.time()

    def _warmup(self):
        im = Image.new("RGB", (640, 960), (200, 180, 160))
        self._run_once(im)

    def _embed_search(self, im: Image.Image, top_k: int):
        vec = lora.embed(self.model, self.proc, [im], self.device)[0]
        return self.index.search(vec, top_k)

    def _run_once(self, im: Image.Image) -> tuple[np.ndarray, np.ndarray, Image.Image, float, float, dict]:
        ms = {}
        t = time.perf_counter()
        cropped, conf = self.cropper(im)
        ms["crop"] = int((time.perf_counter() - t) * 1000)

        t = time.perf_counter()
        sat = C.saturation(cropped)
        cos, idx = self._embed_search(cropped, settings.top_k)
        ms["embed_search"] = int((time.perf_counter() - t) * 1000)
        return cos, idx, cropped, conf, sat, ms

    def _verify(self, cropped: Image.Image, idx: np.ndarray) -> np.ndarray:
        qf = self.verifier.extract(cropped)
        return np.array([self.verifier.inliers(qf, self.index.feats(int(i))) for i in idx], np.float64)

    def run(self, raw: bytes) -> Result:
        with self.lock:
            return self._run(raw)

    def _run(self, raw: bytes) -> Result:
        t = time.perf_counter()
        im = C.decode(raw, settings.max_side)
        decode_ms = int((time.perf_counter() - t) * 1000)

        cos, idx, cropped, conf, sat, ms = self._run_once(im)
        rotation = 0

        if settings.rotation_probe and float(cos[0]) < settings.rotation_probe_below:
            best = (float(cos[0]), cos, idx, cropped, conf, sat, 0)
            for angle in (90, 180, 270):
                c2, i2, cr2, cf2, s2, _ = self._run_once(im.rotate(angle, expand=True))
                if float(c2[0]) > best[0]:
                    best = (float(c2[0]), c2, i2, cr2, cf2, s2, angle)
            _, cos, idx, cropped, conf, sat, rotation = best

        t = time.perf_counter()
        inl = self._verify(cropped, idx)
        ms["verify"] = int((time.perf_counter() - t) * 1000)
        ms["decode"] = decode_ms

        score = cos + settings.geo_w * np.minimum(inl, settings.geo_cap) / settings.geo_cap
        order = np.argsort(-score, kind="stable")

        candidates = [{
            "slug": self.index.slugs[int(idx[j])],
            "cos": round(float(cos[j]), 4),
            "inliers": int(inl[j]),
            "score": round(float(score[j]), 4),
        } for j in order]

        return Result(candidates=candidates, crop_conf=round(conf, 3), sat=round(sat, 3),
                      rotation=rotation, stages_ms=ms)

    def health(self) -> dict:
        gpu = int(torch.cuda.memory_allocated() / 2 ** 20) if torch.cuda.is_available() else 0
        return {
            "status": "ok",
            "device": self.device,
            "load_s": self.load_s,
            "since_start_s": int(time.time() - self.started),
            "gpu_mem_mb": gpu,
            "index": {"count": len(self.index), **self.index.meta},
        }
