# python -m app.build_index --data /srv/data/wines-svoe --out /assets/index
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import time
from pathlib import Path

import numpy as np

from . import local, lora
from .config import settings
from .crop import load_reference


def catalog(data_dir: Path) -> list[tuple[str, str, str, Path]]:
    conn = sqlite3.connect(f"file:{data_dir / 'wines.db'}?mode=ro&immutable=1", uri=True)
    rows = []
    for slug, name, man in conn.execute("SELECT slug, name, manufacturer FROM wines ORDER BY slug"):
        path = data_dir / "images" / f"{slug}.webp"
        if path.exists():
            rows.append((slug, name or "", man or "", path))
    conn.close()
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, default=Path("/srv/data/wines-svoe"))
    ap.add_argument("--out", type=Path, default=settings.index_dir)
    ap.add_argument("--device", default=settings.device)
    args = ap.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    rows = catalog(args.data)
    print(f"эталонов: {len(rows)}", flush=True)

    model, proc, cfg = lora.load(settings.lora_ckpt, args.device)
    t0 = time.time()
    emb = []
    for i in range(0, len(rows), 16):
        imgs = [load_reference(p) for *_, p in rows[i:i + 16]]
        emb.append(lora.embed(model, proc, imgs, args.device))
        if i % 500 == 0:
            print(f"  эмбеддинги {i}/{len(rows)} за {time.time() - t0:.0f} с", flush=True)
    emb = np.concatenate(emb).astype(np.float32)
    np.save(args.out / "ref_lora.npy", emb)
    print(f"ref_lora.npy {emb.shape} за {time.time() - t0:.0f} с", flush=True)

    del model
    import torch

    torch.cuda.empty_cache()

    ver = local.Verifier(args.device)
    t0 = time.time()
    kps, descs, sizes, offsets = [], [], [], [0]
    for i, (*_, path) in enumerate(rows):
        f = ver.extract(load_reference(path))
        kps.append(f["kp"].numpy().astype(np.float16))
        descs.append(f["desc"].numpy().astype(np.float16))
        sizes.append(f["size"].numpy())
        offsets.append(offsets[-1] + len(f["kp"]))
        if i % 500 == 0:
            print(f"  DISK {i}/{len(rows)} за {time.time() - t0:.0f} с", flush=True)
    np.savez(args.out / "ref_disk512.npz", kp=np.concatenate(kps), desc=np.concatenate(descs),
             size=np.stack(sizes), offsets=np.array(offsets))
    print(f"ref_disk512.npz за {time.time() - t0:.0f} с", flush=True)

    (args.out / "catalog.json").write_text(json.dumps({
        "slugs": [r[0] for r in rows],
        "items": [{"slug": s, "name": n, "manufacturer": m} for s, n, m, _ in rows],
    }, ensure_ascii=False), encoding="utf-8")

    db_sha = hashlib.sha256((args.data / "wines.db").read_bytes()).hexdigest()[:16]
    (args.out / "meta.json").write_text(json.dumps({
        "lora_tag": settings.lora_ckpt.stem,
        "lora_cfg": {k: cfg[k] for k in ("layers", "rank", "alpha") if k in cfg},
        "dim": int(emb.shape[1]),
        "wines_db_sha256": db_sha,
        "built_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }, ensure_ascii=False), encoding="utf-8")
    print("готово:", sorted(p.name for p in args.out.iterdir()))


if __name__ == "__main__":
    main()
