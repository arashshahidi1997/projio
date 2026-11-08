"""Clean the raw synthetic EEG: first-order high-pass + 50 Hz notch.

Runs as a Snakemake `script:` (the `snakemake` object is injected), or
standalone from the repo root for quick inspection:

    python code/pipelines/demo/scripts/clean.py

--------------------------------------------------------------------------
NOTE FOR THE AGENT DEMO
The idea note in docs/log/idea/ proposes a 1 Hz high-pass. This script
applies HIGHPASS_HZ = 0.5. That mismatch is deliberate: it is the
inconsistency the demo asks the agent to surface as a human decision, not
to silently paper over.
--------------------------------------------------------------------------
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

# --- Filter settings (the load-bearing constants for the demo) -------------
HIGHPASS_HZ = 0.5   # first-order high-pass cutoff (idea note proposes 1 Hz)
NOTCH_HZ = 50.0     # mains notch (matches PowerLineFrequency in the sidecar)
NOTCH_Q = 30.0      # notch quality factor (narrowness)


def _read_signal(path: str | Path) -> np.ndarray:
    return np.loadtxt(path, dtype=float)


def _sampling_frequency(sidecar: str | Path, default: float = 250.0) -> float:
    try:
        meta = json.loads(Path(sidecar).read_text(encoding="utf-8"))
        return float(meta.get("SamplingFrequency", default))
    except (OSError, ValueError):
        return default


def highpass(x: np.ndarray, fs: float, fc: float) -> np.ndarray:
    """First-order RC high-pass. y[n] = a*(y[n-1] + x[n] - x[n-1])."""
    dt = 1.0 / fs
    rc = 1.0 / (2.0 * math.pi * fc)
    a = rc / (rc + dt)
    y = np.empty_like(x)
    y[0] = 0.0
    for n in range(1, len(x)):
        y[n] = a * (y[n - 1] + x[n] - x[n - 1])
    return y


def notch(x: np.ndarray, fs: float, f0: float, q: float) -> np.ndarray:
    """RBJ biquad band-stop (notch) at f0."""
    w0 = 2.0 * math.pi * f0 / fs
    alpha = math.sin(w0) / (2.0 * q)
    cos_w0 = math.cos(w0)
    b0, b1, b2 = 1.0, -2.0 * cos_w0, 1.0
    a0, a1, a2 = 1.0 + alpha, -2.0 * cos_w0, 1.0 - alpha
    b0, b1, b2 = b0 / a0, b1 / a0, b2 / a0
    a1, a2 = a1 / a0, a2 / a0
    y = np.zeros_like(x)
    for n in range(len(x)):
        x1 = x[n - 1] if n >= 1 else 0.0
        x2 = x[n - 2] if n >= 2 else 0.0
        y1 = y[n - 1] if n >= 1 else 0.0
        y2 = y[n - 2] if n >= 2 else 0.0
        y[n] = b0 * x[n] + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
    return y


def clean(in_path, out_path, sidecar) -> dict:
    fs = _sampling_frequency(sidecar)
    raw = _read_signal(in_path)
    filtered = notch(highpass(raw, fs, HIGHPASS_HZ), fs, NOTCH_HZ, NOTCH_Q)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    np.savetxt(out_path, filtered, fmt="%.4f")
    return {
        "fs": fs,
        "n_samples": int(raw.size),
        "highpass_hz": HIGHPASS_HZ,
        "notch_hz": NOTCH_HZ,
        "output": str(out_path),
    }


def _report(info: dict) -> None:
    print(
        f"cleaned {info['n_samples']} samples @ {info['fs']} Hz "
        f"(high-pass {info['highpass_hz']} Hz, notch {info['notch_hz']} Hz) "
        f"-> {info['output']}"
    )


# Snakemake injects a module-level `snakemake` object (its script runner does
# not guarantee __name__ == "__main__"), so detect it here rather than in a
# __main__ guard.
if "snakemake" in globals():
    _report(clean(
        snakemake.input.signal,      # noqa: F821
        snakemake.output[0],         # noqa: F821
        snakemake.input.sidecar,     # noqa: F821
    ))
elif __name__ == "__main__":
    # Standalone run from the repo root.
    _report(clean(
        "data/raw/sub-01/eeg/sub-01_task-rest_eeg.txt",
        "data/derivatives/demo/sub-01/sub-01_task-rest_desc-clean_eeg.txt",
        "data/raw/sub-01/eeg/sub-01_task-rest_eeg.json",
    ))
