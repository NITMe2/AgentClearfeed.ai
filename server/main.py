"""AgentClearfeed server — serves .acf documents over HTTP."""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse

from server.parser import load_documents
from server.phase3 import router as phase3_router

app = FastAPI(title="AgentClearfeed", version="0.1")
app.include_router(phase3_router)

DOCS_DIR = Path(__file__).parent / "documents"
DOCS_DIR_PHASE2 = Path(__file__).parent / "documents_phase2"
documents: dict[str, dict] = {}


@app.on_event("startup")
def startup():
    global documents
    documents = load_documents(DOCS_DIR)
    if DOCS_DIR_PHASE2.exists():
        documents.update(load_documents(DOCS_DIR_PHASE2))


@app.get("/acf/document/{doc_id}", response_class=PlainTextResponse)
def get_document(doc_id: str):
    if doc_id not in documents:
        raise HTTPException(404, f"Document {doc_id} not found")
    return documents[doc_id]["raw"]


@app.get("/acf/index", response_class=PlainTextResponse)
def get_index():
    index_id = "acf-index-ai-fairness"
    if index_id in documents:
        return documents[index_id]["raw"]
    lines = ["ACF Index\n"]
    for doc_id, doc in documents.items():
        h = doc["header"]
        lines.append(f"  {doc_id}: {h.get('title', 'Untitled')} [{h.get('type', '?')}]")
    return "\n".join(lines)


@app.get("/acf/domain/{domain}", response_class=PlainTextResponse)
def get_by_domain(domain: str):
    matches = []
    for doc_id, doc in documents.items():
        if doc["header"].get("domain", "").lower() == domain.lower():
            matches.append(doc["raw"])
    if not matches:
        raise HTTPException(404, f"No documents found for domain: {domain}")
    return "\n\n===\n\n".join(matches)


@app.get("/acf/query", response_class=PlainTextResponse)
def query(q: str):
    q_lower = q.lower()
    scored = []
    for doc_id, doc in documents.items():
        score = 0
        header = doc["header"]
        searchable = " ".join([
            header.get("title", ""),
            header.get("tags", ""),
            header.get("domain", ""),
            doc["body"],
        ]).lower()
        for word in q_lower.split():
            if word in searchable:
                score += 1
            if word in header.get("title", "").lower():
                score += 3
        if score > 0:
            scored.append((score, doc))

    if not scored:
        return "No matching documents found."

    scored.sort(key=lambda x: x[0], reverse=True)
    results = [item[1]["raw"] for item in scored[:3]]
    return "\n\n===\n\n".join(results)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
