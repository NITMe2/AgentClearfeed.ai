# AgentClearfeed

**The human web is broken for AI agents.** Pages built for human eyes are bloated with navigation, ads, cookie banners, tracking scripts, and layout markup. An agent parsing a typical webpage wastes 93-98% of its token budget on noise before reaching the actual content.

AgentClearfeed is a parallel content layer built for inference. Clean, structured, verified content served in `.acf` format - not a scraper on top of the human web, but a native format designed for how AI agents actually consume information.

## Key Results

| Metric | HTML | ACF | Improvement |
|--------|------|-----|-------------|
| Tokens per query (Phase 1) | 16,388 | 394 | **97.6% reduction** |
| Tokens per 10-doc retrieval (Phase 2) | 84,022 | 5,429 | **93.5% reduction** |
| Inference latency (Phase 1) | 119s | 23s | **5.2x faster** |
| Multi-doc accuracy (avg across 4 models) | 0.42 | 0.93 | **+0.51 absolute** |

## Why This Matters

LLM inference cost scales with input tokens. Every webpage an agent reads carries thousands of tokens of HTML markup, JavaScript, CSS classes, and UI chrome that contribute nothing to the answer. This isn't just wasteful - it actively degrades accuracy. Models get lost in the noise.

ACF strips content down to structured, labelled fields. The result: agents read less, understand more, and cost a fraction to run.

## Phase 1 - Single Document Retrieval

Three AI fairness questions answered from realistic modern webpages (cookie banners, tracking scripts, ads, paywalls, chat widgets) versus the same content in ACF format.

**Model:** Qwen 2.5 14B (local, Ollama)

| Query | HTML Tokens | ACF Tokens | Reduction | HTML Latency | ACF Latency |
|-------|------------|-----------|-----------|-------------|-------------|
| What is demographic parity? | 23,988 | 320 | **98.7%** | 131s | 22s |
| Known biases in COMPAS dataset? | 13,292 | 398 | **97.0%** | 120s | 26s |
| Can calibration and equalised odds coexist? | 11,886 | 465 | **96.1%** | 107s | 22s |
| **Average** | **16,388** | **394** | **97.6%** | **119s** | **23s** |

Accuracy was identical across both formats. Every extra token in the HTML was pure overhead.

## Phase 2 - Multi-Document Retrieval

10 diverse Wikipedia topics (Photosynthesis, Roman Empire, TCP/IP, Jazz, Great Wall, CRISPR, Relativity, Impressionism, Volcanic Eruptions, Bitcoin) concatenated as a single context. The model must find the right document in the haystack and extract the answer. ACF timings include realistic fetch overhead from a conversion layer.

### Cross-Model Accuracy Comparison

Tested across 4 models spanning local open-source, commercial API, and Chinese cloud providers:

| Model | Type | HTML Accuracy | ACF Accuracy | ACF Advantage |
|-------|------|:------------:|:------------:|:-------------:|
| Qwen 2.5 14B | Local (Ollama) | 0.87 | **1.00** | +0.13 |
| Claude Haiku 4.5 | Anthropic API | 0.67 | **1.00** | +0.33 |
| Kimi K2.5 | Moonshot API | 0.13 | **0.93** | +0.80 |
| Kimi K2.6 | Moonshot API | 0.00 | **0.80** | +0.80 |
| Kimi K2.5 + Agent Swarm | Moonshot API | 0.20 | - | - |

**ACF wins on every model.** The smaller or less HTML-savvy the model, the bigger the advantage.

### Per-Query Breakdown (Claude Haiku 4.5)

| Query | Target | HTML Acc | ACF Acc |
|-------|--------|:--------:|:-------:|
| Stages of photosynthesis? | Photosynthesis | 1.00 | 1.00 |
| TCP three-way handshake? | TCP/IP | 0.00 | 1.00 |
| How does CRISPR-Cas9 cut DNA? | CRISPR | 0.33 | 1.00 |
| Impressionist vs academic art? | Impressionism | 1.00 | 1.00 |
| Bitcoin double-spending prevention? | Bitcoin | 1.00 | 1.00 |

Haiku couldn't even find the TCP handshake answer in 84K tokens of HTML - it said the information wasn't in the context. With 5.4K tokens of ACF, it answered perfectly.

### The Agent Swarm Test

Kimi K2.5 scored 0.13 on HTML retrieval. We tested whether Kimi's Agent Swarm feature (multi-agent orchestration with up to 100 sub-agents) could rescue HTML performance.

