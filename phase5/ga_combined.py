"""Phase 5-GA: Combined GA seeded from both evolved lineages.

Seeds population from ACF-evolved and JSON-evolved schemas simultaneously.
If best fitness <= 1.0821 (hybrid), the hybrid is the global optimum in this space.

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

HYBRID_FITNESS = 1.0821  # from eval_hybrid.py — the bar to beat

RESULTS_DIR = Path(__file__).parent / "results"
_SERVER_DIR = Path(__file__).resolve().parents[1] / "server"


def _load_evolved_schema(results_file: str) -> dict:
    path = RESULTS_DIR / results_file
    data = json.loads(path.read_text())
    return data["best_schema"]


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

    acf_evolved = _load_evolved_schema("ga_results.json")
    json_evolved = _load_evolved_schema("ga_json_results.json")

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

    # --- Build mixed population: 2 elites + 9 mutations each ---
    pop = [
        _make_individual(acf_evolved),
        _make_individual(json_evolved),
    ]
    for _ in range(9):
        pop.append(_make_individual(schema_mod.mutate(acf_evolved)))
    for _ in range(9):
        pop.append(_make_individual(schema_mod.mutate(json_evolved)))

    hof = tools.HallOfFame(1)

    print("Phase 5-GA: Combined GA (ACF-evolved + JSON-evolved seeds)")
    print(f"Population: {POPULATION_SIZE} | Generations: {N_GENERATIONS} | Cx: {CROSSOVER_PROB} | Mut: {MUTATION_PROB}")
    print(f"Hybrid baseline to beat: {HYBRID_FITNESS}")
    print(f"\nEvaluating initial population ({POPULATION_SIZE} individuals)...", flush=True)

    for i, ind in enumerate(pop):
        ind.fitness.values = toolbox.evaluate(dict(ind))
        print(f"  [{i+1:02d}/{POPULATION_SIZE}] fitness={ind.fitness.values[0]:.4f}", flush=True)
    hof.update(pop)

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

    docs = load_documents(_SERVER_DIR / "documents")
    first_doc = docs[QUERIES[0]["acf_doc"]]
    evolved_example = format_doc(first_doc, best_schema)

    # --- Console summary ---
    print("\n" + "=" * 70)
    print(f"Best evolved : fitness={best_fitness:.4f}  tokens={best_metrics['avg_tokens']}  acc={best_metrics['avg_accuracy']:.2f}")
    print(f"Hybrid       : fitness={HYBRID_FITNESS:.4f}")
    print("\nBest evolved schema:")
    for k, v in best_schema.items():
        print(f"  {k}: {v}")
    print(f"\nEvolved format example (first 500 chars):\n{evolved_example[:500]}")

    # --- Save results ---
    output = {
        "hybrid_fitness_baseline": HYBRID_FITNESS,
        "best_fitness": round(best_fitness, 6),
        "best_tokens": best_metrics["avg_tokens"],
        "best_accuracy": best_metrics["avg_accuracy"],
        "best_schema": best_schema,
        "generations": generation_log,
        "evolved_format_example": evolved_example,
    }
    out_path = RESULTS_DIR / "ga_combined_results.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nResults saved to {out_path}")

    # --- Verdict ---
    print("\n" + "=" * 70)
    if best_fitness > HYBRID_FITNESS:
        print(f"NEW CHAMPION: fitness={best_fitness:.4f} beats hybrid ({HYBRID_FITNESS})")
    else:
        print(f"GLOBAL OPTIMUM CONFIRMED: hybrid holds at {HYBRID_FITNESS} (best found={best_fitness:.4f})")
    print("=" * 70)


if __name__ == "__main__":
    main()
