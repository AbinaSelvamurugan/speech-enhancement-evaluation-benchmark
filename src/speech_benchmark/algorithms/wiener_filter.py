"""Decision-directed-like local power estimate, Wiener MMSE gain."""
import numpy as np
from scipy.ndimage import gaussian_filter
from .base import STFTDenoiser, EnhancementContext
from speech_benchmark.audio.validation import mono_float


class WienerFilter(STFTDenoiser):
    name = "wiener"

    def __init__(self, min_gain=0.06, smoothing_frequency=1.5,
                 smoothing_time=2.0, **kwargs):
        super().__init__(**kwargs)
        self.min_gain = float(min_gain)
        self.freq_sigma = float(smoothing_frequency)
        self.time_sigma = float(smoothing_time)
        if not 0 <= self.min_gain <= 1 or min(self.freq_sigma, self.time_sigma) < 0:
            raise ValueError("Invalid Wiener settings")

    def enhance(self, mixture, context: EnhancementContext):
        mixture = mono_float(mixture, False)
        spec = self._stft(mixture, context.sample_rate)
        npsd = self._noise_power(spec, context)
        local_observed_psd = gaussian_filter(np.abs(spec)**2,
                    (self.freq_sigma, self.time_sigma), mode="nearest")
        speech_psd = np.maximum(local_observed_psd - npsd, 0)
        gain = speech_psd / np.maximum(speech_psd + npsd, 1e-15)
        gain = np.clip(gain, self.min_gain, 1.0)
        return self._inverse(gain * spec, context.sample_rate, len(mixture))
