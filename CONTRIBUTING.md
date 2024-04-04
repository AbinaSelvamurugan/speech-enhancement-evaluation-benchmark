# Contributions

Use Python >=3.11,<3.14, install `pip install -e '.[dev]'` in a clean virtualenv.
Before changes run `python -m pytest -q` and `ruff check .`.
Never commit audio you do not have redistribution rights to, generated large WAVs,
PESQ sources, checkpoints, credentials or hand-edited benchmark scores.
Document algorithm assumptions and add deterministic tests for processing and failure paths.
New algorithms implement `Denoiser.enhance()` and register in `algorithms/registry.py`.
Evaluation-data provenance and noise-exposure rules must be recorded in manifests.
For quality claims, submit the complete CSV, YAML config, audio hashes and licensing metadata.
