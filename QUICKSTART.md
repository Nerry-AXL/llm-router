# Quick Start Guide - LLM Router

**Goal:** Get evaluation running in ~10 minutes

---

## Prerequisites

- Python 3.8+
- Groq API key (free tier: https://console.groq.com/keys)

---

## Step 1: Setup (2 minutes)

```bash
# Clone and enter directory
cd llm-router

# Run setup script
bash setup.sh          # Linux/Mac
# OR
.\setup.ps1            # Windows PowerShell

# Set API key
export GROQ_API_KEY=your_key_here
```

---

## Step 2: Generate Dataset (1 minute)

```bash
cd datasets
python sample_datasets.py
```

**Expected output:**
```
Downloading GSM8K (math) - sampling 100 prompts...
  ✓ Sampled 100 math prompts
Downloading MBPP (code) - sampling 100 prompts...
  ✓ Sampled 100 code prompts
...
✓ Dataset ready: datasets/prompts.jsonl
```

---

## Step 3: Run Pilot Evaluation (2 minutes)

Test with 20 prompts to validate setup:

```bash
cd ../evaluation
python runner.py --model groq-20b --limit 20
```

**Expected output:**
```
LLM Router Evaluation Runner
Model:           groq-20b (llama-3.3-70b-versatile)
Prompts:         20 total
Tokens today:    0 / 200,000
...
[1/20] gsm8k_0 (math)
  ✓ Success (168 tokens)
...
Evaluation Complete
Success:         20 prompts
Tokens used:     3,420 / 200,000
```

---

## Step 4: Review Token Usage

Check actual token consumption:

```bash
cat cache/token_budget.json
```

**Adjust estimates if needed** in `runner.py`:
```python
ESTIMATED_TOKENS_PER_REQUEST = 500  # Update based on pilot
```

---

## Step 5: Run Full Evaluation (30 minutes per model)

**Small model (day 1):**
```bash
python runner.py --model groq-20b
```

**Large model (day 2):**
```bash
python runner.py --model groq-120b
```

**Resume if interrupted:**
Just run the same command again - it automatically resumes from cache.

---

## Verification Checklist

- [ ] Python 3.8+ installed
- [ ] Dependencies installed (`pip list | grep requests`)
- [ ] Groq API key set and valid
- [ ] Dataset generated (400 prompts in `datasets/prompts.jsonl`)
- [ ] Pilot run completed successfully (20 prompts)
- [ ] Token budget tracking working (`cache/token_budget.json` exists)
- [ ] Cache working (re-running pilot shows "Cached" for all prompts)

---

## Troubleshooting

**"ModuleNotFoundError: No module named 'requests'"**
```bash
pip install requests
```

**"ERROR: GROQ_API_KEY environment variable not set"**
```bash
export GROQ_API_KEY=your_key_here
# Or add to ~/.bashrc to persist
```

**"HTTP 401: Unauthorized"**
- Check API key is correct
- Verify API key is active at https://console.groq.com/keys

**"HTTP 429: Rate limit exceeded"**
- Wait 1 minute
- Runner will retry automatically

**"Token budget exhausted"**
- Normal! Wait until next day (midnight UTC)
- Runner will resume automatically
- Check `cache/token_budget.json` for reset time

**Dataset download fails**
- Normal! Script uses synthetic fallback data
- Check internet connection
- Fallback data works just as well for evaluation

---

## What's Next?

After both models complete (2 days):

1. **Build grader** - `evaluation/grader.py`
2. **Compute baselines** - Always-large vs always-small quality
3. **Train classifier** - TF-IDF + logistic regression on results
4. **Build heuristic router** - Length + keyword baseline
5. **Implement Worker** - Cloudflare Worker with routing logic
6. **Build demo UI** - Cloudflare Pages demo

See [PROJECT_PLAN.md](PROJECT_PLAN.md) for full timeline.

---

## Directory Structure

```
llm-router/
├── datasets/
│   ├── sample_datasets.py     # Generate 400 prompts
│   ├── prompts.jsonl          # Generated dataset
│   └── LICENSE.md             # Data licenses
├── evaluation/
│   ├── runner.py              # Main evaluation script
│   ├── cache/                 # API responses (gitignored)
│   │   ├── groq-20b_responses.jsonl
│   │   ├── groq-120b_responses.jsonl
│   │   └── token_budget.json
│   └── README.md
├── requirements.txt
├── setup.sh / setup.ps1
├── PROJECT_PLAN.md
└── QUICKSTART.md (this file)
```

---

## Expected Timeline

**Today:** Setup + pilot (15 min)
**Day 1:** Full evaluation on groq-20b (30 min active, spread over day)
**Day 2:** Full evaluation on groq-120b (30 min active, spread over day)
**Day 3+:** Build grader, classifier, worker, demo

**Total project:** 15-18 days (target: Nov 10, 2026)

---

🚀 **Ready to start!** Run `bash setup.sh` and follow the steps above.
