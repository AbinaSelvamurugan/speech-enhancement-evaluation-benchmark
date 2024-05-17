"""Magnitude subtraction, spectral floor, noisy phase and COLA iSTFT."""
import numpy as np
from .base import STFTDenoiser, EnhancementContext
from speech_benchmark.audio.validation import mono_float


class SpectralSubtraction(STFTDenoiser):
    name = "spectral_subtraction"

    def __init__(self, subtraction_strength=1.15, spectral_floor=0.07, **kwargs):
        super().__init__(**kwargs)
        self.strength, self.floor = float(subtraction_strength), float(spectral_floor)
        if self.strength < 0 or not 0 <= self.floor <= 1:
            raise ValueError("Invalid subtraction parameters")

    def enhance(self, mixture, context: EnhancementContext):
        mixture = mono_float(mixture, False)
        spec = self._stft(mixture, context.sample_rate)
        mag = np.abs(spec)
        noise_mag = np.sqrt(self._noise_power(spec, context))
        estimate = np.maximum(mag - self.strength * noise_mag, self.floor * mag)
        gain = estimate / np.maximum(mag, 1e-15)
        return self._inverse(gain * spec, context.sample_rate, len(mixture))
