from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image

MODEL_ID = "google/siglip2-so400m-patch14-384"
TARGETS = ("q_proj", "v_proj", "fc1", "fc2")


class LoRALinear(nn.Module):
    def __init__(self, base: nn.Linear, r: int = 8, alpha: int = 16):
        super().__init__()
        self.base = base
        for p in self.base.parameters():
            p.requires_grad_(False)
        self.r, self.scale = r, alpha / r
        self.A = nn.Linear(base.in_features, r, bias=False)
        self.B = nn.Linear(r, base.out_features, bias=False)
        nn.init.kaiming_uniform_(self.A.weight, a=math.sqrt(5))
        nn.init.zeros_(self.B.weight)

    def forward(self, x):
        return self.base(x) + self.scale * self.B(self.A(x))

    @torch.no_grad()
    def merge(self) -> nn.Linear:
        self.base.weight += self.scale * (self.B.weight @ self.A.weight)
        return self.base


def _blocks(model):
    for blk in model.vision_model.encoder.layers:
        yield blk


def inject(model, n_layers: int, r: int, alpha: int) -> int:
    layers = model.vision_model.encoder.layers
    touched = 0
    for li in range(len(layers) - n_layers, len(layers)):
        block = layers[li]
        for parent, name in ((block.self_attn, "q_proj"), (block.self_attn, "v_proj"),
                             (block.mlp, "fc1"), (block.mlp, "fc2")):
            if name not in TARGETS or not hasattr(parent, name):
                continue
            setattr(parent, name, LoRALinear(getattr(parent, name), r, alpha))
            touched += 1
    return touched


@torch.no_grad()
def merge_all(model) -> int:
    merged = 0
    for block in _blocks(model):
        for parent, name in ((block.self_attn, "q_proj"), (block.self_attn, "v_proj"),
                             (block.mlp, "fc1"), (block.mlp, "fc2")):
            mod = getattr(parent, name, None)
            if isinstance(mod, LoRALinear):
                setattr(parent, name, mod.merge())
                merged += 1
    return merged


def load(ckpt_path: Path, device: str):
    from transformers import AutoImageProcessor, AutoModel

    ckpt = torch.load(ckpt_path, map_location="cpu", weights_only=False)
    cfg = ckpt["cfg"]

    model = AutoModel.from_pretrained(MODEL_ID, dtype=torch.float32)
    proc = AutoImageProcessor.from_pretrained(MODEL_ID)
    for p in model.parameters():
        p.requires_grad_(False)
    inject(model, cfg["layers"], cfg["rank"], cfg["alpha"])
    # to(device) строго после inject: иначе матрицы A и B останутся на CPU
    model = model.to(device)

    result = model.load_state_dict(ckpt["lora"], strict=False)
    if result.unexpected_keys:
        raise RuntimeError(f"чужой чекпойнт LoRA: {result.unexpected_keys[:3]}")
    merge_all(model)
    if hasattr(model, "text_model"):
        del model.text_model
    model.eval()
    return model, proc, cfg


def pad_square(im: Image.Image, fill=(255, 255, 255)) -> Image.Image:
    # Без паддинга center-crop процессора срежет у бутылки низ и верх
    w, h = im.size
    s = max(w, h)
    canvas = Image.new("RGB", (s, s), fill)
    canvas.paste(im, ((s - w) // 2, (s - h) // 2))
    return canvas


@torch.inference_mode()
def embed(model, proc, images: list[Image.Image], device: str, bs: int = 16) -> np.ndarray:
    out = []
    for i in range(0, len(images), bs):
        x = proc(images=[pad_square(im) for im in images[i:i + bs]], return_tensors="pt")["pixel_values"]
        with torch.autocast("cuda", dtype=torch.bfloat16, enabled=device.startswith("cuda")):
            v = model.get_image_features(pixel_values=x.to(device))
        if not torch.is_tensor(v):
            v = v.pooler_output
        out.append(F.normalize(v.float(), dim=-1).cpu().numpy())
    return np.concatenate(out)
