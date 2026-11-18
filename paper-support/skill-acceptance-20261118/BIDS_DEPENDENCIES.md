# BrainVision export runtime

Offline job 51127 passed the fixture checks and found that the retained CodeAct image lacks mne-bids. The new suite mounts mne-bids 0.18.0 and pybv 0.7.6 from the existing server environment as read-only Python packages for the BIDS tasks. The base image, MNE 1.8.0, data, references and decision rules are preserved. Preflight confirms actual BrainVision export and read-back in the isolated runtime.

Job 51129 confirmed that 0.18.0 cannot run on the retained Python 3.9 image because datetime.UTC is unavailable. The next offline attempt mounts the official MNE-BIDS 0.15.0 wheel, which supports Python 3.9, alongside the existing pybv 0.7.6. The older failed attempt and packages remain recorded.
