#!/usr/bin/env python3
"""Generate the tiny synthetic resting-state EEG signal shipped with this starter.

Pure standard library so it runs in any Python without extra deps. The output
is deterministic (fixed seed), so re-running it reproduces the committed file
byte for byte.

Signal model (8 s at 250 Hz = 2000 samples, microvolts):
  - low-amplitude broadband background noise
  - a 10 Hz alpha oscillation
  - a 50 Hz mains component (so the notch in clean.py has something to remove)
  - four short high-amplitude transient bursts at known times

Run:  python data/raw/make_synthetic_eeg.py
"""
from __future__ import annotations

import math
import random
from pathlib import Path

FS = 250.0            # sampling frequency (Hz) — mirrored in the .json sidecar
DURATION_S = 8.0      # recording length (seconds)
SEED = 20260908       # fixed for reproducibility
BURST_ONSETS_S = (1.2, 3.4, 5.1, 6.8)  # burst start times (seconds)
BURST_LEN_S = 0.25    # burst duration (seconds)

OUT = Path(__file__).resolve().parent / "sub-01" / "eeg" / "sub-01_task-rest_eeg.txt"


def main() -> None:
    rng = random.Random(SEED)
    n = int(DURATION_S * FS)
    burst_windows = [
        (int(t * FS), int((t + BURST_LEN_S) * FS)) for t in BURST_ONSETS_S
    ]

    samples = []
    for i in range(n):
        t = i / FS
        background = rng.gauss(0.0, 3.0)          # broadband noise
        alpha = 8.0 * math.sin(2 * math.pi * 10.0 * t)   # 10 Hz alpha
        mains = 2.5 * math.sin(2 * math.pi * 50.0 * t)   # 50 Hz mains
        value = background + alpha + mains
        for start, end in burst_windows:
            if start <= i < end:
                value += 45.0 * math.sin(2 * math.pi * 30.0 * t)  # 30 Hz burst
        samples.append(value)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(f"{v:.4f}" for v in samples) + "\n", encoding="utf-8")
    print(f"wrote {len(samples)} samples to {OUT}")


if __name__ == "__main__":
    main()
