"""Paired comparisons aggregated at recording level; recording-cluster bootstrap."""
from itertools import combinations
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

COMPARED_METRICS = ("pesq", "stoi", "reconstruction_snr_db", "snr_improvement_db")


def paired_comparisons(df: pd.DataFrame, base="noisy", iterations=2000,
                       confidence=0.95, seed=1527) -> pd.DataFrame:
    results = []
    rng = np.random.default_rng(seed)
    for metric in COMPARED_METRICS:
        for (mode, stoi_mode), chunk in df.groupby(["pesq_mode", "stoi_mode"]):
            # Exactly the same input case for both algorithms; then mean within speaker/recording.
            chunk = chunk[["case_id", "recording_id", "algorithm", metric]].dropna()
            if chunk.empty:
                continue
            paired = chunk.pivot_table(index=["recording_id", "case_id"],
                                       columns="algorithm", values=metric, aggfunc="mean")
            names = sorted(paired.columns)
            if base is not None and base not in names:
                continue
            if base is None:
                # Place the noisy control first so differences are intuitive.
                names = (["noisy"] if "noisy" in names else []) + [
                    name for name in names if name != "noisy"]
                pairs = list(combinations(names, 2))
            else:
                pairs = [(base, name) for name in names if name != base]
            for first, other in pairs:
                diffs = (paired[other] - paired[first]).dropna()
                if diffs.empty:
                    continue
                record_diffs = diffs.groupby(level="recording_id").mean().to_numpy()
                n = len(record_diffs)
                delta = float(record_diffs.mean())
                low, high = float("nan"), float("nan")
                if n >= 3 and iterations >= 100:
                    means = np.mean(rng.choice(record_diffs, (iterations, n), replace=True), axis=1)
                    low, high = np.quantile(means, ((1 - confidence) / 2, (1 + confidence) / 2))
                pval = float("nan")
                if n >= 6 and np.count_nonzero(record_diffs) >= 6:
                    try:
                        pval = float(wilcoxon(record_diffs, zero_method="wilcox").pvalue)
                    except ValueError:
                        pass
                effect = float(delta / np.std(record_diffs, ddof=1)) if n >= 2 and np.std(
                    record_diffs, ddof=1) > 1e-12 else float("nan")
                results.append(dict(metric=metric, pesq_mode=mode, stoi_mode=stoi_mode,
                                    baseline=first, alternative=other, paired_cases=len(diffs),
                                    independent_recordings=n, mean_difference=delta,
                                    ci_low=float(low), ci_high=float(high),
                                    cohen_dz=effect, wilcoxon_p=pval))
    frame = pd.DataFrame(results)
    if frame.empty:
        return frame
    frame["holm_p"] = np.nan
    # Holm across all completed comparisons (conservative family-wide correction).
    valid = frame["wilcoxon_p"].dropna().sort_values()
    m = len(valid)
    corrected = np.maximum.accumulate([(m - i) * p for i, p in enumerate(valid)])
    frame.loc[valid.index, "holm_p"] = np.minimum(1.0, corrected)
    return frame