**Result: 0.20 accuracy.** Agent Swarm barely moved the needle.

More agents can't fix bad input. The swarm is still processing the same noisy HTML - orchestration doesn't solve a format problem. Meanwhile, a single ACF call with zero orchestration scores 0.93.

**One cheap API call with ACF > an entire multi-agent pipeline with HTML.**

### Token Efficiency

Consistent 93.5% reduction across all models and queries:

| Topic | HTML Tokens | ACF Tokens | Ratio |
|-------|-----------|-----------|-------|
| Photosynthesis | 8,916 | 536 | 17x |
| Roman Empire | 9,000 | 516 | 17x |
| TCP/IP | 9,000 | 499 | 18x |
| Jazz | 9,000 | 513 | 18x |
| Great Wall | 9,000 | 501 | 18x |
| CRISPR | 8,895 | 569 | 16x |
| Relativity | 6,705 | 552 | 12x |
| Impressionism | 8,640 | 598 | 14x |
| Volcanic Eruptions | 5,794 | 608 | 10x |
| Bitcoin | 9,000 | 519 | 17x |
| **Total** | **84,022** | **5,429** | **15.5x** |

## What ACF Proves

1. **Format is the bottleneck, not the model.** Kimi K2.6 scores 0.0 on HTML and 0.80 on ACF - same model, same content, different format.

2. **ACF is model-agnostic.** Every model tested - from a 14B local model to frontier APIs to Chinese cloud providers - performs better with ACF.

3. **ACF makes smaller models viable.** Tasks that require expensive frontier models with HTML work perfectly with cheap models on ACF. This changes the economics of agent deployments.

4. **Orchestration can't fix format.** Agent Swarm, multi-agent pipelines, RAG - none of these solve the fundamental problem of noisy input. Clean input does.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Start the ACF server
python -m server.main

# Phase 1 - single-doc retrieval (requires Ollama + qwen2.5:14b)
python -m test_harness.harness

# Phase 2 - multi-doc retrieval
python -m test_harness.phase2.harness_phase2                          # Ollama (default: qwen2.5:14b)
python -m test_harness.phase2.harness_phase2 --model claude-haiku     # Anthropic API
python -m test_harness.phase2.harness_phase2 --model kimi-k2.5        # Kimi API
python -m test_harness.phase2.harness_phase2 --model kimi-k2.5 --swarm --html-only  # Agent Swarm test
```

### Prerequisites

- Python 3.11+
- [Ollama](https://ollama.ai) for local models (`ollama pull qwen2.5:14b`)
- `.env` file with API keys for cloud models:
  ```
  ANTHROPIC_API_KEY=sk-ant-...
  KIMI_API_KEY=sk-...
  ```

## ACF Format

ACF (AgentClearfeed Format) is a plain text format designed for LLM consumption. Every field is explicit, every document is self-describing. See [ACF_Format_Spec.md](ACF_Format_Spec.md) for the full specification.

Core principles:
- **Token efficiency first** - every byte must earn its place
- **Structured over prose** - fields not paragraphs
- **Explicit affordances** - agents always know what they're reading
- **Ungameable by design** - structured fields leave no room for SEO manipulation

## Project Structure

```
AgentClearfeed/
├── ACF_Format_Spec.md              # Format specification
├── server/
│   ├── main.py                     # FastAPI server
│   ├── parser.py                   # ACF document parser
│   ├── documents/                  # Phase 1: AI fairness .acf docs
│   └── documents_phase2/           # Phase 2: 10 Wikipedia .acf docs
├── test_harness/
│   ├── harness.py                  # Phase 1 test runner
│   ├── queries.py                  # Phase 1 queries
│   ├── raw_sources/                # Phase 1 HTML sources
│   ├── phase2/
│   │   ├── harness_phase2.py       # Phase 2 test runner (multi-model)
│   │   ├── queries_phase2.py       # Phase 2 queries
│   │   ├── fetch_wikipedia.py      # Wikipedia HTML fetcher
│   │   └── raw_sources/            # Phase 2 HTML sources
│   └── results/                    # JSON results from all runs
└── requirements.txt
```

## API Endpoints

```
GET /acf/document/{id}    - Fetch a single ACF document
GET /acf/index            - List all documents
GET /acf/domain/{domain}  - Get documents by domain
GET /acf/query?q={query}  - Natural language search
```
