# wordcount — I/O Contract

## Input

| Entity | Pattern | Format |
|--------|---------|--------|
| text | `raw/{sub}/{sub}_task-read_text.txt` | Plain text |

## Output

| Product | Pattern | Format |
|---------|---------|--------|
| json | `derivatives/text_analysis/wordcount/{sub}/{sub}_task-read_wordcount.json` | JSON dict: word → count |
| summary | `derivatives/text_analysis/wordcount/{sub}/{sub}_task-read_wordcount.summary.txt` | Human-readable rank table |

## Dependencies

- `textlib.word_frequencies` — tokenization and counting
- `textlib.zipf_rank` — rank ordering
