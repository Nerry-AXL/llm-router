#!/usr/bin/env python3
"""
Evaluation Runner for LLM Router

Runs prompts through Groq API with:
- Token-aware rate limiting (200K tokens/day free tier)
- Response caching (JSONL format)
- Resume capability
- Exponential backoff retry

Usage:
  python runner.py --model groq-20b --limit 20  # Pilot run
  python runner.py --model groq-20b              # Full run
  python runner.py --model groq-120b             # Full run on large model
"""

import json
import time
import argparse
from pathlib import Path
from typing import Dict, List, Optional
import sys
import os

try:
    import requests
except ImportError:
    print("ERROR: requests library not found.")
    print("Install with: pip install requests")
    sys.exit(1)

# Configuration
PROMPTS_FILE = Path(__file__).parent.parent / "datasets" / "prompts.jsonl"
CACHE_DIR = Path(__file__).parent / "cache"
CACHE_DIR.mkdir(exist_ok=True)

# Groq API Configuration
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_API_KEY_ENV = "GROQ_API_KEY"

# Model configurations
MODELS = {
    "groq-20b": "llama-3.3-70b-versatile",  # Free tier model (~20B effective)
    "groq-120b": "llama-3.1-405b-reasoning",  # Larger model
}

# Rate limiting (conservative estimates)
DAILY_TOKEN_LIMIT = 200_000  # Groq free tier
ESTIMATED_TOKENS_PER_REQUEST = 500  # Prompt + response average
REQUESTS_PER_MINUTE = 30  # Groq free tier limit


class TokenBudgetTracker:
    """Track token usage across runs."""

    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.budget_file = cache_dir / "token_budget.json"
        self.load_budget()

    def load_budget(self):
        """Load token usage from disk."""
        if self.budget_file.exists():
            with self.budget_file.open() as f:
                data = json.load(f)
                self.tokens_today = data.get("tokens_today", 0)
                self.last_reset = data.get("last_reset", time.strftime("%Y-%m-%d"))
        else:
            self.tokens_today = 0
            self.last_reset = time.strftime("%Y-%m-%d")

        # Reset if new day
        today = time.strftime("%Y-%m-%d")
        if today != self.last_reset:
            print(f"New day detected. Resetting token budget.")
            self.tokens_today = 0
            self.last_reset = today
            self.save_budget()

    def save_budget(self):
        """Save token usage to disk."""
        with self.budget_file.open('w') as f:
            json.dump({
                "tokens_today": self.tokens_today,
                "last_reset": self.last_reset,
                "last_updated": time.strftime("%Y-%m-%d %H:%M:%S")
            }, f, indent=2)

    def add_usage(self, tokens: int):
        """Record token usage."""
        self.tokens_today += tokens
        self.save_budget()

    def can_continue(self, estimated_tokens: int) -> bool:
        """Check if we can make another request."""
        return (self.tokens_today + estimated_tokens) <= DAILY_TOKEN_LIMIT

    def remaining_tokens(self) -> int:
        """Get remaining token budget."""
        return max(0, DAILY_TOKEN_LIMIT - self.tokens_today)

    def remaining_requests(self) -> int:
        """Estimate remaining requests."""
        return self.remaining_tokens() // ESTIMATED_TOKENS_PER_REQUEST


class ResponseCache:
    """Cache responses to avoid re-running."""

    def __init__(self, cache_file: Path):
        self.cache_file = cache_file
        self.cache = self.load_cache()

    def load_cache(self) -> Dict:
        """Load cache from disk."""
        if not self.cache_file.exists():
            return {}

        cache = {}
        with self.cache_file.open() as f:
            for line in f:
                if line.strip():
                    entry = json.loads(line)
                    cache[entry['id']] = entry
        return cache

    def get(self, prompt_id: str) -> Optional[Dict]:
        """Get cached response."""
        return self.cache.get(prompt_id)

    def set(self, entry: Dict):
        """Add entry to cache."""
        self.cache[entry['id']] = entry

        # Append to file
        with self.cache_file.open('a') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')


def load_prompts(prompts_file: Path, limit: Optional[int] = None) -> List[Dict]:
    """Load prompts from JSONL file."""
    prompts = []
    with prompts_file.open() as f:
        for line in f:
            if line.strip():
                prompts.append(json.loads(line))

    if limit:
        prompts = prompts[:limit]

    return prompts


def call_groq_api(prompt: str, model: str, api_key: str, max_retries: int = 3) -> Dict:
    """Call Groq API with exponential backoff retry."""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 2048,
    }

    for attempt in range(max_retries):
        try:
            response = requests.post(
                GROQ_API_URL,
                headers=headers,
                json=payload,
                timeout=60
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "response": data['choices'][0]['message']['content'],
                    "usage": data.get('usage', {}),
                    "model": model,
                }

            elif response.status_code == 429:  # Rate limit
                wait_time = 2 ** attempt
                print(f"  Rate limited. Waiting {wait_time}s...")
                time.sleep(wait_time)
                continue

            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "model": model,
                }

        except requests.Timeout:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"  Timeout. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                return {
                    "success": False,
                    "error": "Request timeout",
                    "model": model,
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "model": model,
            }

    return {
        "success": False,
        "error": f"Failed after {max_retries} retries",
        "model": model,
    }


