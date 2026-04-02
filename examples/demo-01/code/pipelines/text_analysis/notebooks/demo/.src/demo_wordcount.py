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
# # Demo: Word frequency pipeline results
#
# Display summary outputs from the text_analysis/wordcount module.

# %%
from pathlib import Path

# %% [markdown]
# ## Read summaries

# %%
deriv = Path("derivatives/text_analysis/wordcount")
summaries = sorted(deriv.glob("*/*_task-read_wordcount.summary.txt"))

for summary_path in summaries:
    print(summary_path.read_text())
    print()

# %% [markdown]
# ## Load JSON and show top words per subject

# %%
import json

for sub_dir in sorted(deriv.iterdir()):
    json_file = next(sub_dir.glob("*_wordcount.json"), None)
    if json_file:
        data = json.loads(json_file.read_text())
        top5 = sorted(data.items(), key=lambda x: -x[1])[:5]
        print(f"{sub_dir.name}: {', '.join(f'{w}({c})' for w, c in top5)}")
