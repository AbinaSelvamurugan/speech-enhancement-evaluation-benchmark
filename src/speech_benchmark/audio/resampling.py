"""Deterministic rational polyphase sample-rate conversion."""
from math import gcd
import numpy as np
from scipy.signal import resample_poly
from .validation import mono_float


def resample(data: np.ndarray, original_rate: int, target_rate: int) -> np.ndarray:
    if original_rate <= 0 or target_rate <= 0:
        raise ValueError("Sample rates must be positive")
    data = mono_float(data)
    if original_rate == target_rate:
        return data
    factor = gcd(original_rate, target_rate)
    converted = resample_poly(data, target_rate // factor, original_rate // factor)
    expected = int(round(len(data) * target_rate / original_rate))
    return converted[:expected] if len(converted) >= expected else np.pad(
        converted, (0, expected - len(converted))
    )
