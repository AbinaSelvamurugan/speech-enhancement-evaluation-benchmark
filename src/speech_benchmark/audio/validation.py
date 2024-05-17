"""Uniform invariants for waveform inputs and DSP outputs."""
import numpy as np


def mono_float(data: np.ndarray, allow_stereo: bool = True) -> np.ndarray:
    arr = np.asarray(data, dtype=np.float64)
    if arr.ndim == 2 and allow_stereo and arr.shape[1] in (1, 2):
        arr = arr.mean(axis=1)  # documented arithmetic downmix
    if arr.ndim != 1 or arr.size == 0:
        raise ValueError("Expected non-empty mono waveform or 1/2-channel audio")
    if not np.all(np.isfinite(arr)):
        raise ValueError("Audio contains NaN or Inf")
    return np.array(arr, dtype=np.float64, copy=True)


def pair(clean: np.ndarray, other: np.ndarray, *, min_samples: int = 1):
    a, b = mono_float(clean, False), mono_float(other, False)
    if len(a) != len(b):
        raise ValueError(f"Unaligned lengths: clean {len(a)}, degraded {len(b)}")
    if len(a) < min_samples:
        raise ValueError(f"Signal too short: {len(a)} < {min_samples}")
    return a, b
