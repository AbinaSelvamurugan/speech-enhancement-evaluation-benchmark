"""Structural and algebraic CSV audit; never replaces independent metric validation."""
import json
from pathlib import Path
import numpy as np
import pandas as pd


def audit_results(path: str | Path) -> dict:
    path = Path(path).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Missing result CSV: {path}")
    frame = pd.read_csv(path)
    meta = json.loads((path.parent / "run_metadata.json").read_text(encoding="utf-8"))
    required = {"case_id", "recording_id", "noise_category", "target_snr_db", "algorithm",
                "input_snr_db", "noisy_reconstruction_snr_db", "reconstruction_snr_db",
                "snr_improvement_db", "pesq", "stoi", "status", "errors"}
    if frame.empty or not required.issubset(frame.columns):
        raise ValueError("Missing required columns or no rows")
    if frame.duplicated(["case_id", "algorithm"]).any():
        raise ValueError("Duplicate case-algorithm output")
    unexpected = set(frame.status) - {"ok", "metric_partial", "algorithm_failed"}
    if unexpected:
        raise ValueError(f"Invalid status labels {unexpected}")
    for errors in frame.errors:
        if not isinstance(json.loads(errors), dict):
            raise ValueError("errors must be a JSON mapping")
    good = frame[frame.status != "algorithm_failed"]
    if good.empty:
        raise ValueError("No algorithm results for audit")
    if not np.isfinite(good["reconstruction_snr_db"]).all():
        raise ValueError("Nonfinite reconstruction SNR in successful rows")
    if not np.allclose(good["snr_improvement_db"],
                       good["reconstruction_snr_db"] - good["noisy_reconstruction_snr_db"],
                       atol=1e-7, rtol=1e-9):
        raise ValueError("SNR improvement arithmetic mismatch")
    if not np.allclose(good["input_snr_db"], good["noisy_reconstruction_snr_db"],
                       atol=1e-7):
        raise ValueError("Mixture input/reconstruction SNR mismatch")
    if not np.allclose(good["input_snr_db"], good["target_snr_db"], atol=1e-6):
        raise ValueError("Controlled SNR calibration inconsistent")
    if not np.allclose(good.groupby("case_id").input_snr_db.max(),
                       good.groupby("case_id").input_snr_db.min(), atol=1e-12):
        raise ValueError("Different algorithms received inconsistent input SNR")
    if not good["stoi"].dropna().between(-1.001, 1.001).all():
        raise ValueError("Out of range STOI score")
    if not good["pesq"].dropna().between(-.5, 4.65).all():
        raise ValueError("Out of range PESQ score")
    for case_id, group in frame.groupby("case_id"):
        if set(group.algorithm) != set(meta["algorithms"]):
            raise ValueError(f"Missing algorithm within case {case_id}")
    if meta["rows"] != len(frame) or meta["cases"] != frame.case_id.nunique():
        raise ValueError("run_metadata counts disagree with CSV")
    result = {
        "verdict": "PASS: CSV structure and arithmetic",
        "manifest_kind": meta["manifest_kind"],
        "cases": int(frame.case_id.nunique()), "rows": len(frame),
        "independent_recording_ids": int(frame.recording_id.nunique()),
        "valid_pesq": int(frame.pesq.notna().sum()),
        "valid_stoi": int(frame.stoi.notna().sum()),
        "algorithm_failures": int((frame.status == "algorithm_failed").sum()),
        "metric_partial": int((frame.status == "metric_partial").sum()),
    }
    return result
