# AgentClearfeed — Phase 1 Proof of Concept

An agent-native web layer. Clean, structured, verified content served in `.acf` format.

Phase 1 proves the token efficiency and accuracy delta between an agent querying raw HTML versus querying clean ACF format.

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
