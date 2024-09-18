import json
import numpy as np
import pandas as pd
from speech_benchmark.reporting.report import generate_report
from speech_benchmark.metrics.aggregation import summarize
from speech_benchmark.evaluation.runner import RESULT_COLUMNS


def test_aggregation_counts():
    a = pd.DataFrame([dict(algorithm="x",pesq_mode="wb",stoi_mode="stoi",
                          recording_id="one", status="metric_partial", pesq=np.nan, stoi=.6),
                      dict(algorithm="x",pesq_mode="wb",stoi_mode="stoi",
                           recording_id="two",status="ok",pesq=2.2,stoi=.7)])
    for c in RESULT_COLUMNS:
        if c not in a:
            a[c] = np.nan
    out = summarize(a)
    assert out.pesq_n.iloc[0] == 1
    assert out.pesq_failures.iloc[0] == 1
    assert out.stoi_n.iloc[0] == 2


def test_report_real_files(tmp_path):
    path = tmp_path / "benchmark.csv"
    data = []
    for i in range(2):
        for name in ("noisy", "wiener"):
            row = dict.fromkeys(RESULT_COLUMNS)
            row.update(case_id=f"fixture{i}", recording_id=f"fixture{i}",
                       noise_category="synthetic_only", target_snr_db=5,
                       algorithm=name, pesq_mode="wb", stoi_mode="stoi",
                       pesq=np.nan, stoi=.65+(.05 if name=="wiener" else 0),
                       reconstruction_snr_db=5+(1 if name=="wiener" else 0),
                       snr_improvement_db=1 if name=="wiener" else 0,
                       processing_ms=5,rtf=.005,input_snr_db=5,status="metric_partial")
            data.append(row)
    pd.DataFrame(data).to_csv(path, index=False)
    meta = {"manifest_kind":"synthetic_test_only", "sample_rate":16000,
            "config_sha256":"synthetic", "manifest_sha256":"synthetic", "seed":2,
            "snrs_db":[5], "segment_seconds":2, "noise_profile":"oracle",
            "algorithms":["noisy","wiener"],"alignment":"zero lag", "timing":"enhance() only",
            "metrics":{"bootstrap_iterations":200,"confidence_level":.95}}
    (tmp_path / "run_metadata.json").write_text(json.dumps(meta))
    report = generate_report(path)
    text = report.read_text()
    assert "synthetic test signals rather than real speech" in text
    assert "PESQ valid 0/4" in text
    assert "No valid measurements" in text or "unavailable" in text
    assert (tmp_path / "figures/mean_stoi.png").is_file()
    assert (tmp_path / "paired_statistics.csv").is_file()


def test_missing_report_metadata(tmp_path):
    path = tmp_path / "benchmark.csv"
    path.write_text("fake,columns\n1,2\n")
    import pytest
    with pytest.raises(FileNotFoundError):
        generate_report(path)
