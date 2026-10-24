# Evaluation Infrastructure

## Overview

This directory contains the evaluation infrastructure for the LLM Router project.

## Files

- `runner.py` - Main evaluation script with rate limiting and caching
- `cache/` - Cached API responses (auto-created)
- `grader.py` - Response grading logic (TODO)
- `analyze.py` - Analysis and visualization (TODO)

## Quick Start

### 1. Set Up Environment

```bash
# Install dependencies
pip install requests

# Get Groq API key from https://console.groq.com/keys
export GROQ_API_KEY=your_key_here
```

### 2. Generate Dataset

```bash
cd ../datasets
python sample_datasets.py
```

This creates `datasets/prompts.jsonl` with 400 prompts.

### 3. Run Pilot (20 prompts)

```bash
python runner.py --model groq-20b --limit 20
```

This tests the setup and measures actual token usage.

### 4. Run Full Evaluation

```bash
# Small model
python runner.py --model groq-20b

# Large model (after small completes)
python runner.py --model groq-120b
```

## Token Budget Management

**Groq Free Tier Limits:**
- 200,000 tokens/day
- 30 requests/minute

**Strategy:**
- Conservative estimate: 500 tokens/request
- 400 prompts × 500 tokens = 200K tokens (fits in 1 day)
- Runner automatically tracks usage in `cache/token_budget.json`
- Resets daily at midnight

**If you hit the limit:**
- Script will stop and resume automatically next day
- Cache preserves completed work
- No need to re-run successful prompts

## Cache Format

Responses are cached in `cache/{model}_responses.jsonl`:

```json
{
  "id": "gsm8k_0",
  "category": "math",
  "prompt": "If 5 apples cost $10, how much do 12 apples cost?",
  "response": "To find the cost...",
  "model": "groq-20b",
  "usage": {
    "prompt_tokens": 23,
    "completion_tokens": 145,
    "total_tokens": 168
  },
  "timestamp": "2026-10-24 14:30:00"
}
```

## Resume Capability

The runner automatically resumes from where it left off:

1. Loads existing cache
2. Skips prompts already in cache
3. Continues with remaining prompts
4. Updates token budget

No special flags needed - just run the same command again.

## Dry Run Mode

Test without API calls:

```bash
python runner.py --model groq-20b --limit 20 --dry-run
```

This shows:
- Which prompts would be called
- Which are already cached
- Token budget status

## Expected Timeline

**Pilot (20 prompts):**
- Time: ~2 minutes
- Tokens: ~10,000
- Purpose: Validate setup

**Full run (400 prompts per model):**
- Time: ~30 minutes per model
- Tokens: ~200K per model
- Total: 2 days (1 model per day)

## Troubleshooting

**Error: `GROQ_API_KEY` not set**
```bash
export GROQ_API_KEY=your_key_here
```

**Error: `requests` module not found**
```bash
pip install requests
```

**Error: Rate limit exceeded**
- Wait 1 minute
- Runner will retry automatically

**Error: Token budget exhausted**
- Wait until next day (midnight UTC)
- Cache preserved, just re-run

## Next Steps

After both models complete:

1. Build grader (`grader.py`)
2. Compute baseline metrics
3. Train classifier on results
4. Build heuristic router baseline

## Files Created

```
evaluation/
├── runner.py              # Main evaluation script
├── cache/
│   ├── groq-20b_responses.jsonl    # Small model responses
│   ├── groq-120b_responses.jsonl   # Large model responses
│   └── token_budget.json           # Token usage tracker
└── README.md              # This file
```
