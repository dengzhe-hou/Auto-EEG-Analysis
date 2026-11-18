# Per-skill acceptance



Executed deliveries with verified outcomes 198/198. Passed 192, failed 6, incomplete 0.

API usage estimate USD 0.6398. Committed including unresolved reserves USD 0.6398.

See PER_SKILL.csv, SESSION_RESULTS.csv and the frozen plan.

Each result describes a bounded skill operation on a specified synthetic or saved-stage fixture.

## Changes and full retest

The repaired candidate is ac4aa825e454ab8ce3745d428ce5398f00fecfef. The Python dependency path now reaches the BIDS analysis subprocess. Guidance clarifies array axes, the specified MNE Morlet implementation, GEV denominators and stage readiness. Sixteen task requests clarify their existing output or execution requirements, and the common prompt requests full JSON precision. The original 66 inputs, references, tolerance values and verifier are identical to the first run. Offline job 51189 verified 12 saved child-process deliveries and all 66 expected-output fixtures before the metered sessions started.

The fixed verifier accepted 192/198 (96.97%) in the revised setup, compared with 168/198 (84.85%) in the first run. This difference is 12.12 percentage points and covers the combined execution and wording repairs. 17 of 22 skills reached 9/9. The original session outputs and evaluations remain in the first run directory.

| Skill | First run | Full retest |
|---|---:|---:|
| eeg-audit | 9/9 | 7/9 |
| eeg-behavior | 6/9 | 8/9 |
| eeg-bids | 3/9 | 8/9 |
| eeg-complexity | 9/9 | 9/9 |
| eeg-connectivity | 6/9 | 9/9 |
| eeg-decoding | 4/9 | 9/9 |
| eeg-epoch | 9/9 | 9/9 |
| eeg-erp | 9/9 | 9/9 |
| eeg-figure | 9/9 | 9/9 |
| eeg-group-compare | 7/9 | 9/9 |
| eeg-ica | 9/9 | 9/9 |
| eeg-methods-text | 9/9 | 9/9 |
| eeg-microstate | 3/9 | 9/9 |
| eeg-pipeline | 8/9 | 8/9 |
| eeg-preprocess | 9/9 | 8/9 |
| eeg-qc | 9/9 | 9/9 |
| eeg-recipe | 9/9 | 9/9 |
| eeg-report | 9/9 | 9/9 |
| eeg-source | 9/9 | 9/9 |
| eeg-spectral | 9/9 | 9/9 |
| eeg-stats | 9/9 | 9/9 |
| eeg-tfr | 5/9 | 9/9 |

## Remaining nonpassing deliveries

| Session | Evidence |
|---|---|
| skills66__behavior-response-assignment__rep1 | The execution loop received Markdown fence/prose in Python cells repeatedly and exited without a complete delivery. |
| skills66__preprocess-resample-events__rep1 | The saved event indices agree with the target indices, but the result returned the whole three-column event table instead of its sample-index column. |
| skills66__bids-sample-origin__rep1 | The archived program applied average referencing before export. The saved marker samples agree, but the saved waveform differs. |
| skills66__audit-unit-of-analysis__rep2 | Result fields matched and the saved analysis.py required for this run was absent. |
| skills66__pipeline-start__rep3 | The execution loop received prose and fencing in the Python cell repeatedly and exited without a complete delivery. |
| skills66__audit-window__rep3 | Result fields matched and the saved analysis.py required for this run was absent. |

All nine BIDS attempts generated an output dataset. The one failure reflects the extra average reference. The earlier BIDS import and missing-output failures did not recur. The cross-run table keeps other new failures visible.

All six Slurm batches and the two final jobs completed with ExitCode 0:0. The formal sessions ran for 56.6 wall-clock minutes with one CPU and 4 GiB. CPU occupancy was 38.4% and highest scheduler-sampled step memory was 0.97 GiB. Measured batch durations were 9 to 10 minutes against the 20-minute time limit. Provider API usage was estimated at USD 0.639794. The second independent count check reconciled every session and confirmed the model and packet receipts.
