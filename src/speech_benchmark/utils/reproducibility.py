"""Deterministic per-case RNG and file SHA256."""
import hashlib
from pathlib import Path
import numpy as np


def stable_seed(seed: int, *parts: str) -> int:
    digest = hashlib.sha256((str(seed) + "|" + "|".join(parts)).encode()).digest()
    return int.from_bytes(digest[:8], "little")


def rng_for(seed: int, *parts: str) -> np.random.Generator:
    return np.random.default_rng(stable_seed(seed, *parts))


def sha256(path: Path) -> str:
    hash_ = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hash_.update(chunk)
    return hash_.hexdigest()
