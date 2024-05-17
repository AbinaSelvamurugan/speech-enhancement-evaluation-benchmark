"""PESQ binding wrapper. Unavailable dependency is always an explicit failure."""
import numpy as np
from speech_benchmark.audio.validation import pair


def compute_pesq(clean: np.ndarray, degraded: np.ndarray,
                 sample_rate: int, mode: str = "wb") -> float:
    if (sample_rate, mode) not in {(8000, "nb"), (16000, "nb"), (16000, "wb")}:
        raise ValueError("PESQ accepts nb at 8k/16k or wb at 16k; benchmark uses wb@16k, nb@8k")
    a, b = pair(clean, degraded, min_samples=int(sample_rate * 0.5))
    if np.max(np.abs(a)) < 1e-6:
        raise ValueError("PESQ cannot score a silent clean reference")
    try:
        from pesq import pesq, PesqError
    except ImportError as exc:
        raise RuntimeError("PESQ dependency unavailable; install pesq==0.0.4; score is missing") from exc
    result = float(pesq(sample_rate, a, b, mode, on_error=PesqError.RAISE_EXCEPTION))
    if not np.isfinite(result) or result < -0.5 or result > 4.65:
        raise ValueError(f"Invalid PESQ score returned by binding: {result}")
    return result
