"""Safe SoundFile loading and writing. Does not infer recording provenance."""
from pathlib import Path
import numpy as np
import soundfile as sf
from .validation import mono_float
from .resampling import resample


def load_audio(path: str | Path, sample_rate: int | None = None) -> tuple[np.ndarray, int]:
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Missing audio: {path}")
    try:
        audio, sr = sf.read(str(path), dtype="float64", always_2d=True)
    except (RuntimeError, ValueError) as exc:
        raise ValueError(f"Unreadable audio: {path}: {exc}") from exc
    audio = mono_float(audio)
    if sample_rate is not None:
        audio = resample(audio, sr, sample_rate)
        sr = sample_rate
    return audio, sr


def save_audio(path: str | Path, audio: np.ndarray, sr: int) -> None:
    path = Path(path)
    audio = mono_float(audio, allow_stereo=False)
    if sr <= 0:
        raise ValueError("Invalid sample rate")
    path.parent.mkdir(parents=True, exist_ok=True)
    # Float WAV avoids introducing quantization/clipping into scored waveforms.
    sf.write(path, audio, sr, subtype="FLOAT")
