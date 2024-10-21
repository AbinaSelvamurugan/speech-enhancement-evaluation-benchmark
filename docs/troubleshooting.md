# Troubleshooting

- `PESQ dependency unavailable`: `python -m pip install pesq==0.0.4`. Building the extension
  needs a working C compiler, NumPy and potentially Cython; verify Python compatibility.
  If the install fails, the benchmark retains blank PESQ columns and error explanations.
- `ruﬀ`/`ruff` unavailable: install `ruff==0.15.5` then `ruff check .`.
- `Dataset manifest absent`: data are not downloaded automatically; consult
  `data/README.md`, obtain licensed sources and create accurate manifest JSON.
- `Unaligned lengths`: enhanced outputs must be exactly same samples as reference.
  Do not blindly truncate external model outputs; account for deterministic fixed delay.
- `Near-silent clean reference`: omit unusable source clip rather than turning 0/0 into 0 dB.
- `No recordings after filtering`: inspect manifest `noise_category` values and `--categories`.
- `metric_partial`: read `errors` JSON column; no replacement with synthetic scores.
- `ImportError` when executing scripts: `python -m pip install -e .`, or for offline
  development `PYTHONPATH=src python scripts/run_benchmark.py ...`.
- `High peak`: audio is written as float WAV, not arbitrarily clipped after scoring.
- Very slow plots: set `MPLBACKEND=Agg`; report is file-based and needs no dashboard.
- Empty CIs/p-values: <3 or <6 independent recording IDs; 5 SNR versions of one
  recording are **not** 5 independent speakers.
