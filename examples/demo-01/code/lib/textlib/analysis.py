from collections import Counter


def word_frequencies(text: str) -> dict[str, int]:
    """Count word frequencies in text."""
    return dict(Counter(text.lower().split()))


def zipf_rank(frequencies: dict[str, int]) -> list[tuple[str, int, int]]:
    """Return (word, count, rank) sorted by frequency descending."""
    sorted_words = sorted(frequencies.items(), key=lambda x: -x[1])
    return [(word, count, rank + 1) for rank, (word, count) in enumerate(sorted_words)]
