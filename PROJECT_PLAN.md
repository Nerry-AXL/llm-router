# LLM Router - Full Implementation Plan

**Current Status:** P3 Data Audit → Moving to P4 Validation & Baselines  
**Target Completion:** 2026-11-10  
**GitHub:** https://github.com/Nerry-AXL/llm-router

## Phase Overview

We've completed the feasibility test (P4 early validation) showing TF-IDF + logistic regression runs in 0.011ms p95, well under the 10ms Worker CPU limit.

Now we build the full system following the KEAL framework.

---

## Completed ✅

- ✅ Feasibility test: Worker CPU test PASSED (0.011ms p95)
- ✅ Repository created on GitHub
- ✅ Notion updated with GitHub URL
- ✅ Master AI Product Brief drafted in Notion

---

## Current Phase: P4 Validation & Baselines

### Tasks (Next 2-3 days)

1. **Dataset Assembly** (Day 1)
   - [ ] Download and validate public benchmark datasets:
     - GSM8K (math, 100 samples)
     - MBPP or HumanEval (code, 100 samples)
     - ARC-Challenge (reasoning, 100 samples)
     - Create 100 chat prompts (general)
   - [ ] Verify licenses and document in `datasets/LICENSE.md`
   - [ ] Create sampling script with stratification
   - [ ] Generate `datasets/prompts.jsonl` (400 prompts)

2. **Evaluation Runner** (Day 1-2)
   - [ ] Build `evaluation/runner.py`:
     - Token-aware rate limiter (respect 200K tokens/day)
     - Cache responses to avoid re-running
     - Resume capability from JSONL cache
     - Retry with exponential backoff
   - [ ] Test with 20-prompt pilot
   - [ ] Measure actual tokens per call
   - [ ] Update token budget estimate

3. **Baseline Measurement** (Day 2-3)
   - [ ] Run all 400 prompts through BOTH models:
     - Groq gpt-oss-20b (small)
     - Groq gpt-oss-120b (large)
   - [ ] Cache all responses in `evaluation/cache.jsonl`
   - [ ] Build graders:
     - Exact match for math/reasoning/code
     - LLM judge (qwen3.8-27b) for chat
   - [ ] Compute baseline metrics:
     - Always-large quality score
     - Always-small quality score
     - Cost per 1K queries for each

4. **Heuristic Router** (Day 3)
   - [ ] Implement length + keyword heuristic baseline
   - [ ] Evaluate offline from cache
   - [ ] Document performance vs baselines
   - [ ] This becomes the baseline to beat

---

## Next Phase: P5 System Build (Week 2)

### Core Infrastructure

1. **Classifier Training**
   - [ ] Extract features from prompts (TF-IDF)
   - [ ] Label as easy/hard based on model performance
   - [ ] Train logistic regression classifier
   - [ ] Export to JSON weights for Worker
   - [ ] Validate classification accuracy

2. **Cloudflare Worker**
   - [ ] Project setup: `wrangler init`
   - [ ] Implement classifier inference (pure JS)
   - [ ] Benchmark CPU time (must be <10ms)
   - [ ] Groq API integration
   - [ ] Routing logic with confidence thresholds
   - [ ] Error handling and fallbacks

3. **Demo UI (Cloudflare Pages)**
   - [ ] Static site setup
   - [ ] Query interface
   - [ ] Results display with routing metadata
   - [ ] Results tab with benchmark charts
   - [ ] Budget indicator
   - [ ] Recorded examples fallback

---

## Phase: P6 UX-Model Integration (Week 2-3)

1. **Guardrails & Limits**
   - [ ] Per-visitor rate limiting (KV store)
   - [ ] Global daily budget tracking
   - [ ] Input validation and sanitization
   - [ ] Privacy notice
   - [ ] Fallback to recorded results

2. **Cost Tracking**
   - [ ] Log every routing decision
   - [ ] Calculate estimated costs
   - [ ] Export cost analytics

---

## Phase: P7 Shadow Evaluation (Week 3)

1. **Full Evaluation**
   - [ ] Run complete offline evaluation
   - [ ] Generate Pareto curve (cost vs quality)
   - [ ] Compare heuristic vs learned router
   - [ ] Measure routing accuracy on test set
   - [ ] Document confidence calibration

