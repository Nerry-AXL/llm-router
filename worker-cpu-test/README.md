# Worker CPU Feasibility Test

## Goal
Verify that a TF-IDF vectorizer + logistic regression classifier can classify text prompts within Cloudflare Worker's 10ms CPU limit.

## What we're testing
- TF-IDF feature extraction from text (no external libraries)
- Logistic regression inference using pre-trained weights (plain JS)
- Total CPU time for end-to-end classification

## Success criteria
- Full classification (tokenize → TF-IDF → logistic regression → prediction) completes in < 10ms
- Works with vocabulary size ~1000-2000 terms
- Can handle prompts up to 500 tokens

## Non-goals
- Training (happens offline in Python)
- Perfect accuracy (that's evaluated separately)
- Handling edge cases (this is a speed test only)

## Test approach
1. Mock TF-IDF weights (vocabulary + IDF values) as JSON
2. Mock logistic regression weights as JSON
3. Implement inference in plain JavaScript
4. Benchmark with realistic prompt samples
5. Report p50, p95, p99 times

## Files
- `classifier.js` - TF-IDF + logistic regression implementation
- `test-data.json` - Sample prompts and mock weights
- `benchmark.js` - Timing harness
- `results.txt` - Benchmark output (to commit as evidence)
