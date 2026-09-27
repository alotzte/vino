import hashlib
from typing import List, Protocol

from .normalize import NormalizedImage

EMBEDDING_DIM = 768


class Embedder(Protocol):
    dim: int

    def embed(self, image: NormalizedImage) -> List[float]:
        ...


class StubEmbedder:

    dim = EMBEDDING_DIM
    name = "stub"

    def embed(self, image: NormalizedImage) -> List[float]:
        digest = hashlib.sha256(image.image.tobytes()).digest()
        return [b / 255.0 for b in digest]


def get_embedder(engine: str) -> Embedder:
    if engine == "siglip":
        # from .siglip import SiglipEmbedder
        # return SiglipEmbedder()
        raise NotImplementedError("SigLIP-эмбеддер ещё не подключён, см. ARCHITECTURE.md")
    return StubEmbedder()
