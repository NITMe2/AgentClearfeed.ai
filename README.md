# AgentClearfeed — Phase 1 Proof of Concept

**97.6% token reduction. 5.2x faster. Zero accuracy loss.**

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

# In another terminal, run the test harness (requires Ollama with qwen2.5:14b)
python -m test_harness.harness
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
│   └── documents/               # 10 AI fairness .acf documents + index
├── test_harness/
│   ├── harness.py               # Main test runner
│   ├── queries.py               # Test queries with expected facts
│   └── raw_sources/             # HTML equivalents for comparison
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
