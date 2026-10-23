# Project context (read this first, every session)

This repo is one of 5 flagship portfolio projects for a GitHub profile aimed at an AI engineer / CTO path. The profile must show production engineering, system architecture, cost optimization and security, through decisions and measured evidence, not feature lists.

The owner works in the KEAL framework (Koukoui Enterprise AI Lifecycle): four gates (Discovery, Feasibility, Development, Governance), each needing a self sign-off backed by an evidence link. Notion is the source of truth for tasks and status (links below).

## Hard constraints
1. **Free tiers only.** Never add a paid service, a paid dependency, or a step that needs a payment method. If something seems to need paying, stop and propose a free alternative.
2. **No secrets** in the repo, frontend bundles, logs or commits. Use `.env.example`, platform secret stores and a pre-commit secret scan (gitleaks).
3. **Never fabricate or round up numbers.** Every figure in the README or docs must trace to committed data or a logged run. Label estimates as estimates. Record the date for every price or limit.
4. Provider limits and model names live in **config**, not in code.
5. **Never run model-generated or untrusted code on the host.** Use an isolated container with no network.
6. Use **synthetic data only** for anything resembling personal data.

## How to work
- Start each session by reading this file and `docs/`. Check the Notion Build Tasks for this project (if the Notion connector is available) and take the lowest-order "To do" task.
- Run feasibility tests first. If one fails, stop and report before building on that assumption.
- For architecture-impacting choices, write a short ADR in `docs/adr/` (context, options, decision, cost) and ask the owner before committing to it.
- Prefer the smallest implementation that passes the test. Keep commits small with clear messages.
- Write tests. Where it makes sense, the local dev path is one command (Docker Compose or a make target).
- A task is **Done only with evidence**: a commit, test output, chart or run log. Put the link in the Notion task's Evidence URL.
- If unsure about a provider limit or API detail, check the official docs and say what you verified. Anything marked **VERIFY** must be confirmed before you rely on it.
- When using the Notion connector: set Status to "In progress" when you start a task, "Done" (plus Evidence URL) when finished, and put decisions in Notes. Never delete rows.

## Required in every repo
README (live demo link at the top, architecture diagram, results, cost table, limitations), `docs/adr/`, `docs/threat-model.md`, `docs/ops.md` (monitoring, rollback), `docs/keal-gates.md` (gates passed, with evidence links).

## Demo rules
The live demo shows its evidence, has a graceful fallback for every failure and budget state, shows a privacy notice, and enforces rate limits. It never shows a raw error page.

Notion links: Command Center https://app.notion.com/p/3fde9a5ffec081a4b7c4f59a7092dba7 , Build Tasks https://app.notion.com/p/0043b09ab6e047c9b90ab8662936e183

---

# Project: Intelligent Multi-Tier LLM Model Router
Notion page (full brief, sections 1-23): https://app.notion.com/p/3fde9a5ffec0814eb176d05380d96c36

## Goal
Route each query to a small or large model so cost falls while quality stays near the always-large baseline, and publish honest, measured numbers. Live demo on Cloudflare (Pages UI + Worker API).

## Models (Groq, OpenAI-compatible API; verify base URL in Groq docs)
- Small: `openai/gpt-oss-20b`. Large: `openai/gpt-oss-120b`. Judge (chat category only): `qwen/qwen3.8-27b`.
- Free-tier limits per model (from the Groq console, Oct 2026): 30 req/min, 1K req/day, 8K tokens/min, 200K tokens/day. Tokens/day is the real ceiling. Reasoning tokens count. Keep these in config and re-check the console.
- Token prices were roughly 2x apart (VERIFY on console). Maximum savings are bounded by that ratio, so the original "60-80% savings" idea is NOT a target. Report measured savings only.

## Evaluation design (core idea)
Run every prompt through both models once, cache every response, then simulate any routing policy offline by picking the cached answer. The full cost-vs-quality curve costs zero extra API calls.
- 400 prompts: 100 math (GSM8K), 100 code (MBPP or HumanEval), 100 reasoning (ARC-Challenge or MMLU subset), 100 general chat. Check dataset licenses first.
- Graders: exact match (math, multiple choice), unit tests run in an isolated container with no network (code), qwen judge plus manual spot-check of about 50 (chat).
- Split 70/30 stratified, fixed seed; use cross-validation. "Hard" label = small model fails where large passes.
- Cache record (JSONL): prompt_id, category, prompt, model, response, tokens_in, tokens_out, reasoning_tokens, latency_ms, grader, score, timestamp, prices_used.
- Runner: token-aware rate limiter, resume from cache, retry with backoff (failed requests may count against limits).
- Disclose: possible benchmark contamination, small test set (report confidence intervals), judge bias, dates of prices and limits.

## Worker constraints
Cloudflare free Workers: about 100K requests/day and 10 ms CPU per request (VERIFY current docs). Waiting on Groq does not count as CPU. No PyTorch, no native dependencies. Classifier = TF-IDF + logistic regression trained in Python, exported as JSON weights, inference in plain JS. KV counters are eventually consistent, so per-visitor and global budgets are approximate (Durable Objects give exact counts, VERIFY free-plan availability).

## Suggested layout
eval/ (sample, run, graders, cache) | train/ (features, train, export_weights) | worker/ | web/ | data/ (prompts, cache, results) | docs/

## Success metrics (targets, to validate)
Quality retention >= 95% of always-large (stretch 97%); cost vs. quality Pareto curve; measured savings at 80/20, 60/40, 40/60 easy/hard mixes; router overhead p50/p95; routing accuracy on labeled set. Ablation: (1) heuristic, (2) TF-IDF classifier, (3) confidence-based escalation.

## Demo guardrails
Keep ~20% of the daily token budget in reserve; per-visitor cap (about 5/day); global daily budget (about 150 queries, tune after measuring); input length limit; no uploads; recorded-examples fallback when budget is spent or Groq errors; "budget left today" indicator; privacy notice (no sensitive data); optional bring-your-own-key box (session only, never logged); Results tab built from committed data.

## Task order (mirror in Notion Build Tasks)
1. Worker CPU test (feasibility, do this FIRST)  2. License check  3. Sampling script  4. Eval runner  5. Graders  6. 20-prompt pilot, recompute token budget  7. Full run (3-4 days)  8. Profile results  9. Heuristic + TF-IDF offline eval  10. Worker API + guardrails  11. UI + Results tab
