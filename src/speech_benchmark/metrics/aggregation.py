"""Finite-only metrics with explicit missing values and failure counts."""
import pandas as pd

KEYS = ["algorithm", "noise_category", "target_snr_db", "pesq_mode", "stoi_mode"]
METRICS = ["pesq", "stoi", "input_snr_db", "reconstruction_snr_db",
           "snr_improvement_db", "processing_ms", "rtf"]


def summarize(df: pd.DataFrame, groups: list[str] | None = None) -> pd.DataFrame:
    groups = groups or ["algorithm", "pesq_mode", "stoi_mode"]
    if df.empty:
        return pd.DataFrame()
    output = []
    for keys, sub in df.groupby(groups, dropna=False, sort=True):
        keys = keys if isinstance(keys, tuple) else (keys,)
        record = dict(zip(groups, keys))
        record["total_cases"] = len(sub)
        record["unique_recordings"] = sub["recording_id"].nunique()
        record["algorithm_failures"] = int((sub["status"] == "algorithm_failed").sum())
        for metric in METRICS:
            scores = pd.to_numeric(sub[metric], errors="coerce").dropna()
            record.update({
                f"{metric}_mean": float(scores.mean()) if len(scores) else float("nan"),
                f"{metric}_median": float(scores.median()) if len(scores) else float("nan"),
                f"{metric}_std": float(scores.std(ddof=1)) if len(scores) > 1 else float("nan"),
                f"{metric}_n": int(len(scores)),
                f"{metric}_failures": int(len(sub) - len(scores)),
            })
        output.append(record)
    return pd.DataFrame(output)
