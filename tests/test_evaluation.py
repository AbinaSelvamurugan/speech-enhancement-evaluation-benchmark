import json
from pathlib import Path
import numpy as np
import pytest
import pandas as pd
from speech_benchmark.config import load_settings
from speech_benchmark.evaluation.experiments import read_manifest
from speech_benchmark.evaluation.runner import evaluate_case, run_benchmark
from speech_benchmark.evaluation.statistics import paired_comparisons
from speech_benchmark.audio.mixing import mix_at_snr


def _configs(tmp_path, manifest):
    cfg = tmp_path / "config"
    cfg.mkdir()
    (cfg / "benchmark.yaml").write_text(
        f"manifest: {manifest}\noutput_dir: {tmp_path / 'out'}\n"
        "sample_rate: 16000\nsegment_seconds: 1.5\nsnrs_db: [0, 5]\nseed: 88\n"
        "max_recordings: 0\nalgorithms: [noisy, spectral_subtraction, spectral_gating, wiener]\n"
        "noise_profile: oracle\nsave_audio: true\nwarmup: false\n")
    (cfg / "algorithms.yaml").write_text("{}\n")
    (cfg / "metrics.yaml").write_text("pesq_mode: wb\nstoi_extended: false\n"
                                                "power_floor: 1.0e-12\nbootstrap_iterations: 200\n"
                                                "confidence_level: 0.95\n")
    return load_settings(cfg / "benchmark.yaml")


def test_missing_manifest(tmp_path):
    with pytest.raises(FileNotFoundError):
        read_manifest(tmp_path / "missing.json")


def test_reject_missing_audio_in_manifest(tmp_path):
    path = tmp_path / "manifest.json"
    obj = {"kind": "real_recordings", "recordings": [{k:"x" for k in
           ("id", "clean", "noise", "noise_category", "clean_license", "noise_license",
            "clean_source", "noise_source")}]}
    path.write_text(json.dumps(obj))
    with pytest.raises(FileNotFoundError):
        read_manifest(path)


def test_pipeline_and_repeatability(tmp_path, synthetic_manifest):
    s = _configs(tmp_path, synthetic_manifest)
    a = run_benchmark(s, max_recordings=2)
    assert len(a) == 2*2*4
    assert set(a.algorithm) == {"noisy", "spectral_subtraction", "spectral_gating", "wiener"}
    assert (a.status != "algorithm_failed").all()
    assert a.stoi.notna().all()
    assert a.pesq.notna().sum() in (0, len(a))  # availability is environment-dependent
    csv = pd.read_csv(s.output_dir / "benchmark.csv")
    assert len(csv) == len(a)
    assert len(json.loads((s.output_dir / "benchmark.json").read_text())) == len(a)
    assert (s.output_dir / "run_metadata.json").is_file()
    assert (s.output_dir / "summary_by_condition.csv").is_file()
    b = run_benchmark(s, max_recordings=2)
    np.testing.assert_allclose(a.reconstruction_snr_db, b.reconstruction_snr_db)
    np.testing.assert_allclose(a.stoi, b.stoi)
    assert (a[a.algorithm=="noisy"].snr_improvement_db == 0).all()


def test_filter_no_recordings(tmp_path, synthetic_manifest):
    s = _configs(tmp_path, synthetic_manifest)
    with pytest.raises(ValueError):
        run_benchmark(s, categories=["real_traffic_not_in_fixture"])


def test_algorithm_failure_isolated(synthetic_signal):
    clean, v, fs = synthetic_signal
    s, y, noise, _ = mix_at_snr(clean, v, 5)
    metrics = {"power_floor": 1e-12, "pesq_mode": "wb", "stoi_extended": False}
    rows = evaluate_case(s, y, noise, fs, "a", "noise", 5,
                         ["noisy", "neural", "wiener"], {}, metrics, "oracle", warmup=False)
    assert rows[1]["status"] == "algorithm_failed"
    assert "unavailable" in rows[1]["errors"]
    assert rows[0]["status"] != "algorithm_failed"
    assert rows[2]["status"] != "algorithm_failed"


def test_bootstrap_cluster_count():
    rows = []
    for k in range(7):
        for snr in [-5, 0, 5]:
            for name, delta in [("noisy",0),("wiener",.1)]:
                rows.append(dict(recording_id=str(k), case_id=f"{k}:{snr}",
                                 algorithm=name,pesq_mode="wb",stoi_mode="stoi",
                                 pesq=.9+delta,stoi=.5+delta,
                                 reconstruction_snr_db=snr+delta,
                                 snr_improvement_db=delta))
    stats = paired_comparisons(pd.DataFrame(rows), iterations=200)
    assert len(stats) == 4
    assert (stats.independent_recordings == 7).all()
    assert (stats.paired_cases == 21).all()
    assert stats.ci_low.notna().all()
    assert stats.wilcoxon_p.notna().all()


def test_one_failed_metric_keeps_other_scores(monkeypatch, synthetic_signal):
    import speech_benchmark.evaluation.runner as module
    clean, noise, fs = synthetic_signal
    s, mixture, added, _ = mix_at_snr(clean, noise, 0)

    def forced_pesq_failure(*args, **kwargs):
        raise RuntimeError("deliberate test-only PESQ failure")

    monkeypatch.setattr(module, "compute_pesq", forced_pesq_failure)
    metrics = {"power_floor": 1e-12, "pesq_mode": "wb", "stoi_extended": False}
    row = evaluate_case(s, mixture, added, fs, "failure_case", "synthetic", 0,
                        ["wiener"], {}, metrics, "oracle", warmup=False)[0]
    assert row["status"] == "metric_partial"
    assert np.isnan(row["pesq"])
    assert np.isfinite(row["stoi"])
    assert "deliberate test-only PESQ failure" in row["errors"]
