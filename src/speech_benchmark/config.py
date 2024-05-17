"""Validated configuration and path resolution."""
from dataclasses import dataclass
from pathlib import Path
import yaml


@dataclass(frozen=True)
class Settings:
    manifest: Path
    output_dir: Path
    sample_rate: int
    segment_seconds: float
    snrs_db: tuple[float, ...]
    seed: int
    max_recordings: int
    algorithms: tuple[str, ...]
    noise_profile: str
    save_audio: bool
    warmup: bool
    algorithm_options: dict
    metric_options: dict
    config_path: Path


def read_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"YAML root must be mapping: {path}")
    return value


def load_settings(path: str | Path) -> Settings:
    path = Path(path).resolve()
    config = read_yaml(path)
    base = path.parent
    alg = read_yaml(base / "algorithms.yaml")
    metrics = read_yaml(base / "metrics.yaml")
    sr = int(config["sample_rate"])
    if sr not in (8000, 16000):
        raise ValueError("PESQ benchmark requires 8000 or 16000 Hz")
    sec = float(config["segment_seconds"])
    if sec < 1:
        raise ValueError("segment_seconds must be at least 1 for meaningful STOI")
    snrs = tuple(float(x) for x in config["snrs_db"])
    if not snrs or not all(-40 <= x <= 60 for x in snrs):
        raise ValueError("Invalid/empty SNR list")
    profile = str(config.get("noise_profile", "oracle"))
    if profile not in {"oracle", "blind"}:
        raise ValueError("noise_profile must be oracle or blind")
    max_rec = int(config.get("max_recordings", 0))
    if max_rec < 0:
        raise ValueError("max_recordings must be >=0")
    for key in ("pesq_mode", "stoi_extended", "power_floor"):
        if key not in metrics:
            raise ValueError(f"Missing metric config: {key}")
    if metrics["pesq_mode"] != ("wb" if sr == 16000 else "nb"):
        raise ValueError("For comparability, PESQ must be wb@16k or nb@8k")
    return Settings(
        manifest=(base / config["manifest"]).resolve(),
        output_dir=(base / config["output_dir"]).resolve(),
        sample_rate=sr, segment_seconds=sec, snrs_db=snrs,
        seed=int(config["seed"]), max_recordings=max_rec,
        algorithms=tuple(config["algorithms"]), noise_profile=profile,
        save_audio=bool(config.get("save_audio", False)),
        warmup=bool(config.get("warmup", True)),
        algorithm_options=alg, metric_options=metrics, config_path=path,
    )
