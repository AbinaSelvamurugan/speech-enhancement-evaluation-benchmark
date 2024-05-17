"""Reconstruction SNR (noise + speech distortion), not isolated residual-noise SNR."""
import numpy as np
from speech_benchmark.audio.validation import pair


def reconstruction_snr(clean: np.ndarray, estimate: np.ndarray, floor=1e-12) -> float:
    clean, estimate = pair(clean, estimate)
    if floor <= 0 or not np.isfinite(floor):
        raise ValueError("Invalid numerical floor")
    speech_energy = float(np.sum(clean**2))
    residual_energy = float(np.sum((clean - estimate)**2))
    if speech_energy / len(clean) <= floor:
        raise ValueError("Near-silent clean reference")
    # Floor applies to mean-square error; cap perfect reconstruction at finite SNR.
    return float(10 * np.log10((speech_energy / len(clean)) /
                               max(residual_energy / len(clean), floor)))


def snr_improvement(clean, mixture, enhanced, floor=1e-12) -> float:
    return reconstruction_snr(clean, enhanced, floor) - reconstruction_snr(
        clean, mixture, floor)
