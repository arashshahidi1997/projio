# Strict raw root

**Status:** draft

!!! note "Sources & anchors"
    - **Stack component:** BIDS
    - **Canonical artifact:** `pixecog/raw/` (survey component 1)
    - **Workshop session:** Day-1 AM session 1 (BIDS)
    - **Outline:** [`_outline.md`](../_outline.md) §B
    - **Port source:** `teaching/NeuroPySeminar/docs/slides/bootcamp-ii/tutorial-plan.md (steps 3, 5)` (NeuroPySeminar — needs refresh for current stack)

## Frame

`participants.tsv` + `dataset_description.json` + `sub-XX/`; the directory layout *is* the API.

## The thesis

The directory layout is the API. That phrase is worth taking literally. A
script that knows BIDS can find any subject's session-two intracranial
recording at `sub-XX/ses-02/ieeg/sub-XX_ses-02_ieeg.extension` without
reading a project configuration file, without calling an inventory function,
and without asking the person who ran the experiment. The convention absorbs
the configuration. Two separate pipelines, two separate authors, two separate
computing clusters — all navigate the same `raw/` tree identically. The power
is not in any individual file; it is in the agreement on where every file
lives.

## The minimal valid BIDS root

Three things make a directory a BIDS raw root:

**`dataset_description.json`** at the top level. This file names the dataset
and declares the BIDS version. It is the handshake: any BIDS-aware tool reads
it first to know what version of the spec to apply. The full schema has
optional fields for authors, license, DOI, ethics approval, and funding, but
the validator only requires `Name` and `BIDSVersion`.

**`participants.tsv`** — a tab-separated table with one row per subject and
`participant_id` in the first column. Every other column is free-form metadata
that travels with the dataset. In pixecog, `participants.tsv` carries surgical
metadata (implant hemisphere, device identifiers, surgery dates, electrode
coordinates, weight) that would otherwise live in a lab notebook or a
per-session script comment. Once it is in the TSV, every downstream pipeline
can join on subject ID without querying a separate system.

**`sub-XX/` directories** — one per subject, organised into sessions (`ses-YY/`)
and then datatypes. The path from subject to file is a lookup, not a search.

## pixecog/raw as the canonical example

pixecog's raw root (`pixecog/raw/`) demonstrates the pattern at research-lab
scale:

```
raw/
├── dataset_description.json    # BIDSVersion 1.10.0 + HEDVersion 8.2.0
├── participants.tsv             # 5 subjects (sub-01..05) + sub-test
├── participants.json            # column descriptions for participants.tsv
├── tasks.json                   # task-level metadata for recording sessions
├── registry.yml                 # projio-layer: pipeio source registry
├── sub-01/
│   ├── sub-01_sessions.tsv      # per-session summary for sub-01
│   ├── sub-01_sessions.json     # column descriptions
│   ├── sub-01_probes.tsv        # electrode probe metadata
│   └── ses-04/
│       ├── ecephys/             # extracellular electrophysiology (Neuropixels)
│       ├── ieeg/                # intracranial EEG (ECoG grid)
│       ├── motion/              # motion tracking
│       └── ttl/                 # TTL trigger signals
├── sub-02/  ...
└── sub-test/
```

The sidecar pattern runs at every level. Every data file has a matching JSON
sidecar: `sub-01_ses-04_ieeg.json` holds channel count, sampling rate, and
electrode reference. The sidecar is how BIDS carries per-file metadata without
embedding it in the binary. It also makes the metadata machine-readable without
parsing the binary file — a script can build a session inventory entirely from
TSV and JSON files.

## What the layout gives you for free

**Path resolution without configuration.** Snakebids's `generate_inputs()`
reads the BIDS root and enumerates every subject, session, and run, populating
Snakemake wildcards automatically. Adding a sixth subject to `raw/` — creating
the `sub-06/` directory — is enough; the Snakefile does not change.

**Scanner-portable code.** The same Snakefile that processes pixecog's ECoG
recordings will process gecog's ECoG recordings if the BIDS layout is
consistent, because the script addresses files by wildcards (`{subject}`,
`{session}`, `{datatype}`) rather than hard-coded paths. The layout contracts
replace per-project glue.

**Self-describing provenance.** A new collaborator who clones only `raw/` can
reconstruct what was recorded, when, and under what conditions by reading
`dataset_description.json`, `participants.tsv`, and the sidecar JSONs. The
metadata travels with the data.

**Tool compatibility.** BIDS Layout libraries (PyBIDS, MNE-BIDS) and standard
viewers understand the structure immediately. The ecosystem investment in BIDS
tooling is accessible for free.

## The honest gap

BIDS validation in this cohort is not mechanically enforced. pixecog's
`dataset_description.json` declares `BIDSVersion: 1.10.0`, but some fields
(authors, DOI) are blank placeholders; a strict validator pass would flag
these. Across the three study projects (pixecog, gecog, msol), no CI hook or
DataLad save hook currently runs `bids-validator`. The convention is the
guide; enforcement is social.

The workshop demonstrates `bids-validator` as a sanity check — `bids-validator
raw/` from the dataset root — without implying it must pass clean before every
pipeline run. A partial pass is normal at active development time.

Derivative directories are a sharper case: pixecog's `derivatives/preprocess_ieeg/`
has no `dataset_description.json` at its root, so it is not BIDS-valid as a
derivative dataset. That is a deliberate tradeoff, discussed in
[Derivatives and manifest](derivatives-and-manifest.md) and catalogued in
[Honest gaps](../99-honest-gaps.md) §1.

## Further reading

- **[BIDS specification](https://bids-specification.readthedocs.io/)** — canonical source for all entity names, sidecar requirements, and `dataset_description.json` fields.
- **[bids-validator](https://github.com/bids-standard/bids-validator)** — run `bids-validator raw/` to catch layout violations; JavaScript and Python variants available.
- **[PyBIDS](https://pybids.readthedocs.io/)** — Python library for querying BIDS datasets; complement to snakebids for non-Snakemake code.
- **[MNE-BIDS](https://mne.tools/mne-bids/stable/index.html)** — BIDS-aware I/O for electrophysiology; handles sidecar creation from raw EEG/iEEG recordings.
