"""STOI intelligibility estimate via pystoi; no resampling within metric wrapper."""
import numpy as np
from speech_benchmark.audio.validation import pair


def compute_stoi(clean: np.ndarray, degraded: np.ndarray,
                 sample_rate: int, extended=False) -> float:
    if sample_rate < 8000 or sample_rate > 48000:
        raise ValueError("STOI input sample rate outside supported benchmark range")
    a, b = pair(clean, degraded, min_samples=sample_rate)
    if np.mean(a**2) < 1e-12 or np.mean(b**2) < 1e-12:
        raise ValueError("STOI input contains near-silence")
    from pystoi import stoi
    value = float(stoi(a, b, sample_rate, extended=bool(extended)))
    if not np.isfinite(value) or not -1.001 <= value <= 1.001:
        raise ValueError(f"STOI returned invalid score {value}")
    return value
