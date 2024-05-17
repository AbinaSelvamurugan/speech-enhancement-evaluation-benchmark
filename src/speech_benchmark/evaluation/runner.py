"""Fair case-level evaluation with per-metric failure isolation."""
from __future__ import annotations
import json
import platform
import time
from dataclasses import asdict
from pathlib import Path
import numpy as np
import pandas as pd
import scipy
from speech_benchmark import __version__
from speech_benchmark.config import Settings
from speech_benchmark.audio.loader import load_audio, save_audio
from speech_benchmark.audio.mixing import select_noise, mix_at_snr
from speech_benchmark.audio.alignment import align_known_zero_delay
from speech_benchmark.algorithms.base import EnhancementContext
from speech_benchmark.algorithms.registry import create
from speech_benchmark.metrics.pesq_metric import compute_pesq
from speech_benchmark.metrics.stoi_metric import compute_stoi
from speech_benchmark.metrics.snr_metric import reconstruction_snr
from speech_benchmark.metrics.aggregation import summarize
from speech_benchmark.evaluation.experiments import read_manifest, manifest_kind
from speech_benchmark.utils.reproducibility import rng_for, sha256

RESULT_COLUMNS = ["case_id", "recording_id", "noise_category", "target_snr_db", "algorithm",
                  "pesq_mode", "stoi_mode", "input_snr_db", "reconstruction_snr_db",
                  "noisy_reconstruction_snr_db", "snr_improvement_db", "pesq", "stoi",
                  "processing_ms", "rtf", "status", "errors", "output_file"]


def _measure(metric, *args, **kwargs) -> tuple[float, str | None]:
    try:
        value = metric(*args, **kwargs)
        if not np.isfinite(value):
            raise ValueError("Metric produced non-finite value")
        return float(value), None
    except Exception as exc:  # failure isolation is deliberate
        return float("nan"), f"{type(exc).__name__}: {exc}"


def evaluate_case(clean, mixture, scaled_noise, sr, record_id, category, target_snr,
                  algorithms, options, metrics, profile, save_dir=None, warmup=True):
    """Independent outputs, common exact samples, oracle profile from scaled independent noise.

    Only `.enhance()` is timed. Metric setup, loading, STFT warmup, and saving are excluded.
    """
    actual_snr = reconstruction_snr(clean, mixture, metrics["power_floor"])
    case_id = f"{record_id}__{category}__{target_snr:g}dB"
    results = []
    for name in algorithms:
        row = dict.fromkeys(RESULT_COLUMNS)
        row.update(case_id=case_id, recording_id=record_id, noise_category=category,
                   target_snr_db=target_snr, algorithm=name, input_snr_db=actual_snr,
                   noisy_reconstruction_snr_db=actual_snr,
                   pesq_mode=metrics["pesq_mode"],
                   stoi_mode="estoi" if metrics["stoi_extended"] else "stoi",
                   errors="{}", status="ok")
        errors = {}
        try:
            alg = create(name, options)
            ctx = EnhancementContext(sr, scaled_noise.copy() if profile == "oracle" else None,
                                     profile)
            if warmup:
                # Warm up each implementation on unrelated *synthetic* input, not test utterance.
                # The real call is timed only after the same implementation path is exercised.
                t = np.arange(sr, dtype=float) / sr
                dummy = (0.1 * np.sin(2 * np.pi * 440 * t)).astype(float)
                dummy_ctx = EnhancementContext(sr, dummy.copy(), profile)
                alg.enhance(dummy, dummy_ctx)
            t0 = time.perf_counter_ns()
            enhanced = alg.enhance(mixture.copy(), ctx)
            elapsed_ms = (time.perf_counter_ns() - t0) / 1e6
            clean_ref, enhanced = align_known_zero_delay(clean, enhanced)
            if np.max(np.abs(enhanced)) > 100:
                raise ValueError("Output has explosive amplitude")
            row["processing_ms"] = elapsed_ms
            row["rtf"] = elapsed_ms / 1000 / (len(mixture) / sr)
            row["reconstruction_snr_db"] = reconstruction_snr(
                clean_ref, enhanced, metrics["power_floor"])
            row["snr_improvement_db"] = row["reconstruction_snr_db"] - actual_snr
            row["pesq"], err = _measure(compute_pesq, clean_ref, enhanced, sr,
                                          metrics["pesq_mode"])
            if err:
                errors["pesq"] = err
            row["stoi"], err = _measure(compute_stoi, clean_ref, enhanced, sr,
                                          metrics["stoi_extended"])
            if err:
                errors["stoi"] = err
            if save_dir is not None:
                path = Path(save_dir) / case_id / f"{name}.wav"
                save_audio(path, enhanced, sr)
                row["output_file"] = str(path)
            if errors:
                row["status"] = "metric_partial"
        except Exception as exc:
            row["status"] = "algorithm_failed"
            errors["algorithm"] = f"{type(exc).__name__}: {exc}"
        row["errors"] = json.dumps(errors, sort_keys=True)
        results.append(row)
    return results


