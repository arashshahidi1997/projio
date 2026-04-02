# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Investigate Zipf's law in wordcount outputs
#
# Load JSON word frequency outputs from the text_analysis pipeline,
# compute Zipf rank, and check whether the rank–frequency distribution
# follows the expected power law.

# %%
import json
from pathlib import Path

import textlib

# %% [markdown]
# ## Load word frequencies

# %%
deriv = Path("derivatives/text_analysis/wordcount")
subjects = sorted(p.parent.name for p in deriv.glob("*/*_task-read_wordcount.json"))

all_freqs: dict[str, int] = {}
for sub in subjects:
    data = json.loads((deriv / sub / f"{sub}_task-read_wordcount.json").read_text())
    for word, count in data.items():
        all_freqs[word] = all_freqs.get(word, 0) + count
    print(f"{sub}: {len(data)} unique words")

print(f"\nCombined: {len(all_freqs)} unique words, {sum(all_freqs.values())} total")

# %% [markdown]
# ## Compute Zipf rank table

# %%
ranked = textlib.zipf_rank(all_freqs)

print(f"{'Rank':>4s}  {'Word':<20s}  {'Count':>5s}")
print("-" * 35)
for word, count, rank in ranked[:20]:
    print(f"{rank:4d}  {word:<20s}  {count:5d}")

# %% [markdown]
# ## Check Zipf's law
#
# For a Zipf distribution, rank × frequency ≈ constant.

# %%
print(f"\n{'Rank':>4s}  {'Freq':>5s}  {'Rank×Freq':>10s}")
print("-" * 25)
for word, count, rank in ranked[:10]:
    print(f"{rank:4d}  {count:5d}  {rank * count:10d}")
