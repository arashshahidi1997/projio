#!/usr/bin/env python3
"""Generate cumulative build-up stages of diagram.svg for the talk.

Single source of truth is diagram.svg (all blocks visible). Each stage reveals
a cumulative set of block groups, bottom-up, following the talk's narrative,
with the newest block highlighted. Hidden blocks keep their layout slot so
nothing shifts between stages.

Run:  python build-diagram.py   (from this directory)
"""
from pathlib import Path

HERE = Path(__file__).parent
MASTER = (HERE / "diagram.svg").read_text()

# Every group id in the diagram, so we can hide the complement of "shown".
ALL = [
    "g-agent", "g-execarrow", "g-projio",
    "g-ground", "g-biblio", "g-code",
    "g-life", "g-notebooks", "g-promote", "g-pipelines", "g-render",
    "g-publication", "g-plant-seed", "g-plant-sprout", "g-plant-fruit",
    "g-datalad", "g-bids",
]

# Cumulative reveal order (each stage ADDS to the previous). (added, hot)
STEPS = [
    (["g-bids"], ["g-bids"]),                                             # 1 data
    (["g-ground", "g-code"], ["g-code"]),                                 # 2 code
    (["g-biblio"], ["g-biblio"]),                                         # 3 literature
    (["g-datalad", "g-life", "g-pipelines", "g-plant-sprout"],
     ["g-pipelines", "g-datalad"]),                                       # 4 reproducible
    (["g-notebooks", "g-promote", "g-plant-seed"], ["g-notebooks"]),      # 5 exploration
    (["g-render", "g-publication", "g-plant-fruit"], ["g-publication"]),  # 6 reporting
    (["g-projio", "g-execarrow", "g-agent"], ["g-agent"]),                # 7 full picture
]


def css_for(shown, hot):
    hidden = [g for g in ALL if g not in shown]
    rules = []
    if hidden:
        rules.append(",".join(f"#{g}" for g in hidden) + "{opacity:0;}")
    if hot:
        rules.append(",".join(f"#{g}" for g in hot) + "{filter:url(#glow);}")
    return "\n    ".join(rules)


# Spotlight recap: one component lit (glow), everything else dimmed. The flow
# walks the stack bottom-up as a closing "mention each piece" sequence.
SPOTS = [
    ["g-bids"],
    ["g-datalad"],
    ["g-code"],
    ["g-biblio"],
    ["g-notebooks", "g-plant-seed"],
    ["g-pipelines", "g-plant-sprout"],
    ["g-publication", "g-plant-fruit"],
    ["g-agent", "g-projio", "g-execarrow"],
]


def spot_css(lit):
    dim = [g for g in ALL if g not in lit]
    rules = [",".join(f"#{g}" for g in dim) + "{opacity:0.14;}"]
    rules.append(",".join(f"#{g}" for g in lit) + "{filter:url(#glow);}")
    return "\n    ".join(rules)


def main():
    shown = []
    for i, (added, hot) in enumerate(STEPS, start=1):
        shown += added
        svg = MASTER.replace("/*STAGECSS*/", css_for(shown, hot))
        (HERE / f"stage-{i}.svg").write_text(svg)
        print(f"wrote stage-{i}.svg  (shown={len(shown)}/{len(ALL)}, hot={hot})")
    for i, lit in enumerate(SPOTS, start=1):
        svg = MASTER.replace("/*STAGECSS*/", spot_css(lit))
        (HERE / f"spot-{i}.svg").write_text(svg)
        print(f"wrote spot-{i}.svg  (lit={lit})")


if __name__ == "__main__":
    main()
