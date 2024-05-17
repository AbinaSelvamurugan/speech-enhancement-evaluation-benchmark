"""Tabulations are computed exclusively from measured rows."""
from pathlib import Path
import pandas as pd
from speech_benchmark.metrics.aggregation import summarize
from speech_benchmark.evaluation.statistics import paired_comparisons


def write_tables(df: pd.DataFrame, directory: Path, *, iterations=2000, confidence=0.95):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    summarize(df).to_csv(directory / "summary.csv", index=False)
    summarize(df, ["algorithm", "noise_category", "target_snr_db", "pesq_mode",
                   "stoi_mode"]).to_csv(directory / "summary_by_condition.csv", index=False)
    pairs = paired_comparisons(df, base=None, iterations=iterations, confidence=confidence)
    pairs.to_csv(directory / "paired_statistics.csv", index=False)
    return pairs
