"""Common denoiser interface and numerically stable STFT utilities."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
import numpy as np
from scipy.signal import stft, istft
from speech_benchmark.audio.validation import mono_float


@dataclass(frozen=True)
class EnhancementContext:
    sample_rate: int
    noise_reference: np.ndarray | None = None
    noise_profile: str = "oracle"


class Denoiser(ABC):
    name: str

    @abstractmethod
    def enhance(self, mixture: np.ndarray, context: EnhancementContext) -> np.ndarray:
        """Return a new, finite, zero-lag, equal-length waveform."""


class STFTDenoiser(Denoiser):
    def __init__(self, nperseg=512, hop=128):
        self.nperseg, self.hop = int(nperseg), int(hop)
        if self.nperseg < 32 or not 0 < self.hop <= self.nperseg:
            raise ValueError("Invalid STFT size/hop")

    def _stft(self, data, sample_rate):
        return stft(data, fs=sample_rate, window="hann", nperseg=self.nperseg,
                    noverlap=self.nperseg - self.hop, boundary="zeros", padded=True)[2]

    def _inverse(self, spectrum, sample_rate, length):
        _, audio = istft(spectrum, fs=sample_rate, window="hann", nperseg=self.nperseg,
                         noverlap=self.nperseg - self.hop, boundary=True)
        return mono_float(audio[:length] if len(audio) >= length else np.pad(
            audio, (0, length - len(audio))), False)

    def _noise_power(self, spectrum, context):
        """Oracle: independent noise only; blind: 20th percentile mixture power."""
        if context.noise_profile == "oracle":
            if context.noise_reference is None:
                raise ValueError("Oracle profile requires an independent noise reference")
            noise = mono_float(context.noise_reference, False)
            if np.mean(noise**2) <= 1e-12:
                raise ValueError("Near-silent noise reference")
            profile = np.mean(np.abs(self._stft(noise, context.sample_rate))**2,
                              axis=1, keepdims=True)
        elif context.noise_profile == "blind":
            profile = np.quantile(np.abs(spectrum)**2, 0.20, axis=1, keepdims=True)
        else:
            raise ValueError("Unknown noise-profile strategy")
        return np.maximum(profile, 1e-15)
