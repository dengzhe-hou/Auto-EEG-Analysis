# AEA skill acceptance and full retest

This archive covers 22 skills. Each skill was assigned three representative synthetic or saved-stage tasks, with three fresh Haiku 5.5 executions per task. Each round contains 198 first deliveries.

| Round | Accepted deliveries | Skills with nine accepted deliveries |
| --- | ---: | ---: |
| Initial | 168/198 (84.85%) | 14/22 |
| Repaired setup | 192/198 (96.97%) | 17/22 |

The two rounds share the original reference values, input data, numerical tolerances and deterministic checks. The retest followed repairs to BIDS dependency propagation, revised AEA guidance and clearer instructions for certain tasks. The archive preserves the full initial results and the recorded acceptance failures in both rounds. These results cover the specified operations under the recorded model and execution settings. The manuscript's paired evaluations provide the separate comparison with the same model without AEA.

## Evidence and exact resources

- [Initial report](original/TEST_REPORT.md), [per-session results](original/SESSION_RESULTS.csv), [first deliveries](original/first-deliveries.zip) and [protocol](original/PROTOCOL_FROZEN.json)
- [Retest report](retest/TEST_REPORT.md), [per-session results](retest/SESSION_RESULTS.csv), [first deliveries](retest/first-deliveries.zip) and [protocol](retest/PROTOCOL_FROZEN.json)
- [Per-skill comparison](BEFORE_AFTER.csv), [skill guidance patch](aea-skill-repairs.patch), [runner changes](runner-repair.diff), [preflight fix record](PREFLIGHT_FIXES.md) and [export dependency record](BIDS_DEPENDENCIES.md)

The initial AEA resource base is [06c6c44](https://github.com/dengzhe-hou/Auto-EEG-Analysis/commit/06c6c44d6fcc11f0a4727b292588525b7ca83f1e). Apply the skill guidance patch to that base to reproduce the resource changes for the recorded candidate ac4aa82. The initial and retest task manifests contain the instructions for each round of this engineering record. Shared input arrays, independent reference fields and the original acceptance script accompany the manifests.

The two ZIP files hold the retained first submissions, saved programs, result JSON, grading reasons, requested artifacts and executed code cells where present. A missing deliverable remains missing. Build and delivery paths from the server were normalized. The archives include synthetic EEG and synthetic stage records and omit provider request payloads.

## Check archived outputs locally

Use Python with NumPy, SciPy, MNE and MNE-BIDS. The original artifact verifier ran with MNE 1.11.0 and MNE-BIDS 0.18.0. The model-facing runner used MNE 1.8.0, with MNE-BIDS 0.15.0 and PyBV 0.7.6 for the BIDS tasks.

Run the following from this directory. The command checks the saved files and recounts the two rounds without invoking a model or executing the model-written programs.

```bash
python -B replay_archive.py
```

The expected counts are 168/198 and 192/198. The full reports list the operations tested and identify the remaining failures.
