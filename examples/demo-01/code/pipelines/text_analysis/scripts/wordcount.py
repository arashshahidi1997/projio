"""Snakemake script: count word frequencies in a text file.

Reads input text, computes word frequencies using textlib,
writes JSON counts and a human-readable summary.
"""
import json
from pathlib import Path

import textlib

input_path = Path(snakemake.input[0])
out_json = Path(snakemake.output.json)
out_summary = Path(snakemake.output.summary)

text = input_path.read_text()
freqs = textlib.word_frequencies(text)
ranked = textlib.zipf_rank(freqs)

# Write JSON output
out_json.parent.mkdir(parents=True, exist_ok=True)
out_json.write_text(json.dumps(freqs, indent=2, sort_keys=True))

# Write summary
lines = [f"Word frequency summary for {input_path.name}", "=" * 50, ""]
lines += [f"  {rank:3d}. {word:<20s} {count:4d}" for word, count, rank in ranked]
lines += ["", f"Total unique words: {len(freqs)}", f"Total words: {sum(freqs.values())}"]
out_summary.write_text("\n".join(lines) + "\n")
