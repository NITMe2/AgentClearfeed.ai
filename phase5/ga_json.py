"""Phase 5 Step 3 — GA seeded from JSON to test convergence.

Seed individual = JSON_SEED (quote_values=True vs ACF's False).
Question: does the GA reach the same optimum from a different starting point?
CONVERGED = global optimum confirmed. DIVERGED = two candidates to cross-breed.

Same fitness function, dataset, and model as ga.py (llama3.1:8b via Ollama).
"""

import copy
import json
import random
from pathlib import Path

from deap import algorithms, base, creator, tools

from phase5 import schema as schema_mod
from phase5.fitness import evaluate, get_last_metrics
from phase5.formatters.evolved import format_doc
from server.parser import load_documents
from test_harness.queries import QUERIES

POPULATION_SIZE = 20
N_GENERATIONS = 10
CROSSOVER_PROB = 0.5
MUTATION_PROB = 0.3
SEED = 42

RESULTS_DIR = Path(__file__).parent / "results"
_SERVER_DIR = Path(__file__).resolve().parents[1] / "server"


def _make_individual(schema_dict: dict):
    ind = creator.Individual()
    ind.update(copy.deepcopy(schema_dict))
    return ind


def _deap_mutate(individual):
    individual.update(schema_mod.mutate(dict(individual)))
    del individual.fitness.values
    return (individual,)


def _deap_crossover(ind1, ind2):
    c1, c2 = schema_mod.crossover(dict(ind1), dict(ind2))
    ind1.update(c1)
    ind2.update(c2)
    del ind1.fitness.values
    del ind2.fitness.values
    return ind1, ind2


