"""Controlled SNR mixing, with a reproducible independent noise offset."""
import numpy as np
from .validation import mono_float


def power(a: np.ndarray) -> float:
    a = mono_float(a, False)
    return float(np.mean(a * a))


def select_noise(noise: np.ndarray, length: int, rng: np.random.Generator) -> np.ndarray:
    """Wrap noise if short; choose random contiguous offset if long."""
    noise = mono_float(noise, False)
    if length < 1:
        raise ValueError("length must be positive")
    if len(noise) >= length:
        start = int(rng.integers(0, len(noise) - length + 1))
        return np.array(noise[start:start + length], copy=True)
    start = int(rng.integers(0, len(noise)))
    return np.take(noise, (start + np.arange(length)) % len(noise))


def mix_at_snr(clean: np.ndarray, noise: np.ndarray, snr_db: float,
               floor: float = 1e-12) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    """Returns (matched clean, mixture, actual scaled noise, measured input SNR).

    Both clean and mixture are scaled together if peak > .95 to avoid exported clipping.
    """
    clean, noise = mono_float(clean, False), mono_float(noise, False)
    if len(clean) != len(noise):
        raise ValueError("Clean and noise must have identical length")
    ps, pv = power(clean), power(noise)
    if ps <= floor or pv <= floor:
        raise ValueError("Clean speech and noise must both have non-negligible power")
    if not np.isfinite(snr_db):
        raise ValueError("Target SNR must be finite")
    alpha = np.sqrt(ps / (pv * (10.0 ** (snr_db / 10.0))))
    scaled = noise * alpha
    mixture = clean + scaled
    peak = float(np.max(np.abs(mixture)))
    factor = min(1.0, 0.95 / peak) if peak > 0 else 1.0
    clean, scaled, mixture = clean * factor, scaled * factor, mixture * factor
    actual = 10 * np.log10(power(clean) / power(scaled))
    return clean, mixture, scaled, float(actual)
