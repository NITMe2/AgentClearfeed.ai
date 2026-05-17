# AgentClearfeed — Phase 4: Agent Communication Protocol

**Branch:** `Agent-Comm` | **Base:** [main](https://github.com/NITMe2/AgentClearfeed.ai)

Phases 1–3 proved ACF beats HTML for agent document retrieval (97.6% token reduction, 5.2x faster, +0.51 accuracy across 4 models). Phase 4 asks the next question: **which format is best when agents talk to each other?**

Two agents in sequence. Agent A fetches a document and formats it. Agent B receives it and answers a question. Only the wire format changes: **ACF** vs **JSON** vs **TOON**.

New metric: **data loss** — facts in Agent A's message that fail to appear in Agent B's answer. Measures information fidelity through the handoff, not just token count.

---

## Results

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

---

### Phase 2 Dataset — Wikipedia (5 queries, Claude Haiku 4.5)

| Format | Avg Tokens | Accuracy | Data Loss | Cost/query |
|--------|:----------:|:--------:|:---------:|:----------:|
| ACF | 1,129 | **1.00** | 0.00 | $0.000903 |
| TOON | 1,150 | **1.00** | 0.00 | $0.000920 |
| JSON | 1,228 | **1.00** | 0.00 | $0.000982 |

Perfect accuracy across all formats on Wikipedia content — Haiku handles clean structured docs regardless of format. ACF still wins on tokens (-8.1% vs JSON). TOON closes the gap on article content with structured lists.

---

### Token Efficiency Across Both Datasets

| Comparison | AI Fairness | Wikipedia |
|-----------|:-----------:|:---------:|
| ACF vs JSON | **-11.2%** | **-8.1%** |
| TOON vs JSON | -7.7% | -6.4% |
| ACF vs TOON | -3.9% | -1.9% |

ACF < TOON < JSON on token count, consistently. The gap narrows on longer Wikipedia articles where JSON's fixed syntax overhead becomes proportionally smaller.

---

### Four Test Structure

Each run compares formats in four rounds — same query, same data, same model, only format changes:

| Test | Formats | Purpose |
|------|---------|---------|
| 1 | ACF vs JSON | Direct comparison, most common baseline |
| 2 | ACF vs TOON | ACF vs best compact alternative |
| 3 | JSON vs TOON | Validates against TOON's published benchmarks |
| 4 | ACF vs JSON vs TOON | Finale — all three together |

---

## Key Findings

**1. Data loss is format-agnostic for capable models.** Qwen (deterministic) preserves facts identically across ACF, TOON, and JSON. The information survives the handoff regardless of wire format.

**2. ACF wins on tokens, consistently.** 8-11% fewer tokens than JSON across both datasets and both models. Smaller messages, lower cost, same or better accuracy.

**3. TOON is a credible middle ground.** 6-8% fewer tokens than JSON. Readable, structured, and — on tabular content like TCP handshake steps or CRISPR mechanisms — starts to close the gap with ACF.

**4. The same advantage holds end-to-end.** ACF beat HTML by 93-98% in retrieval. It beats JSON by 8-11% in agent comms. The format wins at every layer of the stack.

---

## TOON Note

[toon-format](https://github.com/toon-format/toon) v0.1.0 ships with a stub encoder (`NotImplementedError`). This repo includes a custom implementation in `phase4/formatters/toon_fmt.py` built from the published spec.

---

## Running Phase 4

No server needed — reads documents directly from `server/documents/`.

```bash
pip install -r requirements.txt

# AI Fairness dataset (3 queries)
python -m phase4.orchestrator                                          # Qwen 2.5 14B (default)
python -m phase4.orchestrator --model claude-haiku                    # Claude Haiku 4.5

# Wikipedia dataset (5 queries)
python -m phase4.orchestrator --dataset phase2                        # Qwen
python -m phase4.orchestrator --dataset phase2 --model claude-haiku   # Haiku
```

### Prerequisites

- Python 3.11+
- [Ollama](https://ollama.ai) + `ollama pull qwen2.5:14b` (for local model runs)
- `.env` with API keys for cloud models:
  ```
  ANTHROPIC_API_KEY=sk-ant-...
  KIMI_API_KEY=sk-...
  ```

---

## File Structure

```
phase4/
├── agent_a.py              # Fetches document, formats in ACF/JSON/TOON
├── agent_b.py              # Receives message, queries model, grades answer
├── orchestrator.py         # Runs all 4 tests (--model, --dataset flags)
├── formatters/
│   ├── acf.py              # ACF passthrough
│   ├── json_fmt.py         # json.dumps
│   └── toon_fmt.py         # TOON encoder (custom implementation)
└── results/
    ├── phase4_results_phase1_qwen2.5_14b.json
    ├── phase4_results_phase1_claude-haiku.json
    └── phase4_results_phase2_claude-haiku.json
```

---

## Prior Phases

| Phase | What | Headline |
|-------|------|---------|
| 1 | Single-doc retrieval, HTML vs ACF | 97.6% token reduction, 5.2x faster |
| 2 | Multi-doc retrieval, 4 models | ACF wins on every model tested |
| 3 | Live data, staleness metric | 98.7% reduction, 11.5x fresher |

Full results and methodology on the [main branch](https://github.com/NITMe2/AgentClearfeed.ai).
