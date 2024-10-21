# Preregistered evaluation design

- Use `real_recordings` manifest of correctly sourced, licensed clean utterances and
  distinct environmental noise files with documented contents, original split and attribution.
- Use speaker-disjoint evaluation partition. Never tune subtraction strength, gating
  thresholds or Wiener smoothing on test outcomes. Use separately held-out tuning data.
- Same clean segment/noise offset reused across SNRs and algorithms. Fixed SNRs:
  −5, 0, 5, 10, 15 dB. Fixed clean duration: 4s, sample rate: 16kHz.
- Investigate oracle noise PSD first as a privileged classical reference, then blind
  PSD in a distinct run, avoiding mixing these conditions in one statistical summary.
- Evaluator compares 3 classical enhancements to the unprocessed control, not to
  oracle clean. `input_snr_db` is the measured mixture; `snr_improvement_db` is the
  reconstruction difference. PESQ@16k WB and ordinary STOI are the primary endpoints.
- Missing metric/algorithm results remain missing with error details. Aggregate only
  same PESQ/STOI modes. Report means, medians, SD (sample ddof=1), counts and failures.
- Pair comparisons by exact `case_id`; average paired differences within each independent
  recording ID. Bootstrap the recording means (2000 draws) if n>=3. Use two-sided Wilcoxon
  on recording means if n>=6 and >=6 nonzero differences. Apply Holm correction across
  all executed comparisons; inspect uncorrected and adjusted p-values plus effect size dz.
- Statistically defensible *claims* need many independent speakers/noise conditions;
  CI excludes zero is not conclusive if dataset chosen opportunistically. No inferential
  p-value is produced when sample conditions aren't met.
- Time methods on same machine, after the same class of warmup; report RTF and
  workload. Optional human A/B listening is valuable because objective metrics are proxies.
- Do not substitute pure tones (from deterministic software fixtures) for real speech
  when answering perceptual-quality research questions.