def run_evaluation(
    model_name: str,
    limit: Optional[int] = None,
    dry_run: bool = False
):
    """Run evaluation with rate limiting and caching."""

    # Validate model
    if model_name not in MODELS:
        print(f"ERROR: Unknown model '{model_name}'")
        print(f"Available models: {', '.join(MODELS.keys())}")
        sys.exit(1)

    model_id = MODELS[model_name]

    # Check API key
    api_key = os.getenv(GROQ_API_KEY_ENV)
    if not api_key:
        print(f"ERROR: {GROQ_API_KEY_ENV} environment variable not set.")
        print(f"Get your API key from: https://console.groq.com/keys")
        print(f"Then set it: export {GROQ_API_KEY_ENV}=your_key_here")
        sys.exit(1)

    # Initialize
    cache_file = CACHE_DIR / f"{model_name}_responses.jsonl"
    cache = ResponseCache(cache_file)
    budget = TokenBudgetTracker(CACHE_DIR)

    prompts = load_prompts(PROMPTS_FILE, limit)

    print("="*60)
    print(f"LLM Router Evaluation Runner")
    print("="*60)
    print(f"Model:           {model_name} ({model_id})")
    print(f"Prompts:         {len(prompts)} total")
    print(f"Cache:           {cache_file}")
    print(f"Cached:          {len(cache.cache)} responses")
    print(f"Tokens today:    {budget.tokens_today:,} / {DAILY_TOKEN_LIMIT:,}")
    print(f"Remaining:       ~{budget.remaining_requests()} requests")
    print(f"Dry run:         {dry_run}")
    print("="*60)
    print()

    if dry_run:
        print("DRY RUN MODE - No API calls will be made.")
        print()

    # Run evaluation
    success_count = 0
    error_count = 0
    cached_count = 0
    skipped_count = 0

    start_time = time.time()

    for i, prompt_data in enumerate(prompts, 1):
        prompt_id = prompt_data['id']
        prompt_text = prompt_data['prompt']
        category = prompt_data['category']

        print(f"[{i}/{len(prompts)}] {prompt_id} ({category})")

        # Check cache
        cached = cache.get(prompt_id)
        if cached:
            print(f"  ✓ Cached")
            cached_count += 1
            continue

        # Check budget
        if not budget.can_continue(ESTIMATED_TOKENS_PER_REQUEST):
            print(f"  ⚠ Token budget exhausted. Stopping.")
            skipped_count = len(prompts) - i + 1
            break

        if dry_run:
            print(f"  → Would call API")
            continue

        # Rate limiting
        time.sleep(60 / REQUESTS_PER_MINUTE)  # Respect RPM limit

        # Call API
        result = call_groq_api(prompt_text, model_id, api_key)

        if result['success']:
            # Extract token usage
            usage = result.get('usage', {})
            total_tokens = usage.get('total_tokens', ESTIMATED_TOKENS_PER_REQUEST)

            # Update budget
            budget.add_usage(total_tokens)

            # Cache result
            cache_entry = {
                'id': prompt_id,
                'category': category,
                'prompt': prompt_text,
                'response': result['response'],
                'model': model_name,
                'usage': usage,
                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
            }
            cache.set(cache_entry)

            success_count += 1
            print(f"  ✓ Success ({total_tokens} tokens)")
        else:
            error_count += 1
            print(f"  ✗ Error: {result['error']}")

    elapsed = time.time() - start_time

    # Summary
    print("\n" + "="*60)
    print("Evaluation Complete")
    print("="*60)
    print(f"Time elapsed:    {elapsed:.1f}s")
    print(f"Cached:          {cached_count} prompts")
    print(f"Success:         {success_count} prompts")
    print(f"Errors:          {error_count} prompts")
    print(f"Skipped:         {skipped_count} prompts")
    print(f"Tokens used:     {budget.tokens_today:,} / {DAILY_TOKEN_LIMIT:,}")
    print(f"Remaining:       ~{budget.remaining_requests()} requests")
    print("="*60)

    if skipped_count > 0:
        print(f"\n⚠ Budget exhausted. Run again tomorrow to complete.")
    elif error_count > 0:
        print(f"\n⚠ {error_count} errors occurred. Check logs and retry.")
    else:
        print(f"\n✓ All prompts evaluated successfully!")


def main():
    parser = argparse.ArgumentParser(description="Run LLM Router evaluation")
    parser.add_argument(
        "--model",
        required=True,
        choices=list(MODELS.keys()),
        help="Model to evaluate"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of prompts (for testing)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run (don't call API)"
    )

    args = parser.parse_args()

    run_evaluation(
        model_name=args.model,
        limit=args.limit,
        dry_run=args.dry_run
    )


if __name__ == "__main__":
    main()
