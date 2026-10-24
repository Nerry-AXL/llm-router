#!/usr/bin/env python3
"""
Dataset Sampling Script for LLM Router Evaluation

Samples 400 prompts from public benchmarks with stratified sampling:
- 100 math (GSM8K)
- 100 code (MBPP)
- 100 reasoning (ARC-Challenge)
- 100 chat (synthetic generation)

Outputs: datasets/prompts.jsonl
"""

import json
import random
from pathlib import Path
from typing import List, Dict
import urllib.request

# Set random seed for reproducibility
random.seed(42)

OUTPUT_FILE = Path(__file__).parent / "prompts.jsonl"
LICENSES_FILE = Path(__file__).parent / "LICENSE.md"


def download_gsm8k(n_samples: int = 100) -> List[Dict]:
    """
    Download GSM8K math dataset from HuggingFace.
    License: MIT
    """
    print(f"Downloading GSM8K (math) - sampling {n_samples} prompts...")

    # GSM8K test set URL (using HuggingFace datasets API)
    url = "https://datasets-server.huggingface.co/rows?dataset=openai/gsm8k&config=main&split=test&offset=0&length=1000"

    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            data = json.loads(response.read())
            rows = data.get('rows', [])

            # Sample and format
            sampled = random.sample(rows, min(n_samples, len(rows)))
            prompts = []
            for i, item in enumerate(sampled):
                row_data = item.get('row', {})
                prompts.append({
                    "id": f"gsm8k_{i}",
                    "category": "math",
                    "prompt": row_data.get('question', ''),
                    "answer": row_data.get('answer', ''),
                    "source": "GSM8K",
                    "license": "MIT"
                })

            print(f"  ✓ Sampled {len(prompts)} math prompts")
            return prompts

    except Exception as e:
        print(f"  ✗ Failed to download GSM8K: {e}")
        print("  → Using fallback synthetic math prompts")
        return generate_fallback_math(n_samples)


def download_mbpp(n_samples: int = 100) -> List[Dict]:
    """
    Download MBPP code dataset from HuggingFace.
    License: CC-BY-4.0
    """
    print(f"Downloading MBPP (code) - sampling {n_samples} prompts...")

    url = "https://datasets-server.huggingface.co/rows?dataset=google-research-datasets/mbpp&config=full&split=test&offset=0&length=500"

    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            data = json.loads(response.read())
            rows = data.get('rows', [])

            sampled = random.sample(rows, min(n_samples, len(rows)))
            prompts = []
            for i, item in enumerate(sampled):
                row_data = item.get('row', {})
                prompts.append({
                    "id": f"mbpp_{i}",
                    "category": "code",
                    "prompt": row_data.get('text', ''),
                    "answer": row_data.get('code', ''),
                    "source": "MBPP",
                    "license": "CC-BY-4.0"
                })

            print(f"  ✓ Sampled {len(prompts)} code prompts")
            return prompts

    except Exception as e:
        print(f"  ✗ Failed to download MBPP: {e}")
        print("  → Using fallback synthetic code prompts")
        return generate_fallback_code(n_samples)


def download_arc(n_samples: int = 100) -> List[Dict]:
    """
    Download ARC-Challenge reasoning dataset from HuggingFace.
    License: CC-BY-SA-4.0
    """
    print(f"Downloading ARC-Challenge (reasoning) - sampling {n_samples} prompts...")

    url = "https://datasets-server.huggingface.co/rows?dataset=allenai/ai2_arc&config=ARC-Challenge&split=test&offset=0&length=1000"

    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            data = json.loads(response.read())
            rows = data.get('rows', [])

            sampled = random.sample(rows, min(n_samples, len(rows)))
            prompts = []
            for i, item in enumerate(sampled):
                row_data = item.get('row', {})
                question = row_data.get('question', '')
                choices = row_data.get('choices', {})
                answer_key = row_data.get('answerKey', '')

                # Format as multiple choice
                choices_text = choices.get('text', [])
                choices_labels = choices.get('label', [])
                formatted_choices = "\n".join(
                    f"{label}. {text}"
                    for label, text in zip(choices_labels, choices_text)
                )

                prompt_text = f"{question}\n\n{formatted_choices}"

                prompts.append({
                    "id": f"arc_{i}",
                    "category": "reasoning",
                    "prompt": prompt_text,
                    "answer": answer_key,
                    "source": "ARC-Challenge",
                    "license": "CC-BY-SA-4.0"
                })

            print(f"  ✓ Sampled {len(prompts)} reasoning prompts")
            return prompts

    except Exception as e:
        print(f"  ✗ Failed to download ARC-Challenge: {e}")
        print("  → Using fallback synthetic reasoning prompts")
        return generate_fallback_reasoning(n_samples)


