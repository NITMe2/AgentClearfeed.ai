# AgentClearfeed

**Phase 1:** 97.6% token reduction, 5.2x faster, zero accuracy loss.
**Phase 2:** 93.5% token reduction across 10 docs — ACF *outscores* HTML on accuracy (1.00 vs 0.87).

An agent-native web layer. Clean, structured, verified content served in `.acf` format. Not a scraper on top of the human web — a parallel layer built for inference.

## Results

Tested with `qwen2.5:14b` on local Ollama. Same queries, same information. Raw HTML (realistic modern web pages with tracking scripts, cookie banners, ads, paywalls, chat widgets) versus clean ACF format.

| Query | HTML Tokens | ACF Tokens | Reduction | HTML Latency | ACF Latency |
|-------|------------|-----------|-----------|-------------|-------------|
| What is demographic parity? | 23,988 | 320 | **98.7%** | 131s | 22s |
| Known biases in COMPAS dataset? | 13,292 | 398 | **97.0%** | 120s | 26s |
| Can calibration and equalised odds coexist? | 11,886 | 465 | **96.1%** | 107s | 22s |
| **Average** | **16,388** | **394** | **97.6%** | **119s** | **23s** |

Accuracy was identical across both formats — the agent extracted the same facts from 394 tokens that it did from 16,388. Every extra token in the HTML was pure overhead.

## Phase 2 Results — Multi-Document Retrieval

10 diverse Wikipedia topics (Photosynthesis, Roman Empire, TCP/IP, Jazz, Great Wall of China, CRISPR, Theory of Relativity, Impressionism, Volcanic Eruptions, Bitcoin) concatenated as one big context. The model must find the needle in the haystack. ACF path includes realistic fetch overhead to simulate a conversion layer.

| Query | Target | HTML Acc | ACF Acc | HTML Latency | ACF Latency |
|-------|--------|----------|---------|-------------|-------------|
| Stages of photosynthesis? | Photosynthesis | 1.00 | 1.00 | 65s | 59s |
| TCP three-way handshake? | TCP/IP | 1.00 | 1.00 | 58s | 80s |
| How does CRISPR-Cas9 cut DNA? | CRISPR | **0.67** | **1.00** | 81s | 77s |
| Impressionist vs academic art? | Impressionism | 1.00 | 1.00 | 102s | 68s |
| Bitcoin double-spending prevention? | Bitcoin | **0.67** | **1.00** | 43s | 67s |
| **Average** | | **0.87** | **1.00** | **70s** | **70s** |

- **Token reduction:** 84,022 → 5,429 tokens (**93.5%**)
- **Accuracy:** ACF perfect (1.00), HTML missed facts on CRISPR and Bitcoin queries — the model got lost in 84K tokens of HTML noise
- **Latency:** Roughly equal (~70s) even with 23.6s ACF fetch overhead included

### This is what the agent has to parse on the human web

![Bloated HTML page](docs/bloated-html-screenshot.png)

Cookie banners, push notification prompts, newsletter popups, ads, tracking scripts, JSON-LD, social proof toasts, exit-intent overlays, chat widgets, comments, job boards, paywalls — all before reaching the actual content. This is what agents deal with on every query.

The ACF version of the same content is 320 tokens of structured, labelled, verified information. No chrome. No manipulation. No waste.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Start the ACF server
python -m server.main

# In another terminal — Phase 1 (single-doc, AI fairness)
python -m test_harness.harness

# Phase 2 (multi-doc, 10 Wikipedia topics)
python -m test_harness.phase2.fetch_wikipedia   # one-time: fetch HTML pages
python -m test_harness.phase2.harness_phase2    # run the test
```

## Prerequisites

- Python 3.11+
- [Ollama](https://ollama.ai) running locally with `qwen2.5:14b` pulled:
  ```bash
  ollama pull qwen2.5:14b
  ```

## Project Structure

```
├── ACF_Format_Spec.md          # The format standard
├── AgentClearfeed_Concept.docx  # Full concept document
├── server/
│   ├── main.py                  # FastAPI server
│   ├── parser.py                # ACF document parser
│   ├── documents/               # Phase 1: 10 AI fairness .acf documents + index
│   └── documents_phase2/        # Phase 2: 10 diverse Wikipedia .acf documents
├── test_harness/
│   ├── harness.py               # Phase 1 test runner (single-doc)
│   ├── queries.py               # Phase 1 queries
│   ├── raw_sources/             # Phase 1 HTML sources
│   ├── phase2/
│   │   ├── harness_phase2.py    # Phase 2 test runner (multi-doc retrieval)
│   │   ├── queries_phase2.py    # Phase 2 queries (5 across 10 topics)
│   │   ├── fetch_wikipedia.py   # Wikipedia HTML fetcher
│   │   └── raw_sources/         # Phase 2 HTML sources (10 Wikipedia pages)
│   └── results/                 # JSON results from all test runs
└── requirements.txt
```

## What the Test Measures

For each query, the harness:
1. Sends the question + raw HTML context to Ollama
2. Sends the same question + ACF context to Ollama
3. Compares: **token count**, **latency**, **factual accuracy**

## API Endpoints

```
GET /acf/document/{id}    — Fetch a single ACF document
GET /acf/index            — List all documents
GET /acf/domain/{domain}  — Get documents by domain
GET /acf/query?q={query}  — Natural language search
```
