from typing import List, Tuple

from .. import catalog

Hit = Tuple[str, float]  # (slug, score 0..1)


class StubIndex:

    name = "stub"

    def __init__(self) -> None:
        self._slugs: List[str] = []

    @property
    def slugs(self) -> List[str]:
        if not self._slugs:
            self._slugs = catalog.all_slugs()
        return self._slugs

    def size(self) -> int:
        return len(self.slugs)

    def query(self, vector: List[float], top_k: int = 5) -> List[Hit]:
        slugs = self.slugs
        if not slugs:
            return []

        seed = int(sum(v * 1000 for v in vector))
        hits: List[Hit] = []
        base = 0.93
        for i in range(min(top_k, len(slugs))):
            slug = slugs[(seed + i * 7919) % len(slugs)]
            hits.append((slug, round(base - i * 0.17, 4)))
        return hits


_index: StubIndex | None = None


def get_index(engine: str) -> StubIndex:
    global _index
    if engine == "siglip":
        raise NotImplementedError("Векторный индекс SigLIP ещё не собран, см. ARCHITECTURE.md")
    if _index is None:
        _index = StubIndex()
    return _index