2. **Visualization**
   - [ ] Cost savings charts (80/20, 60/40, 40/60 mixes)
   - [ ] Quality retention vs baseline
   - [ ] Router overhead (latency added)
   - [ ] Routing accuracy by category

---

## Phase: P8 Documentation & Shipping

### ADRs (Architecture Decision Records)

1. **ADR-001: Two-tier vs Three-tier Routing**
   - Context: Model tier selection
   - Decision: Two-tier (gpt-oss-20b, gpt-oss-120b)
   - Rationale: 2x price gap limits savings; adding third tier increases complexity
   - Cost: Max theoretical savings capped at ~50%

2. **ADR-002: TF-IDF vs Embedding Classifier**
   - Context: Classification approach for Worker
   - Decision: TF-IDF + logistic regression
   - Rationale: Fits in 10ms CPU budget; embeddings would require external API
   - Cost: Lower accuracy than embedding-based approach

3. **ADR-003: Groq vs Other Providers**
   - Context: LLM API provider selection
   - Decision: Groq with fallback to OpenRouter
   - Rationale: Free tier, fast inference, both models in same family
   - Cost: 200K token/day limit requires multi-day evaluation

### Threat Model

- [ ] Prompt injection through router
- [ ] Demo quota exhaustion abuse
- [ ] API key exposure
- [ ] Data sent to third-party (Groq)
- [ ] Cache poisoning (not applicable - no cache in v1)
- [ ] Misrouting leading to poor quality

### Operations Guide

- [ ] What to monitor:
  - Tier usage mix (% small vs large)
  - Escalation rate (low confidence → large)
  - Tokens used per day
  - Error rates by provider
  - Router latency (p50/p95)
- [ ] How to roll back:
  - Route 100% to large model
  - Update confidence threshold
  - Deploy previous Worker version
- [ ] Failure modes:
  - Provider outage → fallback chain
  - Budget exhausted → recorded results
  - Classifier error → default to large model

### README

- [ ] Architecture diagram (Mermaid)
- [ ] One-command local setup
- [ ] Live demo link
- [ ] Benchmark results table
- [ ] Cost savings by traffic mix
- [ ] Routing accuracy
- [ ] Router overhead
- [ ] Limitations and failure modes
- [ ] ADRs linked
- [ ] Threat model linked
- [ ] KEAL gates evidence

---

## Timeline Estimate

**Week 1 (Current):**
- Days 1-3: Dataset assembly and baseline measurement (P4)
- Days 4-5: Heuristic router baseline
- Weekend: Classifier training

**Week 2:**
- Days 1-3: Worker implementation and testing (P5)
- Days 4-5: Demo UI build (P6)
- Weekend: Integration testing

**Week 3:**
- Days 1-2: Full evaluation and charts (P7)
- Days 3-4: Documentation (ADRs, threat model, ops guide)
- Day 5: README polish and demo testing
- Weekend: Final review and ship

**Total: ~15-18 days** (target: Nov 10, 2026)

---

## Risk Mitigations

1. **Token Budget Risk**
   - Mitigation: Run pilot first, cache aggressively, spread over days
   - Fallback: Smaller dataset (300 instead of 400)

2. **Worker CPU Limit**
   - Mitigation: Already tested at 0.011ms, 900x headroom
   - Fallback: Smaller vocabulary if needed

3. **Groq API Changes**
   - Mitigation: Keep model names in config, document date
   - Fallback: OpenRouter or other compatible provider

4. **Learned Router Not Better Than Heuristic**
   - Mitigation: This is acceptable! Publish honest results
   - Message: "AI necessity justified by trying; heuristic won"

---

## Success Criteria

- ✅ All KEAL gates passed with evidence
- ✅ Live demo deployed and working
- ✅ README complete with all required sections
- ✅ Reproducible evaluation (committed cache + script)
- ✅ Cost claims backed by measurements
- ✅ Quality metrics honest (with confidence intervals)
- ✅ Repository pinned on GitHub profile

---

## Next Immediate Actions

1. Create `datasets/` directory
2. Write dataset sampling script
3. Download and validate public benchmarks
4. Build evaluation runner
5. Run 20-prompt pilot

Let's start! 🚀
