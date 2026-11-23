"""Project 4: Bank Queue Simulation with a Priority Queue -- your code.

Fill in every TODO (replace `raise NotImplementedError()`). Keep the function names and
arguments so that run_checks.py can test them. Then run:
    python run_checks.py           # tests (handout example + random tests)
    python run_example.py          # full report for data/example.txt (or another input file)
    python run_experiment.py       # doubling experiment, CSV and plot in results/
"""

from p4_env import *


# ============================================================================
# Task 1 — Your own priority queues
# ============================================================================

class MinHeap:
    """Binary min-heap stored in a list."""

    def __init__(self):
        self.Q = []

    def __len__(self):
        return len(self.Q)

    def insert(self, item):
        # TODO: append the item
        # TODO: heapify up: swap it with its parent (i - 1) // 2 while it is smaller
        raise NotImplementedError()

    def delete_min(self):
        # TODO: swap the root with the last item and pop the last item (that is the minimum)
        # TODO: heapify down from the root: swap with the smaller child while that child is smaller
        # TODO: return the minimum
        if len(self.Q) == 0:
            raise IndexError("Heap is empty")

        self.Q[0], self.Q[-1] = self.Q[-1], self.Q[0]
        minimum = self.Q.pop()

        i = 0
        n = len(self.Q)

        while 2 * i + 1 < n:
            left = 2 * i + 1
            right = 2 * i + 2
            smallest = left

            if right < n and self.Q[right] < self.Q[left]:
                smallest = right
            if self.Q[smallest] < self.Q[i]:
                self.Q[i], self.Q[smallest] = self.Q[smallest], self.Q[i]
                i = smallest
            else:
                break
        return minimum


class UnsortedListPQ:
    """Baseline priority queue: an unsorted list."""

    def __init__(self):
        self.items = []

    def __len__(self):
        return len(self.items)

    def insert(self, item):
        # TODO: append the item to the list
        raise NotImplementedError()

    def delete_min(self):
        # TODO: find the index of the smallest item with one scan
        # TODO: swap it with the last item, then pop and return it
        


# ============================================================================
# Tasks 2–4 — The event-driven simulation
# ============================================================================

class Bank:
    """State of the simulation (provided)."""

    def __init__(self, tellers, customers, patience, PQ, log):
        self.tellers = sorted(tellers, key=lambda t: t.service_time)    # fastest first
        self.customers = customers
        self.patience = patience
        self.events, self.waiting, self.free = PQ(), PQ(), PQ()
        self.status = ["new"] * len(customers)
        self.log = log
        for j, teller in enumerate(self.tellers):
            self.free.insert((teller.service_time, j))


def start_service(bank, t, i, j):
    """Teller j starts serving customer i at minute t."""
    # TODO: set bank.status[i] = "served" and call bank.log.start(t, customer, teller)
    # TODO: insert the completion event (t + service time of teller j, COMPLETION, j, i) into bank.events
    raise NotImplementedError()


def on_arrival(bank, t, i):
    """Customer i arrives at minute t."""
    c = bank.customers[i]
    bank.log.arrival(t, c)
    # TODO: if a teller is free: take the fastest free teller from bank.free and call start_service
    # TODO: otherwise: set the status to "waiting", insert (PRIORITY[c.cls], c.arrival, i) into bank.waiting, and insert the event (t + bank.patience, ABANDON, i, i)
    raise NotImplementedError()


def on_completion(bank, t, j, i):
    """Teller j finishes customer i at minute t."""
    bank.log.completion(t, bank.customers[i], bank.tellers[j])
    # TODO: take entries from bank.waiting until you find a customer whose status is still "waiting" (skip customers who left)
    # TODO: if you find one: teller j serves that customer now (start_service)
    # TODO: otherwise: teller j becomes free: insert (service_time, j) into bank.free
    raise NotImplementedError()


def on_abandon(bank, t, i):
    """Customer i's patience ends at minute t."""
    # TODO: only if the customer is still "waiting": set the status to "abandoned" and call bank.log.abandon(t, customer)
    # TODO: a customer who is already served does nothing
    raise NotImplementedError()


def simulate(tellers, customers, patience, PQ=None, keep_events=True):
    """Run the whole simulation and return the EventLog (provided)."""
    PQ = PQ or MinHeap
    log = EventLog(keep_events)
    bank = Bank(tellers, customers, patience, PQ, log)
    for i, c in enumerate(customers):
        bank.events.insert((c.arrival, ARRIVAL, i, i))
    while len(bank.events):
        t, kind, tie, i = bank.events.delete_min()
        if kind == COMPLETION:
            on_completion(bank, t, tie, i)
        elif kind == ARRIVAL:
            on_arrival(bank, t, i)
        else:
            on_abandon(bank, t, i)
    return log


# ============================================================================
# Full report (provided)
# ============================================================================

def analyze(source, events=60, plot=True):
    """Full report for a bank file (or text): event log and statistics. Provided."""
    tellers, customers, patience = read_bank(source)
    print("Tellers:", ", ".join(f"{t.name} ({t.service_time} min)" for t in tellers), f"| patience {patience} min")
    log = simulate(tellers, customers, patience)
    log.print_events(events)
    print()
    log.print_summary(tellers)
    if plot:
        log.plot_queue_length(path="results/queue_length.png")
    return log
