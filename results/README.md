# Experiment artifacts

A benchmark run emits `benchmark.csv`, `benchmark.json`, `summary.csv`,
`summary_by_condition.csv`, `run_metadata.json`, and optional 32-bit float audio outputs.
`report` produces `paired_statistics.csv`, `figures/*.png`, `figures/*.svg`, and `report.md`.

`status=ok` means all implemented metrics succeeded, `metric_partial` means at least one
metric was unavailable or failed (see the `errors` field in the JSON), and
`algorithm_failed` means the run produced no valid result. Missing metric values are written
as empty CSV fields or JSON null, never zero.

Results depend on representative licensed real audio, independent recording clusters, a
working PESQ install, and sufficient statistical power.
