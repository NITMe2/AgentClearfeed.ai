# Phase 4 — Agent Communication Protocol Test
## Claude Code Guide

**Branch:** `phase4-agent-comms-test`
**DO NOT push to main.**

---

## Project Context

- Repo: NITMe2/AgentClearfeed.ai
- Phases 1–3 proven ACF beats HTML (97.6% token reduction, 5.2x faster, zero accuracy loss)
- Phase 4 tests ACF vs JSON vs TOON for agent-to-agent communication
- Existing stack: FastAPI server, Ollama qwen2.5:14b local, Python test harness, results logged to results/results.json
- TOON (Token-Oriented Object Notation) is an existing open format — Python package available via `pip install toon-format` or from github.com/toon-format/toon

---

## What to Build

Two agents passing structured data between each other.

**Agent A** receives a query → fetches data → formats it → sends to Agent B
**Agent B** receives Agent A's message → processes it → returns a final answer

Run four tests total:
1. ACF vs JSON (2v2)
2. ACF vs TOON (2v2)
3. JSON vs TOON (2v2)
4. ACF vs JSON vs TOON (3v3 finale)

---

## File Structure

```
phase4/
├── agent_a.py          ← formats and sends data
├── agent_b.py          ← receives and processes data
├── orchestrator.py     ← runs all four tests, captures metrics
├── formatters/
│   ├── acf.py          ← ACF formatter (use existing ACF spec)
│   ├── json_fmt.py     ← standard JSON formatter
│   └── toon_fmt.py     ← TOON formatter (use toon-format library)
└── results/
    └── phase4_results.json
```

---

## Agent A (agent_a.py)

- Receives a query
- Fetches relevant data from existing ACF documents in server/documents/
- Formats the same data in all three formats: ACF, JSON, TOON
- Sends formatted message to Agent B
- Logs outbound token count for each format

---

## Agent B (agent_b.py)

- Receives Agent A's message in whatever format the current test uses
- Uses qwen2.5:14b via Ollama at localhost:11434
- Processes the message and returns a structured answer
- Logs: inbound tokens consumed, latency, response content

---

## Orchestrator (orchestrator.py)

Runs all four tests sequentially. Same query, same data, same model every time. Only the format changes.

**Test 1 — ACF vs JSON**
**Test 2 — ACF vs TOON**
**Test 3 — JSON vs TOON**
**Test 4 — ACF vs JSON vs TOON**

Capture per run:
- Agent A outbound tokens (per format)
- Agent B inbound tokens consumed
- Total tokens both agents combined
- Agent B response accuracy vs ground truth (0.0–1.0)
- Data loss score — facts present in Agent A's message missing or wrong in Agent B's answer (0.0–1.0, lower is better)
- End-to-end latency (ms)
- Estimated cost at $0.30/1M tokens

---

## Queries

Use existing queries from test_harness/queries.py — same benchmark queries as Phases 1–3 for direct comparison. Use existing ground truth for accuracy scoring.

---

## Output

**results/phase4_results.json** — raw per-run data for all four tests

**Printed summary — one table per test:**

```
TEST 1: ACF vs JSON
Format | A Tokens | B Tokens | Total | Accuracy | Data Loss | Latency | Cost
ACF    | ...      | ...      | ...   | ...      | ...       | ...     | ...
JSON   | ...      | ...      | ...   | ...      | ...       | ...     | ...
Delta  | ...%     | ...%     | ...%  | ...      | ...       | ...     | ...

TEST 2: ACF vs TOON
...

TEST 3: JSON vs TOON
...

TEST 4: ACF vs JSON vs TOON (finale)
...
```

---

## Important Notes

- Proof of concept, not production. Keep it simple.
- Both agents use qwen2.5:14b locally — no external APIs
- Fixed random seed for reproducibility across all runs
- Log everything to results/phase4_results.json
- Test 3 (JSON vs TOON) should be compared against TOON's own published benchmarks — if results match, methodology is validated; if they differ, note it
- Data loss metric is critical — do not skip it. It measures information fidelity through the agent handoff, not just token count
- README update: add Phase 4 section with all four result tables once tests complete, same format as existing phases

---

## Dependencies to Add to requirements.txt

```
toon-format  # TOON formatter
tiktoken     # token counting
```

---

## Definition of Data Loss Score

For each query, Agent A's message contains N verifiable facts from the ground truth.
After Agent B responds, check how many of those facts are present and correct in the response.

`data_loss = (facts_missing_or_wrong / total_facts_in_message)`

0.0 = perfect fidelity, nothing lost
1.0 = complete data loss

This is the key new metric for Phase 4. Token cost people have estimated before. Information integrity through agent handoffs has not been tested publicly.
