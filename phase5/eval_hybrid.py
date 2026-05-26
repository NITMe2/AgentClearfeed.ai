"""Quick eval: ACF-evolved vs JSON-evolved vs Hybrid."""

from phase5.fitness import evaluate, get_last_metrics

SCHEMAS = {
    "acf_evolved": {
        "delimiter": ":",
        "key_style": "none",
        "nesting": "flat",
        "field_order": ["id", "type", "title", "source", "author", "confidence", "domain", "tags"],
        "quote_values": False,
        "newline_sep": False,
    },
    "json_evolved": {
        "delimiter": ":",
        "key_style": "none",
        "nesting": "flat",
        "field_order": ["id", "title", "source", "author", "published", "confidence", "domain"],
        "quote_values": True,
        "newline_sep": True,
    },
    "hybrid": {
        "delimiter": ":",
        "key_style": "none",
        "nesting": "flat",
        "field_order": ["id", "title", "source", "author", "published", "confidence", "domain"],
        "quote_values": False,
        "newline_sep": False,
    },
}

results = {}
for name, schema in SCHEMAS.items():
    print(f"Evaluating {name}...", flush=True)
    fit = evaluate(schema)[0]
    m = get_last_metrics()
    results[name] = {"fitness": fit, "tokens": m["avg_tokens"], "acc": m["avg_accuracy"]}
    print(f"  fitness={fit:.4f}  tokens={m['avg_tokens']}  acc={m['avg_accuracy']:.2f}")

print()
print("=" * 50)
print(f"{'Schema':<14} {'Fitness':>8} {'Tokens':>8} {'Accuracy':>9}")
print("-" * 50)
for name, r in results.items():
    print(f"{name:<14} {r['fitness']:>8.4f} {r['tokens']:>8} {r['acc']:>9.2f}")

winner = max(results, key=lambda k: results[k]["fitness"])
print("=" * 50)
print(f"Winner: {winner}  (fitness={results[winner]['fitness']:.4f})")
