# AgentClearfeed — Phase 6: Multi-Agent Swarm with Live Content

**Branch:** `phase4-agent-comms-test` | **Base:** [main](https://github.com/NITMe2/AgentClearfeed.ai)

> **Note:** `max_tokens` is set conservatively for cost control during testing, not representative of production deployment.

---

## Phase 6 — Multi-Agent Swarm with Live Content

Tests whether evolved-ACF's efficiency advantage holds — and compounds — across a realistic multi-agent topology with live Wikipedia content.

**Standard run — single Kimi K2.5 coordinator (4 queries × 3 Wikipedia sources)**

| Format | Avg ctx tokens | Avg accuracy | Compounding |
|--------|:--------------:|:------------:|:-----------:|
| **Evolved** | **5,720** | **0.67** | 0.989x |
| ACF | 5,783 | 0.58 | 0.999x |
| JSON | 5,786 | 0.42 | 1.000x |

With a capable model, evolved-ACF wins on both axes: 1.1% fewer context tokens and highest accuracy.

**Explicit 3-agent run — 3 parallel Haiku sub-agents → Haiku coordinator**

```
Query
  ├── Haiku sub-agent A (doc 1 in wire fmt) → answer A ─┐
  ├── Haiku sub-agent B (doc 2 in wire fmt) → answer B ──→ Haiku Coordinator → Final answer
  └── Haiku sub-agent C (doc 3 in wire fmt) → answer C ─┘
```

| Format | Avg ctx tokens | Avg accuracy | Compounding |
|--------|:--------------:|:------------:|:-----------:|
| Evolved | 5,720 | 0.42 | 0.989x |
| ACF | 5,783 | 0.42 | 0.999x |
| **JSON** | **5,786** | **0.50** | 1.000x |

The accuracy ranking flips with smaller models. Evolved-ACF's compressed positional encoding requires sufficient model capability to parse reliably — below that threshold, JSON's explicit structure wins even at higher token cost.

```bash
python -m phase6.orchestrator             # Standard run (Kimi K2.5)
python -m phase6.orchestrator --explicit  # Explicit 3-agent topology (Claude Haiku)
```

---

## Phase 5 — Genetic Algorithm: Evolving the Format

A DEAP genetic algorithm evolved document format schemas starting from ACF as the seed individual. Fitness = 60% accuracy + 40% token efficiency. Model: llama3.1:8b via Ollama.

| Schema | Tokens | Accuracy | Fitness |
|--------|:------:|:--------:|:-------:|
| ACF seed | 759 | 0.67 | 0.941 |
| **Evolved** | **682** | **0.78** | **1.073** |

**+13.99% fitness improvement.** Converged at generation 7; entire population at the same solution by generation 10.

**Winning evolved schema:**
```python
{
    "delimiter": ":",
    "key_style": "none",       # no key names — positional values only
    "nesting": "flat",         # strip section headers from body
    "field_order": ["id", "type", "title", "source", "author", "confidence", "domain", "tags"],
    "quote_values": False,
    "newline_sep": False,      # header collapsed to a single space-separated line
}
```

Evolution didn't replace ACF — it evolved from it. Same delimiter, same fields, same body structure. Just stripped key names and collapsed the header to one line. "ACF designed the structure; evolution found a more compressed encoding."

```bash
python -m phase5.baseline    # Baseline: ACF vs JSON vs TOON on llama3.1:8b
python -m phase5.ga          # Genetic algorithm evolution (10 generations)
```

---

## Phase 4 — Agent Communication Protocol (ACF vs JSON vs TOON)

Two agents in sequence. Agent A fetches a document and formats it. Agent B receives it and answers a question. Only the wire format changes: **ACF** vs **JSON** vs **TOON**.

New metric: **data loss** — facts in Agent A's message that fail to appear in Agent B's answer. Measures information fidelity through the handoff, not just token count.

### Phase 1 Dataset — AI Fairness (3 queries)

**Qwen 2.5 14B** (local, Ollama, seed=42, fully deterministic)

| Format | A Tokens | B Tokens | Total | Accuracy | Data Loss | Cost/query |
|--------|:--------:|:--------:|:-----:|:--------:|:---------:|:----------:|
| ACF | 394 | 434 | 828 | **0.89** | 0.11 | $0.000249 |
| TOON | 410 | 450 | 860 | **0.89** | 0.11 | $0.000258 |
| JSON | 446 | 486 | 932 | **0.89** | 0.11 | $0.000280 |

Qwen with a fixed seed is completely format-agnostic on accuracy. ACF uses 11.2% fewer tokens than JSON. Format makes no difference to what survives the handoff — all three preserve facts equally.

**Claude Haiku 4.5 — Test 4 Finale (all three formats)**

| Format | Total Tokens | Accuracy | Data Loss | Cost/query |
|--------|:------------:|:--------:|:---------:|:----------:|
| ACF | 828 | **1.00** | **0.00** | $0.000663 |
| TOON | 860 | 0.89 | 0.11 | $0.000688 |
| JSON | 932 | 0.89 | 0.11 | $0.000746 |

ACF is the only format that achieves perfect accuracy for Haiku in the three-way finale. Token efficiency and accuracy advantage in the same direction.

### Phase 2 Dataset — Wikipedia (5 queries, Claude Haiku 4.5)

| Format | Avg Tokens | Accuracy | Data Loss | Cost/query |
|--------|:----------:|:--------:|:---------:|:----------:|
| ACF | 1,129 | **1.00** | 0.00 | $0.000903 |
| TOON | 1,150 | **1.00** | 0.00 | $0.000920 |
| JSON | 1,228 | **1.00** | 0.00 | $0.000982 |

Perfect accuracy across all formats on Wikipedia content — Haiku handles clean structured docs regardless of format. ACF still wins on tokens (-8.1% vs JSON). TOON closes the gap on article content with structured lists.

### Token Efficiency Across Both Datasets

| Comparison | AI Fairness | Wikipedia |
|-----------|:-----------:|:---------:|
| ACF vs JSON | **-11.2%** | **-8.1%** |
| TOON vs JSON | -7.7% | -6.4% |
| ACF vs TOON | -3.9% | -1.9% |

ACF < TOON < JSON on token count, consistently. The gap narrows on longer Wikipedia articles where JSON's fixed syntax overhead becomes proportionally smaller.

### Four Test Structure

| Test | Formats | Purpose |
|------|---------|---------|
| 1 | ACF vs JSON | Direct comparison, most common baseline |
| 2 | ACF vs TOON | ACF vs best compact alternative |
| 3 | JSON vs TOON | Validates against TOON's published benchmarks |
| 4 | ACF vs JSON vs TOON | Finale — all three together |

```bash
pip install -r requirements.txt

python -m phase4.orchestrator                                          # Qwen 2.5 14B (default)
python -m phase4.orchestrator --model claude-haiku                    # Claude Haiku 4.5
python -m phase4.orchestrator --dataset phase2 --model claude-haiku   # Wikipedia dataset
```

---

## TOON Note

[toon-format](https://github.com/toon-format/toon) v0.1.0 ships with a stub encoder (`NotImplementedError`). This repo includes a custom implementation in `phase4/formatters/toon_fmt.py` built from the published spec.

---

## Prerequisites

- Python 3.11+
- [Ollama](https://ollama.ai) + `ollama pull qwen2.5:14b` / `ollama pull llama3.1:8b`
- `.env` with API keys:
  ```
  ANTHROPIC_API_KEY=sk-ant-...
  KIMI_API_KEY=sk-...
  ```

---

## Prior Phases

| Phase | What | Headline |
|-------|------|---------|
| 1 | Single-doc retrieval, HTML vs ACF | 97.6% token reduction, 5.2x faster |
| 2 | Multi-doc retrieval, 4 models | ACF wins on every model tested |
| 3 | Live data, staleness metric | 98.7% reduction, 11.5x fresher |

Full results and methodology on the [main branch](https://github.com/NITMe2/AgentClearfeed.ai).
