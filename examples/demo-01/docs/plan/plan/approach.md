# Approach

We use a Python-based word counting pipeline managed by pipeio. The analysis
follows [@zipf1949] in ranking words by frequency and fitting a power-law model.

## Pipeline steps

1. Tokenize raw text files
2. Count word frequencies
3. Rank and fit power-law distribution
4. Generate summary statistics and figures
