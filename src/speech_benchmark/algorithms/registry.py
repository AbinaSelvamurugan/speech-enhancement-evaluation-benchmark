"""Extensible algorithm factory."""
from .base import Denoiser, EnhancementContext
from .spectral_subtraction import SpectralSubtraction
from .spectral_gating import SpectralGating
from .wiener_filter import WienerFilter
from speech_benchmark.audio.validation import mono_float


class Noisy(Denoiser):
    name = "noisy"

    def enhance(self, mixture, context: EnhancementContext):
        return mono_float(mixture, False)


REGISTRY: dict[str, type[Denoiser]] = {
    "noisy": Noisy,
    "spectral_subtraction": SpectralSubtraction,
    "spectral_gating": SpectralGating,
    "wiener": WienerFilter,
}


def create(name: str, options: dict | None = None) -> Denoiser:
    if name == "neural":
        raise RuntimeError("Neural denoiser unavailable: no approved model/checkpoint installed")
    if name not in REGISTRY:
        raise ValueError(f"Unknown algorithm {name!r}; available: {list(REGISTRY)}")
    return REGISTRY[name](**((options or {}).get(name, {})))
