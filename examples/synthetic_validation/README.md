# Synthetic validation example

This folder holds a small generated audio fixture with its measured scores and PNG figures.
The signals are synthetic test audio, not real speech recordings; the folder contains no
voices, clean-speech corpora, or external datasets.

- 3 independent generated signals, 3 SNR levels, 4 approaches: 36 measured rows.
- STOI was computed with the `pystoi` library on the synthetic waveforms.
- The figures and report are the artifacts written by the run.

The report renders on GitHub: [Measured validation report](report.md).
To regenerate the fixture and run it, use `python scripts/make_synthetic_fixture.py` and
the commands in the root [README](../../README.md).