def run_benchmark(settings: Settings, *, snrs=None, categories=None, algorithms=None,
                  max_recordings=None) -> pd.DataFrame:
    examples = read_manifest(settings.manifest)
    if categories:
        examples = [e for e in examples if e.noise_category in categories]
    cap = settings.max_recordings if max_recordings is None else int(max_recordings)
    if cap > 0:
        examples = examples[:cap]
    if not examples:
        raise ValueError("No examples after filtering: no success artifacts written")
    snrs = tuple(settings.snrs_db if snrs is None else snrs)
    algorithms = tuple(settings.algorithms if algorithms is None else algorithms)
    if not algorithms or not snrs:
        raise ValueError("Nonempty algorithms and SNRs required")
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    files = []
    for index, ex in enumerate(examples, 1):
        print(f"[{index}/{len(examples)}] {ex.recording_id} / {ex.noise_category}", flush=True)
        clean, _ = load_audio(ex.clean, settings.sample_rate)
        noise, _ = load_audio(ex.noise, settings.sample_rate)
        count = min(len(clean), int(round(settings.segment_seconds * settings.sample_rate)))
        if count < settings.sample_rate:
            raise ValueError(f"{ex.recording_id}: too short (<1 second)")
        # Fixed prefix of clean speech; noise offset is independent of algorithm and SNR.
        clean = clean[:count]
        noise_segment = select_noise(noise, count, rng_for(settings.seed, ex.recording_id))
        files.append({"recording_id": ex.recording_id, "clean": str(ex.clean),
                      "noise": str(ex.noise), "clean_sha256": sha256(ex.clean),
                      "noise_sha256": sha256(ex.noise), "clean_license": ex.clean_license,
                      "noise_license": ex.noise_license, "clean_source": ex.clean_source,
                      "noise_source": ex.noise_source})
        for snr in snrs:
            clean_scaled, mixture, scaled_noise, measured = mix_at_snr(
                clean, noise_segment, float(snr), settings.metric_options["power_floor"])
            if abs(measured - float(snr)) > 1e-7:
                raise RuntimeError("SNR calibration failed")
            audio_dir = settings.output_dir / "audio" if settings.save_audio else None
            if audio_dir is not None:
                case_id = f"{ex.recording_id}__{ex.noise_category}__{snr:g}dB"
                save_audio(audio_dir / case_id / "clean.wav", clean_scaled, settings.sample_rate)
                save_audio(audio_dir / case_id / "noisy.wav", mixture, settings.sample_rate)
            rows.extend(evaluate_case(clean_scaled, mixture, scaled_noise, settings.sample_rate,
                        ex.recording_id, ex.noise_category, float(snr), algorithms,
                        settings.algorithm_options, settings.metric_options,
                        settings.noise_profile, audio_dir, settings.warmup))
    df = pd.DataFrame(rows, columns=RESULT_COLUMNS)
    if not (df["status"] != "algorithm_failed").any():
        raise RuntimeError("All algorithms failed; no success file written")
    root = settings.output_dir
    df.to_csv(root / "benchmark.csv", index=False)
    (root / "benchmark.json").write_text(df.to_json(orient="records", indent=2), encoding="utf-8")
    summarize(df).to_csv(root / "summary.csv", index=False)
    summarize(df, ["algorithm", "noise_category", "target_snr_db", "pesq_mode",
                   "stoi_mode"]).to_csv(root / "summary_by_condition.csv", index=False)
    provenance = {
        "manifest_kind": manifest_kind(settings.manifest), "benchmark_version": __version__,
        "manifest": str(settings.manifest), "manifest_sha256": sha256(settings.manifest),
        "config_sha256": sha256(settings.config_path),
        "python": platform.python_version(), "numpy": np.__version__,
        "scipy": scipy.__version__, "sample_rate": settings.sample_rate,
        "segment_seconds": settings.segment_seconds, "seed": settings.seed,
        "snrs_db": snrs, "algorithms": algorithms, "noise_profile": settings.noise_profile,
        "metrics": settings.metric_options, "algorithm_options": settings.algorithm_options,
        "timing": "enhance() only; excludes loading, resampling, warmup, scoring, saving",
        "alignment": "zero-lag equal-length exact samples; no post hoc shifting",
        "recordings": files, "cases": df["case_id"].nunique(), "rows": len(df),
    }
    (root / "run_metadata.json").write_text(json.dumps(provenance, indent=2,
                                          default=str), encoding="utf-8")
    return df
