import json
import pandas as pd
import pytest
from speech_benchmark.evaluation.audit import audit_results


def test_audit_detects_bad_reconstruction_arithmetic(tmp_path):
    csv = tmp_path / "benchmark.csv"
    pd.DataFrame([dict(case_id="a", recording_id="a",noise_category="test",
                       target_snr_db=0,algorithm="noisy",input_snr_db=0,
                       noisy_reconstruction_snr_db=0,reconstruction_snr_db=0,
                       snr_improvement_db=42, pesq=None,stoi=.2,status="metric_partial",
                       errors="{}")]).to_csv(csv,index=False)
    (tmp_path / "run_metadata.json").write_text(json.dumps({
        "algorithms":["noisy"],"rows":1,"cases":1,"manifest_kind":"synthetic_test_only"}))
    with pytest.raises(ValueError, match="SNR improvement"):
        audit_results(csv)
