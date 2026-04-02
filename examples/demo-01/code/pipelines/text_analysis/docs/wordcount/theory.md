# wordcount — Theory

## Background

Word frequency analysis is a foundational technique in computational
linguistics. [@zipf1949] established that the frequency of a word in
natural language is inversely proportional to its rank in the frequency
table — a relationship known as Zipf's law.

## Method

1. Tokenize text by whitespace after lowercasing
2. Count occurrences of each token
3. Rank tokens by frequency (descending)

The resulting rank–frequency distribution can be visualized on log-log
axes; a linear relationship with slope ≈ −1 confirms Zipf's law.