def main():
    random.seed(SEED)
    RESULTS_DIR.mkdir(exist_ok=True)

    if not hasattr(creator, "FitnessMax"):
        creator.create("FitnessMax", base.Fitness, weights=(1.0,))
    if not hasattr(creator, "Individual"):
        creator.create("Individual", dict, fitness=creator.FitnessMax)

    toolbox = base.Toolbox()
    toolbox.register("evaluate", evaluate)
    toolbox.register("mate", _deap_crossover)
    toolbox.register("mutate", _deap_mutate)
    toolbox.register("select", tools.selTournament, tournsize=3)
    toolbox.register("clone", copy.deepcopy)

    # --- Establish JSON seed fitness (baseline for this run) ---
    print("Evaluating JSON seed fitness...", flush=True)
    seed_fitness = evaluate(dict(schema_mod.JSON_SEED))[0]
    seed_metrics = get_last_metrics()
    print(f"JSON seed: fitness={seed_fitness:.4f} | tokens={seed_metrics['avg_tokens']} | acc={seed_metrics['avg_accuracy']:.2f}", flush=True)

    # --- Build initial population from JSON seed ---
    pop = [_make_individual(schema_mod.JSON_SEED)]
    for _ in range(POPULATION_SIZE - 1):
        pop.append(_make_individual(schema_mod.mutate(dict(schema_mod.JSON_SEED))))

    hof = tools.HallOfFame(1)

    print(f"\nEvaluating initial population ({POPULATION_SIZE} individuals)...", flush=True)
    for i, ind in enumerate(pop):
        ind.fitness.values = toolbox.evaluate(dict(ind))
        print(f"  [{i+1:02d}/{POPULATION_SIZE}] fitness={ind.fitness.values[0]:.4f}", flush=True)
    hof.update(pop)

    print(f"\nAgentClearfeed Phase 5 — GA (JSON seed)")
    print(f"Population: {POPULATION_SIZE} | Generations: {N_GENERATIONS} | Cx: {CROSSOVER_PROB} | Mut: {MUTATION_PROB}")
    print("=" * 70, flush=True)

    generation_log = []

    for gen in range(1, N_GENERATIONS + 1):
        offspring = algorithms.varAnd(pop, toolbox, CROSSOVER_PROB, MUTATION_PROB)

        invalid = [ind for ind in offspring if not ind.fitness.valid]
        for ind in invalid:
            ind.fitness.values = toolbox.evaluate(dict(ind))

        hof.update(offspring)
        pop = toolbox.select(offspring, POPULATION_SIZE)

        fits = [ind.fitness.values[0] for ind in pop]
        best_fit = hof[0].fitness.values[0]
        mean_fit = sum(fits) / len(fits)

        print(f"Gen {gen:02d} | Best: {best_fit:.4f} | Mean: {mean_fit:.4f} | Re-evaluated: {len(invalid)}", flush=True)
        generation_log.append({
            "gen": gen,
            "best_fitness": round(best_fit, 6),
            "mean_fitness": round(mean_fit, 6),
            "re_evaluated": len(invalid),
        })

    # --- Final evaluation of winner ---
    best_schema = dict(hof[0])
    evaluate(best_schema)
    best_metrics = get_last_metrics()
    best_fitness = hof[0].fitness.values[0]

    improvement_pct = round((best_fitness - seed_fitness) / seed_fitness * 100, 2) if seed_fitness else 0.0

    docs = load_documents(_SERVER_DIR / "documents")
    first_doc = docs[QUERIES[0]["acf_doc"]]
    evolved_example = format_doc(first_doc, best_schema)

    # --- Console summary ---
    print("\n" + "=" * 70)
    outcome = "BEAT JSON" if best_fitness > seed_fitness else "DID NOT BEAT JSON"
    print(f"RESULT: {outcome}")
    print(f"JSON seed fitness : {seed_fitness:.4f}  (tokens={seed_metrics['avg_tokens']}, acc={seed_metrics['avg_accuracy']:.2f})")
    print(f"Best evolved      : {best_fitness:.4f}  (tokens={best_metrics['avg_tokens']}, acc={best_metrics['avg_accuracy']:.2f})")
    print(f"Improvement       : {improvement_pct:+.2f}%")
    print("\nBest evolved schema:")
    for k, v in best_schema.items():
        print(f"  {k}: {v}")
    print(f"\nEvolved format example (first 500 chars):\n{evolved_example[:500]}")

    # --- Save results ---
    output = {
        "baseline_json_fitness": round(seed_fitness, 6),
        "baseline_json_tokens": seed_metrics["avg_tokens"],
        "baseline_json_accuracy": seed_metrics["avg_accuracy"],
        "best_fitness": round(best_fitness, 6),
        "best_tokens": best_metrics["avg_tokens"],
        "best_accuracy": best_metrics["avg_accuracy"],
        "improvement_pct": improvement_pct,
        "best_schema": best_schema,
        "generations": generation_log,
        "evolved_format_example": evolved_example,
    }
    out_path = RESULTS_DIR / "ga_json_results.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nResults saved to {out_path}")

    # --- Convergence check vs ACF-seeded run ---
    acf_results_path = RESULTS_DIR / "ga_results.json"
    if acf_results_path.exists():
        acf_run = json.loads(acf_results_path.read_text())
        acf_best = acf_run["best_schema"]
        match = all(best_schema.get(k) == acf_best.get(k) for k in schema_mod.ACF_SEED)
        print("\n" + "=" * 70)
        print(f"CONVERGENCE vs ACF-seeded run: {'CONVERGED' if match else 'DIVERGED'}")
        if not match:
            for k in schema_mod.ACF_SEED:
                v_json = best_schema.get(k)
                v_acf = acf_best.get(k)
                marker = "  <-- differs" if v_json != v_acf else ""
                print(f"  {k}: json_evolved={v_json!r}  acf_evolved={v_acf!r}{marker}")
        else:
            print("Both lineages evolved to the same schema. Global optimum confirmed.")
        print("=" * 70)
    else:
        print("\n(ga_results.json not found — run phase5.ga first for convergence comparison)")


if __name__ == "__main__":
    main()
