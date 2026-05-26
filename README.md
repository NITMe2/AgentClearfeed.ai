# AgentClearfeed  - ACF-Champion: Format Evolution & Validation

**Branch:** `ACF-Champion` | **Base:** [main](https://github.com/NITMe2/AgentClearfeed.ai)

> **Note:** `max_tokens` is set conservatively for cost control during testing, not representative of production deployment.

---

## Phase 5-GA  - Cross-Species Evolution & Champion Validation

Two genetic algorithm lineages seeded from opposite ends of the schema space (ACF and JSON). Their best genes were cross-bred into a hybrid, then a combined GA was seeded from both  - finding a new champion that neither lineage reached alone.

### Evolution Timeline

| Stage | Schema | Tokens | Accuracy | Fitness |
|-------|--------|:------:|:--------:|:-------:|
| ACF seed | full keys, nested, no quotes | 759 | 0.67 | 0.941 |
| GA-ACF evolved | no keys, flat, no quotes | 682 | 0.78 | 1.073 |
| GA-JSON evolved | no keys, flat, quoted | 693 | 0.78 | 1.060 |
| Hybrid (cross-bred) | ACF compression + JSON field_order | 670 | 0.78 | 1.082 |
| **Champion (combined GA)** | **3 fields: title author source** | **636** | **0.78** | **1.118** |

**+18.77% fitness improvement over the original ACF seed.**

### Champion Schema

```python
{
    "delimiter": ":",
    "key_style": "none",       # positional values only
    "nesting": "flat",         # strip body section headers
    "field_order": ["title", "author", "source"],   # 3 fields  - everything else is noise
    "quote_values": False,
    "newline_sep": False,       # single space-separated line
}
```

Wire format: `Demographic Parity AgentClearfeed Barocas, Hardt, Narayanan`

The combined GA discovered that id, confidence, domain, and tags are dead weight for QA tasks. The body carries the answer  - the header only needs to identify the source.

### Champion Validation  - A2A (Claude Haiku 4.5, Phase 1 dataset)

| Format | Total Tokens | Accuracy | Data Loss | Cost/query |
|--------|:------------:|:--------:|:---------:|:----------:|
| **Champion** | **636** | **1.00** | **0.00** | $0.000509 |
| ACF | 828 | 0.89 | 0.11 | $0.000663 |
| JSON | 932 | 0.89 | 0.11 | $0.000746 |

Champion wins on every axis: -23.2% tokens vs ACF, -31.8% vs JSON, and higher accuracy than both in agent-to-agent communication.

```bash
python -m phase5.ga_json          # GA seeded from JSON
python -m phase5.ga_combined      # Combined GA (both lineages)
python -m phase5.validate_champion  # Champion in A2A validation
```

---

## Phase 6  - Multi-Agent Swarm with Live Content

Tests whether evolved-ACF's efficiency advantage holds  - and compounds  - across a realistic multi-agent topology with live Wikipedia content.

**Standard run  - single Kimi K2.5 coordinator (4 queries x 3 Wikipedia sources)**

| Format | Avg ctx tokens | Avg accuracy | Compounding |
|--------|:--------------:|:------------:|:-----------:|
| **Evolved** | **5,720** | **0.67** | 0.989x |
| ACF | 5,783 | 0.58 | 0.999x |
| JSON | 5,786 | 0.42 | 1.000x |

With a capable model, evolved-ACF wins on both axes: 1.1% fewer context tokens and highest accuracy.

**Explicit 3-agent run  - 3 parallel Haiku sub-agents -> Haiku coordinator**

```
Query
  |- Haiku sub-agent A (doc 1 in wire fmt) -> answer A -|
  |- Haiku sub-agent B (doc 2 in wire fmt) -> answer B ---> Haiku Coordinator -> Final answer
  |- Haiku sub-agent C (doc 3 in wire fmt) -> answer C -|
```

| Format | Avg ctx tokens | Avg accuracy | Compounding |
|--------|:--------------:|:------------:|:-----------:|
| Evolved | 5,720 | 0.42 | 0.989x |
| ACF | 5,783 | 0.42 | 0.999x |
| **JSON** | **5,786** | **0.50** | 1.000x |

The accuracy ranking flips with smaller models. Evolved-ACF's compressed positional encoding requires sufficient model capability to parse reliably  - below that threshold, JSON's explicit structure wins even at higher token cost.

```bash
python -m phase6.orchestrator             # Standard run (Kimi K2.5)
python -m phase6.orchestrator --explicit  # Explicit 3-agent topology (Claude Haiku)
```

---

## Phase 5  - Genetic Algorithm: Evolving the Format (ACF seed)

A DEAP genetic algorithm evolved document format schemas starting from ACF as the seed individual. Fitness = 60% accuracy + 40% token efficiency. Model: llama3.1:8b via Ollama.

| Schema | Tokens | Accuracy | Fitness |
|--------|:------:|:--------:|:-------:|
| ACF seed | 759 | 0.67 | 0.941 |
| **Evolved** | **682** | **0.78** | **1.073** |

**+13.99% fitness improvement.** Converged at generation 7; entire population at the same solution by generation 10.

Evolution didn't replace ACF  - it evolved from it. Same delimiter, same fields, same body structure. Just stripped key names and collapsed the header to one line.

```bash
python -m phase5.baseline    # Baseline: ACF vs JSON vs TOON on llama3.1:8b
python -m phase5.ga          # Genetic algorithm evolution (10 generations, ACF seed)
```

---

## Phase 4  - Agent Communication Protocol (ACF vs JSON vs TOON)

Two agents in sequence. Agent A fetches a document and formats it. Agent B receives it and answers a question. Only the wire format changes: **ACF** vs **JSON** vs **TOON**.

New metric: **data loss**  - facts in Agent A's message that fail to appear in Agent B's answer.

### Phase 1 Dataset  - AI Fairness (3 queries)

**Claude Haiku 4.5  - Test 4 Finale**

| Format | Total Tokens | Accuracy | Data Loss | Cost/query |
|--------|:------------:|:--------:|:---------:|:----------:|
| ACF | 828 | **1.00** | **0.00** | $0.000663 |
| TOON | 860 | 0.89 | 0.11 | $0.000688 |
| JSON | 932 | 0.89 | 0.11 | $0.000746 |

```bash
python -m phase4.orchestrator --model claude-haiku   # Claude Haiku 4.5
```

---

## TOON Note

[toon-format](https://github.com/toon-format/toon) v0.1.0 ships with a stub encoder (`NotImplementedError`). This repo includes a custom implementation in `phase4/formatters/toon_fmt.py` built from the published spec.

---

## Prerequisites

- Python 3.11+
- [Ollama](https://ollama.ai) + `ollama pull llama3.1:8b`
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
