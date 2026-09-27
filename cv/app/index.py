from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import torch


class Index:
    def __init__(self, path: Path, device: str):
        meta = json.loads((path / "meta.json").read_text(encoding="utf-8"))
        self.meta = meta
        self.slugs: list[str] = json.loads((path / "catalog.json").read_text(encoding="utf-8"))["slugs"]

        emb = np.load(path / "ref_lora.npy")
        if emb.shape[0] != len(self.slugs):
            raise RuntimeError(f"индекс рассыпан: {emb.shape[0]} эмбеддингов на {len(self.slugs)} слагов")
        self.emb = torch.from_numpy(emb).to(device)

        z = np.load(path / "ref_disk512.npz")
        self.kp, self.desc, self.size, self.off = z["kp"], z["desc"], z["size"], z["offsets"]
        if len(self.off) - 1 != len(self.slugs):
            raise RuntimeError("ref_disk512.npz не от этого каталога")

    def __len__(self) -> int:
        return len(self.slugs)

    def feats(self, i: int) -> dict:
        a, b = self.off[i], self.off[i + 1]
        return {"kp": torch.from_numpy(self.kp[a:b]), "desc": torch.from_numpy(self.desc[a:b]),
                "size": torch.from_numpy(self.size[i])}

    def search(self, vector: np.ndarray, top_k: int) -> tuple[np.ndarray, np.ndarray]:
        q = torch.from_numpy(vector).to(self.emb.device)
        cos, idx = torch.topk(q @ self.emb.T, min(top_k, len(self)))
        return cos.float().cpu().numpy(), idx.cpu().numpy()