def generate_chat_prompts(n_samples: int = 100) -> List[Dict]:
    """
    Generate synthetic chat prompts across various topics.
    These are original synthetic data.
    """
    print(f"Generating {n_samples} synthetic chat prompts...")

    templates = [
        # Information seeking
        "What is {topic}?",
        "Explain {topic} to me like I'm five.",
        "What are the key differences between {topic1} and {topic2}?",
        "How does {topic} work?",
        "What are the benefits of {topic}?",

        # Advice/recommendations
        "What should I know about {topic}?",
        "Can you recommend resources for learning {topic}?",
        "What are best practices for {topic}?",
        "How can I improve my {skill}?",
        "What tools should I use for {task}?",

        # Analysis
        "What are the pros and cons of {topic}?",
        "Compare {topic1} vs {topic2}.",
        "Analyze the impact of {topic}.",
        "What trends are shaping {domain}?",
        "Evaluate {topic} from multiple perspectives.",

        # Creative/open-ended
        "Tell me an interesting fact about {topic}.",
        "What's new in {domain}?",
        "Describe {topic} in three sentences.",
        "What misconceptions exist about {topic}?",
        "Summarize the history of {topic}.",
    ]

    topics = [
        "machine learning", "web development", "data privacy", "cloud computing",
        "artificial intelligence", "cybersecurity", "blockchain", "quantum computing",
        "climate change", "renewable energy", "space exploration", "biotechnology",
        "electric vehicles", "social media", "remote work", "cryptocurrency",
        "virtual reality", "5G networks", "automation", "sustainable agriculture",
        "mental health", "nutrition", "exercise", "meditation", "sleep science",
        "productivity", "time management", "communication skills", "leadership",
        "entrepreneurship", "financial planning", "investing", "real estate",
        "urban planning", "transportation", "education systems", "learning methods",
        "scientific method", "critical thinking", "problem solving", "creativity",
    ]

    topic_pairs = [
        ("SQL", "NoSQL"), ("Python", "JavaScript"), ("REST", "GraphQL"),
        ("React", "Vue"), ("AWS", "Azure"), ("Docker", "Kubernetes"),
        ("agile", "waterfall"), ("centralization", "decentralization"),
    ]

    skills = ["coding", "writing", "communication", "problem-solving", "leadership"]
    tasks = ["project management", "data analysis", "web design", "API development"]
    domains = ["technology", "healthcare", "finance", "education", "entertainment"]

    prompts = []
    for i in range(n_samples):
        template = random.choice(templates)

        # Fill in template placeholders
        if "{topic1}" in template and "{topic2}" in template:
            t1, t2 = random.choice(topic_pairs)
            text = template.format(topic1=t1, topic2=t2)
        elif "{topic}" in template:
            text = template.format(topic=random.choice(topics))
        elif "{skill}" in template:
            text = template.format(skill=random.choice(skills))
        elif "{task}" in template:
            text = template.format(task=random.choice(tasks))
        elif "{domain}" in template:
            text = template.format(domain=random.choice(domains))
        else:
            text = template

        prompts.append({
            "id": f"chat_{i}",
            "category": "chat",
            "prompt": text,
            "answer": None,  # No ground truth for open-ended chat
            "source": "synthetic",
            "license": "CC0-1.0 (Public Domain)"
        })

    print(f"  ✓ Generated {len(prompts)} chat prompts")
    return prompts


def generate_fallback_math(n: int) -> List[Dict]:
    """Fallback synthetic math prompts if GSM8K fails."""
    templates = [
        "If {a} apples cost ${b}, how much do {c} apples cost?",
        "A train travels {a} km in {b} hours. What is its average speed?",
        "Calculate {a}% of {b}.",
        "Solve for x: {a}x + {b} = {c}",
        "What is the area of a rectangle with length {a}m and width {b}m?",
    ]

    prompts = []
    for i in range(n):
        template = random.choice(templates)
        a, b, c = random.randint(1, 50), random.randint(1, 50), random.randint(1, 100)
        text = template.format(a=a, b=b, c=c)
        prompts.append({
            "id": f"math_fallback_{i}",
            "category": "math",
            "prompt": text,
            "answer": None,
            "source": "synthetic_fallback",
            "license": "CC0-1.0"
        })
    return prompts


