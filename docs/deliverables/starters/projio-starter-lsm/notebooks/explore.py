import marimo

__generated_with = "0.9.0"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    from pathlib import Path

    import numpy as np
    return Path, mo, np


@app.cell
def _(mo):
    mo.md(
        """
        # Explore: cleaned resting-state EEG

        A minimal reactive notebook over the demo pipeline output. Run the
        pipeline first:

        ```bash
        pixi run snakemake -s code/pipelines/demo/Snakefile --cores 1
        ```
        """
    )
    return


@app.cell
def _(Path):
    # notebooks/ sits at the repo root, so parent.parent is the project root.
    root = Path(__file__).resolve().parent.parent
    cleaned_path = root / "data" / "derivatives" / "demo" / "sub-01" / "sub-01_task-rest_desc-clean_eeg.txt"
    fs = 250.0  # Hz, per data/raw/sub-01/eeg/sub-01_task-rest_eeg.json
    return cleaned_path, fs, root


@app.cell
def _(cleaned_path, mo, np):
    if cleaned_path.exists():
        signal = np.loadtxt(cleaned_path, dtype=float)
        status = mo.md(f"Loaded **{signal.size}** samples from `{cleaned_path.name}`.")
    else:
        signal = np.array([])
        status = mo.md(
            "No cleaned signal yet. Run the pipeline, then re-run this cell."
        )
    status
    return signal, status


@app.cell
def _(fs, np, signal):
    # Moving-window RMS envelope + a simple mean + N-sigma burst threshold.
    def rms_envelope(x, win):
        if x.size == 0:
            return x
        power = np.convolve(x**2, np.ones(win) / win, mode="same")
        return np.sqrt(power)

    n_sigma = 4  # the idea note asks the agent to choose 3 vs 4
    envelope = rms_envelope(signal, win=max(1, int(0.05 * fs)))
    if envelope.size:
        threshold = envelope.mean() + n_sigma * envelope.std()
        n_bursts = int((np.diff((envelope > threshold).astype(int)) == 1).sum())
    else:
        threshold, n_bursts = 0.0, 0
    return envelope, n_bursts, n_sigma, threshold


@app.cell
def _(envelope, fs, np, signal, threshold):
    import matplotlib.pyplot as plt

    if signal.size:
        t = np.arange(signal.size) / fs
        fig, ax = plt.subplots(figsize=(8, 3))
        ax.plot(t, signal, lw=0.5, label="cleaned")
        ax.plot(t, envelope, lw=1.0, label="RMS envelope")
        ax.axhline(threshold, color="crimson", ls="--", lw=1.0, label="threshold")
        ax.set_xlabel("time (s)")
        ax.set_ylabel("uV")
        ax.legend(loc="upper right", fontsize=8)
        fig.tight_layout()
        out = fig
    else:
        out = None
    out
    return (plt,)


@app.cell
def _(mo, n_bursts, n_sigma, threshold):
    mo.md(
        f"""
        ## Summary

        - burst threshold: `mean + {n_sigma} sigma` = **{threshold:.2f} uV**
        - detected burst events: **{n_bursts}**

        Next step: write a result note in `docs/log/result/` citing the idea note
        (`source_note:`) and this notebook's finding.
        """
    )
    return


if __name__ == "__main__":
    app.run()
