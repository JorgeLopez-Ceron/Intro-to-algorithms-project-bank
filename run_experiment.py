"""Doubling experiment: python run_experiment.py (writes results/*.csv and results/*.png)"""
from p4_env import *
from starter import *

HEAP_SIZES = [62500, 125000, 250000, 500000, 1000000]
LIST_SIZES = [500, 1000, 2000, 4000, 8000]
if QUICK:
    HEAP_SIZES, LIST_SIZES = [2000, 4000], [500, 1000]


def make_input(n):
    return generate_bank(n, k=5, seed=n)


def run_with(PQ):
    return lambda data: simulate(*data, PQ=PQ, keep_events=False)


print("MinHeap")
rows = doubling_experiment({"MinHeap": run_with(MinHeap)}, HEAP_SIZES, make_input)
print("\nUnsorted list")
rows += doubling_experiment({"UnsortedListPQ": run_with(UnsortedListPQ)}, LIST_SIZES, make_input)
save_csv(rows, "results/experiment.csv")
plot_doubling(rows, "Project 4: whole simulation", "results/experiment.png")

try:
    tellers, customers, patience = generate_bank(HEAP_SIZES[0], k=5, seed=1)
    print()
    simulate(tellers, customers, patience, keep_events=False).print_summary(tellers)
except NotImplementedError:
    pass
