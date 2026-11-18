# Per-skill acceptance



Executed deliveries with verified outcomes 198/198. Passed 168, failed 30, incomplete 0.

API usage estimate USD 0.6249. Committed including unresolved reserves USD 0.6249.

See PER_SKILL.csv, SESSION_RESULTS.csv and the frozen plan.

Each result describes a bounded skill operation on a specified synthetic or saved-stage fixture.

## Skill-level deliveries

| Skill | Operations | Accepted first deliveries |
|---|---|---:|
| eeg-audit | matched, window, unit-of-analysis | 9/9 |
| eeg-behavior | correct-trial-rt, response-assignment, identity-join | 6/9 |
| eeg-bids | signals, channel-status, sample-origin | 3/9 |
| eeg-complexity | sampen, permutation-entropy, approximate-entropy | 9/9 |
| eeg-connectivity | pearson, plv, debiased-wpli2 | 6/9 |
| eeg-decoding | held-out-subjects, held-out-blocks, balanced-null | 4/9 |
| eeg-epoch | event-lock, baseline, trial-rejection | 9/9 |
| eeg-erp | condition-mean, signed-difference, fixed-window-roi | 9/9 |
| eeg-figure | erp-wave, delta-wave, spectrum | 9/9 |
| eeg-group-compare | welch-two-group, paired-subjects, one-way-f | 7/9 |
| eeg-ica | replay-none, remove-one, remove-two | 9/9 |
| eeg-methods-text | acquisition, epoching, retained-and-seed | 9/9 |
| eeg-microstate | transitions, coverage, gev | 3/9 |
| eeg-pipeline | start, resume, blocked-stage | 8/9 |
| eeg-preprocess | reference, channels-and-crop, resample-events | 9/9 |
| eeg-qc | clean, constant-channel, rapid-step | 9/9 |
| eeg-recipe | meets-minimum, missing-marker, insufficient-trials | 9/9 |
| eeg-report | recorded-summary, include-missing, read-executed-seed | 9/9 |
| eeg-source | ridge-inverse, noise-normalized, strong-regularization | 9/9 |
| eeg-spectral | welch-band-power, peak-frequency, relative-power | 9/9 |
| eeg-stats | one-sample-t, paired-effect, exact-sign-flip | 9/9 |
| eeg-tfr | morlet-power, morlet-itc, baseline-logratio | 5/9 |

## Failure details

The fixed verifier accepted 168/198 (84.85%). Fourteen skills reached 9/9. The 30 failures include delivery and representation mismatches as well as calculation errors.

Eight deliveries had matching substantive values but differed in representation. Three trial joins reported the correct unmatched IDs in input order, while the checker expected sorted IDs. Three Pearson calculations returned the exact coefficients with pair labels. Two paired tests gave the matching statistic and p value and represented the paired sample size with one number. Those grader assumptions were stricter than the public task wording. The frozen verdicts and all first deliveries are retained. These observations do not define a second pass rate.

| Task | Failed | First frozen check messages |
|---|---:|---|
| behavior-identity-join | 3/3 | 3 at result.json.missing_on_eeg[0]: exact number mismatch |
| bids-channel-status | 1/3 | 1 at result.json absent |
| bids-sample-origin | 2/3 | 1 at bids/sub-01/eeg/sub-01_task-check_eeg.vhdr: missing or empty / 1 at result.json absent |
| bids-signals | 3/3 | 2 at result.json absent / 1 at BIDS EEGReference: exact value mismatch |
| connectivity-pearson | 3/3 | 3 at result.json.edges[0]: numeric mismatch |
| decoding-balanced-null | 3/3 | 3 at result.json.predictions[0]: expected list of length 5 |
| decoding-held-out-blocks | 1/3 | 1 at result.json.predictions[0]: expected list of length 5 |
| decoding-held-out-subjects | 1/3 | 1 at result.json.predictions[0]: expected list of length 5 |
| group-compare-paired-subjects | 2/3 | 2 at result.json.n_per_group: expected list of length 2 |
| microstate-coverage | 3/3 | 2 at result.json.coverage_pct: expected list of length 3 / 1 at result.json.coverage_pct[1]: numeric mismatch |
| microstate-gev | 2/3 | 2 at result.json.gev_by_state[0]: numeric mismatch |
| microstate-transitions | 1/3 | 1 at result.json.counts: expected list of length 3 |
| pipeline-start | 1/3 | 1 at result.json.blocked: expected list of length 4 |
| tfr-morlet-itc | 2/3 | 1 at result.json.values[0][0]: numeric mismatch / 1 at result.json.values: expected list of length 2 |
| tfr-morlet-power | 2/3 | 2 at result.json.values[0][0]: numeric mismatch |

The microstate GEV discrepancies include an incorrect denominator using correlation-weighted power. Decoding failures include returning three predictions per trial when five time samples were required. The BIDS losses include four missing result files, one missing BrainVision file and one mismatched reference sidecar field.

## Runtime and evidence

Formal sessions ran on one CPU in 60 minutes and 45 seconds. All six Slurm batches, the summary job and the independent aggregate job completed with ExitCode 0:0. The worker memory limit was 4 GiB and the highest recorded step MaxRSS was 0.94 GiB. These step peaks are scheduler samples. Batch CPU occupancy computed from TotalCPU and allocated CPU seconds was 40.1%. Comparable batches took 9 to 12 minutes, below the 75-minute initial limit. The slowest observed batch supports a roughly 19-minute limit for a future same-shape batch at the 1.5 multiplier, before any change in API latency.

The 198 actual sessions used the recorded Haiku 5.5 settings, with a complete assigned entrypoint in the provider requests and the kernel within its worker cgroup. The MNE 1.8.0 Python 3.9 image mounted MNE-BIDS 0.15.0 and pybv 0.7.6 read-only for the BIDS tasks. A real export and read-back was checked before paid execution. Preflight logs preserve the discovered sample-origin issue and the incompatible prior MNE-BIDS version.
