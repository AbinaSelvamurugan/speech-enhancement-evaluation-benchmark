"""Smooth threshold mask; threshold in multiples of noise-amplitude RMS."""
import numpy as np
from scipy.ndimage import gaussian_filter
from .base import STFTDenoiser, EnhancementContext
from speech_benchmark.audio.validation import mono_float


class SpectralGating(STFTDenoiser):
    name = "spectral_gating"

    def __init__(self, threshold=1.5, reduction_strength=0.92, min_gain=0.07,
                 frequency_smoothing=1.5, time_smoothing=1.0, **kwargs):
        super().__init__(**kwargs)
        self.threshold = float(threshold)
        self.reduction = float(reduction_strength)
        self.min_gain = float(min_gain)
        self.freq_sigma = float(frequency_smoothing)
        self.time_sigma = float(time_smoothing)
        if self.threshold <= 0 or not 0 <= self.reduction <= 1 or not 0 <= self.min_gain <= 1:
            raise ValueError("Invalid gating settings")
        if self.freq_sigma < 0 or self.time_sigma < 0:
            raise ValueError("Smoothing must be nonnegative")

    def enhance(self, mixture, context: EnhancementContext):
        mixture = mono_float(mixture, False)
        spec = self._stft(mixture, context.sample_rate)
        noise_rms = np.sqrt(self._noise_power(spec, context))
        # A soft logistic mask avoids a discontinuous hard spectral gate.
        ratio = np.abs(spec) / np.maximum(self.threshold * noise_rms, 1e-15)
        mask = 1.0 / (1.0 + np.exp(-np.clip(6.0 * (ratio - 1.0), -60, 60)))
        if self.freq_sigma or self.time_sigma:
            mask = gaussian_filter(mask, (self.freq_sigma, self.time_sigma), mode="nearest")
        gain = np.clip(1 - self.reduction * (1 - mask), self.min_gain, 1.0)
        return self._inverse(gain * spec, context.sample_rate, len(mixture))
