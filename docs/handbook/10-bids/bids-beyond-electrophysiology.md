# BIDS beyond electrophysiology

**Status:** draft

!!! note "Sources & anchors"
    - **Stack component:** BIDS
    - **Canonical artifact:** `msol/raw/` (survey component 1, msol row)
    - **Workshop session:** Day-1 AM session 1 sidebar
    - **Outline:** [`_outline.md`](../_outline.md) §B

## Frame

BIDS for video / behavior; what generalizes, what doesn't.

## The question this chapter answers

The previous two chapters draw on pixecog — a project with intracranial EEG
and Neuropixels recordings — as the canonical BIDS example. Every study in
the cohort that uses BIDS adopts the same `raw/` root structure with
`participants.tsv`, `dataset_description.json`, and `sub-XX/ses-YY/` paths.
The question is whether that structure is specific to electrophysiology or
whether it is general enough to carry a different kind of experiment.

msol (Modality-Specific Object-Location Memory) is the test case. It records
rats during memory tasks — three cameras per session capturing different viewing
angles, a motion-tracking system, and behavioral event logs. No electrodes, no
neural signals at acquisition time. Its `raw/` is nonetheless valid BIDS.

## msol/raw as the beyond-ephys example

```
raw/
├── dataset_description.json        # MSOL name, BIDSVersion 1.11.1, CC-BY-4.0
├── participants.tsv                 # 6 subjects (sub-01..06)
├── participants.json
├── cameras.tsv                      # camera inventory: role, hardware label, FPS
├── cameras.json                     # column descriptions for cameras.tsv
├── task-multisensory_video.json     # behavioral task metadata (multisensory condition)
├── task-olfactory_video.json
├── task-tactile_video.json
├── sub-01/
│   └── ses-01/
│       ├── beh/
│       │   ├── sub-01_ses-01_task-multisensory_run-01_recording-tiltA_video.avi
│       │   ├── sub-01_ses-01_task-multisensory_run-01_recording-tiltA_video.json
│       │   ├── sub-01_ses-01_task-multisensory_run-01_recording-tiltB_video.avi
│       │   └── ...                  # 3 camera angles × multiple runs
│       └── motion/
│           ├── sub-01_ses-01_task-multisensory_run-01_motion.tak
│           └── sub-01_ses-01_task-multisensory_run-01_motion.json
└── sub-02/ ...
```

The directory grammar is identical to pixecog's. `sub-01/ses-01/` holds
datatypes; the filenames are BIDS entity chains (`sub-`, `ses-`, `task-`,
`run-`, `recording-`); each data file has a JSON sidecar. The experiment type
changed; the layout convention did not.

## What generalizes

**The path grammar generalizes fully.** `sub-XX/ses-YY/datatype/filename` is
domain-neutral. `beh/` and `motion/` are valid BIDS datatypes. The
`_recording-<label>` entity distinguishes camera viewpoints (`tiltA`, `tiltB`,
`top`) in a way that follows the BIDS entity chain pattern.

**The sidecar pattern generalizes fully.** Every data file has a corresponding
JSON sidecar. `sub-01_ses-01_task-multisensory_run-01_recording-tiltA_video.json`
carries camera-specific parameters for that file (frame rate, resolution,
viewpoint). The same join-on-filename logic that works for EEG sidecars
works here.

**Top-level tabular metadata generalizes.** `participants.tsv` holds per-subject
metadata (age, sex, cohort). Task-level JSONs (`task-multisensory_video.json`)
describe the behavioral paradigm. These are standard BIDS mechanisms that apply
to any modality.

**Custom tabular files follow the same sidecar pattern.** `cameras.tsv` and
`cameras.json` are not part of the BIDS specification, but they follow the
same convention (TSV data + JSON column descriptions) that BIDS uses throughout.
Adding project-specific tabular metadata alongside the standard files does not
break the directory grammar — it extends it in the same idiom.

## What doesn't generalize

**Modality-specific schemas.** BIDS has richly specified schemas for EEG (`_channels.tsv`,
`_electrodes.tsv`, `_eeg.json`), fMRI (`_bold.nii.gz` + `_events.tsv`), and
iEEG (`_ieeg.json` with required fields for electrode reference and
amplifier gain). For video and DeepLabCut pose estimation there is no
equivalent canonical schema. msol's `derivatives/dlc_pose/` is a plain output
directory; the BIDS validator doesn't know what to do with `.h5` keypoint
files or DLC config JSONs.

**Validator completeness.** The BIDS video extension (BEP024) is not yet merged
into the main specification. Running `bids-validator` on msol's `raw/` will
flag the `_recording-*` entity in `beh/` as unknown and may warn about the
`_video` suffix. These are not errors in the project's convention; they are
gaps in the spec. The validator feedback is educational — it shows what the
specification currently covers — but it is not authoritative for novel modalities.

## When to fork a micro-convention vs wait for a BEP

The practical rule: use BIDS path grammar always; use BIDS schemas where they
exist; add custom sidecar JSON for anything the schema doesn't cover.

If a BIDS Extension Proposal (BEP) is actively being developed for your
modality, using its draft conventions (even before merge) keeps you compatible
with the emerging standard and lets you contribute feedback. If the BEP is
stalled or absent, invent a local sidecar convention that follows BIDS idioms —
TSV + JSON column descriptions, entity-chain filenames, top-level tabular
metadata — and document it in the `dataset_description.json` `GeneratedBy`
field.

msol follows this rule: `beh/` datatype and `_recording-*` entity are used
because BEP024 (video) hasn't landed yet, but they are the closest-fit choices
within the existing entity vocabulary. The path grammar is BIDS; the file-type
schema is local. When BEP024 eventually ships, the path grammar will stay the
same and only the validator interpretation will change.

The source dataset relationship is also worth noting. msol's `raw/` was
produced by a bidsification script (`code/scripts/bidsify/convert.py`) from a
separate source dataset (`ds-msol` at `file:///storage2/arash/data/ds-msol`).
The `dataset_description.json` records this in `SourceDatasets` and
`GeneratedBy`. This is the correct pattern for any dataset where the raw
acquisition files are not directly BIDS-formatted: maintain the archive
separately, convert to BIDS layout via a documented script, and record the
provenance in `dataset_description.json`. The `raw/` tree is then the
validated representation, not the primary archive.

## Further reading

- **[BIDS Extension Proposals](https://bids-specification.readthedocs.io/en/stable/extensions.html)** — active proposals extending BIDS to video (BEP 024), microscopy, MEG, and other modalities.
- **[BIDS starter kit](https://bids-standard.github.io/bids-starter-kit/)** — annotated examples and templates for adopting BIDS in a new modality.
