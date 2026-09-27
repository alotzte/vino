from __future__ import annotations

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image

from .config import settings
from .crop import rgb_side


def inliers_ransac(p0: np.ndarray, p1: np.ndarray, thr: float = 6.0) -> int:
    if len(p0) < 8:
        return 0
    import pydegensac

    try:
        _, mask = pydegensac.findHomography(p0, p1, thr, 0.999, 2000, seed=settings.ransac_seed)
    except Exception:
        return 0
    return int(mask.sum()) if mask is not None else 0


class Verifier:
    def __init__(self, device: str, max_kp: int = 1024, side: int = 512):
        import kornia.feature as KF

        self.disk = KF.DISK.from_pretrained("depth").to(device).eval()
        self.lg = KF.LightGlue("disk").to(device).eval()
        self.device, self.max_kp, self.side = device, max_kp, side

    @torch.inference_mode()
    def extract(self, im: Image.Image) -> dict:
        g = np.asarray(rgb_side(im, self.side)).copy()
        x = torch.from_numpy(g).to(self.device).permute(2, 0, 1)[None].float() / 255
        h, w = x.shape[-2:]
        x = F.pad(x, (0, (-w) % 16, 0, (-h) % 16))
        f = self.disk(x, self.max_kp, pad_if_not_divisible=True)[0]
        # Точки из паддинга DISK выходят за image_size, и LightGlue падает на нормализации
        keep = (f.keypoints[:, 0] < w) & (f.keypoints[:, 1] < h)
        return {
            "kp": f.keypoints[keep].half().cpu(), "desc": f.descriptors[keep].half().cpu(),
            "size": torch.tensor([w, h], dtype=torch.float32),
        }

    @torch.inference_mode()
    def inliers(self, q: dict, r: dict) -> int:
        if len(q["kp"]) < 8 or len(r["kp"]) < 8:
            return 0
        data = {
            "image0": {"keypoints": q["kp"][None].float().to(self.device),
                       "descriptors": q["desc"][None].float().to(self.device),
                       "image_size": q["size"][None].to(self.device)},
            "image1": {"keypoints": r["kp"][None].float().to(self.device),
                       "descriptors": r["desc"][None].float().to(self.device),
                       "image_size": r["size"][None].to(self.device)},
        }
        m = self.lg(data)["matches"][0].cpu().numpy()
        if len(m) < 8:
            return 0
        return inliers_ransac(q["kp"].float().numpy()[m[:, 0]], r["kp"].float().numpy()[m[:, 1]])
