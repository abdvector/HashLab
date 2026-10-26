"""Deterministic, reproducible comparisons over identical integer workloads."""

import random
from statistics import mean

from hashing import HashTable, STRATEGIES


def run_experiment(size: int, distribution: str, seed: int, max_load: float):
    rng = random.Random(seed)
    count = max(1, min(size, int(size * max_load)))
    if distribution == "Same initial bucket":
        keys = [3 + size * i for i in range(count)]
        misses = [3 + size * (count + i) for i in range(min(100, size))]
    else:
        keys = rng.sample(range(size * 100), count)
        # Disjoint ranges guarantee absent queries without a retry loop.
        misses = rng.sample(range(size * 100, size * 200), min(100, size))
    checkpoints = {max(1, round(count * i / 10)) for i in range(1, 11)}
    rows, summary = [], []
    for strategy in STRATEGIES:
        table = HashTable(size, strategy)
        inserts = []
        for position, key in enumerate(keys, 1):
            inserts.append(table.operate("Insert", key, trace=False))
            if position not in checkpoints:
                continue
            hits = [table.operate("Search", k, trace=False) for k in keys[:position]]
            absent = [table.operate("Search", k, trace=False) for k in misses]
            row = {
                "Strategy": strategy,
                "Keys": position,
                "Load factor": position / size,
                "Successful search comparisons": mean(r.comparisons for r in hits),
                "Unsuccessful search comparisons": mean(r.comparisons for r in absent),
                "Insertion comparisons": mean(r.comparisons for r in inserts),
                "Insertion probes": mean(r.probes for r in inserts),
                "Insertion collisions": sum(r.collisions for r in inserts),
            }
            rows.append(row)
        summary.append(row.copy())
    return rows, summary, keys
