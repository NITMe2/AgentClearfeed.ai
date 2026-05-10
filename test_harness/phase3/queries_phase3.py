"""Phase 3 test queries: dynamic content extraction (live Bitcoin price)."""

PHASE3_QUERIES = [
    {
        "id": "p3q1",
        "question": "What is the current Bitcoin price in USD and its 24-hour percentage change?",
        "expected_facts": [
            "bitcoin price in USD",
            "24-hour percentage change",
            "BTC or Bitcoin mentioned",
        ],
    },
]