def generate_fallback_code(n: int) -> List[Dict]:
    """Fallback synthetic code prompts if MBPP fails."""
    templates = [
        "Write a function to {task}.",
        "Implement a Python function that {task}.",
        "Create a function to {task} and return the result.",
    ]

    tasks = [
        "reverse a string", "find the maximum element in a list",
        "check if a number is prime", "calculate factorial of n",
        "merge two sorted lists", "count vowels in a string",
        "find the sum of digits in a number", "remove duplicates from a list",
    ]

    prompts = []
    for i in range(n):
        template = random.choice(templates)
        task = random.choice(tasks)
        text = template.format(task=task)
        prompts.append({
            "id": f"code_fallback_{i}",
            "category": "code",
            "prompt": text,
            "answer": None,
            "source": "synthetic_fallback",
            "license": "CC0-1.0"
        })
    return prompts


def generate_fallback_reasoning(n: int) -> List[Dict]:
    """Fallback synthetic reasoning prompts if ARC fails."""
    templates = [
        "Which of the following is {property}?\nA. {a}\nB. {b}\nC. {c}\nD. {d}",
        "What would most likely happen if {condition}?\nA. {a}\nB. {b}\nC. {c}\nD. {d}",
    ]

    prompts = []
    for i in range(n):
        template = templates[i % len(templates)]
        text = template.format(
            property="most likely",
            condition="X happens",
            a="Option A", b="Option B", c="Option C", d="Option D"
        )
        prompts.append({
            "id": f"reasoning_fallback_{i}",
            "category": "reasoning",
            "prompt": text,
            "answer": None,
            "source": "synthetic_fallback",
            "license": "CC0-1.0"
        })
    return prompts


def write_licenses():
    """Write LICENSE.md documenting all data sources and licenses."""
    content = """# Dataset Licenses

This evaluation uses prompts from public benchmarks and synthetic data.
All data is used for research and evaluation purposes only.

## Public Benchmarks

### GSM8K (Math)
- **Source:** OpenAI GSM8K Dataset
- **URL:** https://huggingface.co/datasets/openai/gsm8k
- **License:** MIT
- **Usage:** 100 sampled prompts from test set
- **Citation:** Cobbe et al., 2021

### MBPP (Code)
- **Source:** Google MBPP Dataset
- **URL:** https://huggingface.co/datasets/google-research-datasets/mbpp
- **License:** CC-BY-4.0
- **Usage:** 100 sampled prompts from test set
- **Citation:** Austin et al., 2021

### ARC-Challenge (Reasoning)
- **Source:** AI2 ARC Dataset
- **URL:** https://huggingface.co/datasets/allenai/ai2_arc
- **License:** CC-BY-SA-4.0
- **Usage:** 100 sampled prompts from challenge set
- **Citation:** Clark et al., 2018

## Synthetic Data

### Chat Prompts
- **Source:** Generated for this project
- **License:** CC0-1.0 (Public Domain)
- **Usage:** 100 prompts covering various topics
- **Method:** Template-based generation with diverse topics

## Compliance

✓ All datasets allow research use
✓ All datasets allow redistribution of samples
✓ All licenses are compatible with this project
✓ No personally identifiable information (PII)
✓ No proprietary or confidential data

## Random Seed

Sampling uses `random.seed(42)` for reproducibility.
"""

    LICENSES_FILE.write_text(content, encoding='utf-8')
    print(f"\n✓ Wrote {LICENSES_FILE}")


def main():
    print("="*60)
    print("LLM Router Dataset Sampling")
    print("="*60)
    print()

    # Sample from each category
    math_prompts = download_gsm8k(100)
    code_prompts = download_mbpp(100)
    reasoning_prompts = download_arc(100)
    chat_prompts = generate_chat_prompts(100)

    # Combine all prompts
    all_prompts = math_prompts + code_prompts + reasoning_prompts + chat_prompts

    # Write to JSONL
    print(f"\nWriting {len(all_prompts)} prompts to {OUTPUT_FILE}...")
    with OUTPUT_FILE.open('w', encoding='utf-8') as f:
        for prompt in all_prompts:
            f.write(json.dumps(prompt, ensure_ascii=False) + '\n')

    # Write licenses
    write_licenses()

    # Summary
    print("\n" + "="*60)
    print("Summary:")
    print(f"  Math:      {len(math_prompts)} prompts")
    print(f"  Code:      {len(code_prompts)} prompts")
    print(f"  Reasoning: {len(reasoning_prompts)} prompts")
    print(f"  Chat:      {len(chat_prompts)} prompts")
    print(f"  TOTAL:     {len(all_prompts)} prompts")
    print("="*60)
    print(f"\n✓ Dataset ready: {OUTPUT_FILE}")
    print(f"✓ Licenses documented: {LICENSES_FILE}")


if __name__ == "__main__":
    main()
