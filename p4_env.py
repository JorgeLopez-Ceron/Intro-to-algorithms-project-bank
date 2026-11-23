"""
Environment code for the CSCI 4100 group project (provided by the instructor).

You do not need to change this file. Your own code goes in starter.py
(or in the notebook cells marked TODO). This file gives you:
  * input readers and random data generators (fixed seeds, any size),
  * checkers that test your functions (the handout example + random tests),
  * timing helpers for the doubling experiment, and plotting helpers.
"""
import os, sys, io, csv, math, time, random, threading, contextlib

QUICK = os.environ.get("KIT_QUICK") == "1"     # smaller experiments (used only to test this kit)


def check(name, test):
    """Run one group of tests and print a one-line status."""
    try:
        run_with_big_stack(test)
        print(f"✅ {name}: all tests passed")
        return True
    except NotImplementedError:
        print(f"⏳ {name}: not implemented yet (finish the TODOs this test uses)")
    except AssertionError as e:
        print(f"❌ {name}: {e}")
    except Exception as e:
        print(f"❌ {name}: {type(e).__name__}: {e}")
    return False


def run_with_big_stack(fn, *args, **kwargs):
    """Call fn(*args, **kwargs) in a thread with a large stack, so that deep recursion
    (for example a recursive DFS on 10^5 vertices) does not crash Python."""
    sys.setrecursionlimit(max(sys.getrecursionlimit(), 1_000_000))
    box = {}

    def target():
        try:
            box["value"] = fn(*args, **kwargs)
        except BaseException as e:            # re-raised in the caller below
            box["error"] = e

    old = None
    for mb in (512, 256, 64):                 # some systems refuse very large thread stacks
        try:
            old = threading.stack_size(mb * 1024 * 1024)
            break
        except (ValueError, RuntimeError):
            continue
    try:
        t = threading.Thread(target=target)
        t.start()
        t.join()
    finally:
        if old is not None:
            threading.stack_size(old)
    if "error" in box:
        raise box["error"]
    return box.get("value")


def capture_output(fn, *args, **kwargs):
    """Run fn and return everything it printed, as a string."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        fn(*args, **kwargs)
    return buf.getvalue()


def doubling_experiment(methods, sizes, make_input, repeat=3, max_size=None, prepare=None, label="n"):
    """Time every method on every input size and print a doubling table.

    methods   : dict  name -> function(input)
    sizes     : list of input sizes (each one double the previous one)
    make_input: function n -> input (made once per size, not timed)
    repeat    : number of runs per size; the table shows the average
    max_size  : dict  name -> largest size to run that method (for slow methods)
    prepare   : function input -> argument passed to each run (not timed), e.g. list
                to give every run a fresh copy when a method changes its input
    Returns a list of rows {n, method, seconds} for save_csv / plot_doubling.
    """
    max_size = max_size or {}
    prepare = prepare or (lambda data: data)
    names = list(methods)
    print(f"{label:>10} | " + " | ".join(f"{name:>26}" for name in names))
    print("-" * (12 + 29 * len(names)))
    rows, prev = [], {}
    for n in sizes:
        try:
            data = run_with_big_stack(make_input, n)
        except NotImplementedError:
            print(f"{n:>10} | " + " | ".join(f"{'(not implemented)':>26}" for _ in names))
            continue
        cells = []
        for name in names:
            if n > max_size.get(name, float("inf")):
                cells.append(f"{'(skipped: too slow)':>26}")
                continue
            try:
                total = 0.0
                for _ in range(repeat):
                    arg = prepare(data)
                    t0 = time.perf_counter()
                    run_with_big_stack(methods[name], arg)
                    total += time.perf_counter() - t0
            except NotImplementedError:
                cells.append(f"{'(not implemented)':>26}")
                continue
            t = total / repeat
            ratio = ""
            if name in prev and prev[name][0] * 2 == n and prev[name][1] > 0:
                ratio = f"x{t / prev[name][1]:.2f}"
            prev[name] = (n, t)
            rows.append({"n": n, "method": name, "seconds": t})
            cells.append(f"{t * 1000:>14.1f} ms {ratio:>8}")
        print(f"{n:>10} | " + " | ".join(cells), flush=True)
    return rows


def save_csv(rows, path):
    """Save experiment rows (list of dicts) as a CSV file for your report."""
    if not rows:
        return
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print("saved", path)


def _plt():
    import matplotlib
    if "ipykernel" not in sys.modules:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    return plt


def _finish(plt, path):
    if path:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        plt.savefig(path, dpi=150, bbox_inches="tight")
        print("saved", path)
    if "ipykernel" in sys.modules:
        plt.show()
    plt.close()


def plot_doubling(rows, title="", path=None):
    """Log-log plot of running time against n, one line per method."""
    if not rows:
        print("nothing to plot yet")
        return
    plt = _plt()
    plt.figure(figsize=(6, 4))
    for name in dict.fromkeys(r["method"] for r in rows):
        pts = [(r["n"], r["seconds"]) for r in rows if r["method"] == name]
        plt.loglog([p[0] for p in pts], [p[1] for p in pts], "o-", label=name)
    plt.xlabel("n")
    plt.ylabel("average time (s)")
    plt.title(title)
    plt.grid(True, which="both", alpha=0.3)
    plt.legend()
    _finish(plt, path)

# ===========================================================================
# Project 4: Bank Queue Simulation with a Priority Queue
# ===========================================================================

CLASSES = ("VIP", "Elderly", "Regular")
PRIORITY = {"VIP": 0, "Elderly": 1, "Regular": 2}     # smaller = served first
COMPLETION, ARRIVAL, ABANDON = 0, 1, 2                 # order of events at the same time


class Teller:
    __slots__ = ("name", "service_time")

    def __init__(self, name, service_time):
        self.name, self.service_time = name, service_time

    def __repr__(self):
        return f"Teller({self.name!r}, {self.service_time})"


class Customer:
    __slots__ = ("id", "arrival", "cls")

    def __init__(self, id, arrival, cls):
        self.id, self.arrival, self.cls = id, arrival, cls

    def __repr__(self):
        return f"Customer({self.id!r}, {self.arrival}, {self.cls!r})"


EXAMPLE_TEXT = """\
# teller, name, service time in minutes (fastest first)
teller, T1, 3
teller, T2, 5
patience, 4
# customer id, arrival minute, class
C1, 0, Regular
C2, 1, Regular
C3, 2, Elderly
C4, 3, VIP
C5, 4, Regular
C6, 5, VIP
C7, 6, Regular
"""


def parse_bank(text):
    """Parse the bank format (see data/example.txt). Returns (tellers, customers, patience)."""
    tellers, customers, patience = [], [], None
    for no, raw in enumerate(text.splitlines(), 1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        parts = [p.strip() for p in line.split(",")]
        if parts[0] == "teller" and len(parts) == 3:
            tellers.append(Teller(parts[1], int(parts[2])))
        elif parts[0] == "patience" and len(parts) == 2:
            patience = int(parts[1])
        elif len(parts) == 3 and parts[2] in PRIORITY:
            customers.append(Customer(parts[0], int(parts[1]), parts[2]))
        else:
            raise ValueError(f"line {no}: cannot parse {raw!r}")
    if not tellers or patience is None:
        raise ValueError("the input needs at least one teller line and a patience line")
    customers.sort(key=lambda c: c.arrival)          # stable: input order within the same minute
    return tellers, customers, patience


def read_bank(path_or_text):
    if "\n" in path_or_text:
        return parse_bank(path_or_text)
    with open(path_or_text) as f:
        return parse_bank(f.read())


def write_bank(path, tellers, customers, patience):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        f.write("# teller, name, service time in minutes (fastest first)\n")
        for t in tellers:
            f.write(f"teller, {t.name}, {t.service_time}\n")
        f.write(f"patience, {patience}\n# customer id, arrival minute, class\n")
        for c in customers:
            f.write(f"{c.id}, {c.arrival}, {c.cls}\n")


def generate_bank(n, k=5, seed=0, patience=15, load=0.95, mix=(0.1, 0.2, 0.7)):
    """Random bank day: k tellers (service times 3..8 minutes, fastest first) and n customers.
    Arrivals are random (exponential gaps, rounded to whole minutes) at about `load` times the
    tellers' capacity; classes VIP / Elderly / Regular with probabilities `mix`.
    Returns (tellers, customers, patience)."""
    rng = random.Random(seed)
    tellers = [Teller(f"T{j + 1}", s) for j, s in enumerate(sorted(rng.randint(3, 8) for _ in range(k)))]
    rate = load * sum(1 / t.service_time for t in tellers)
    customers, clock = [], 0.0
    w = len(str(n))
    for i in range(n):
        clock += rng.expovariate(rate)
        r = rng.random()
        cls = "VIP" if r < mix[0] else ("Elderly" if r < mix[0] + mix[1] else "Regular")
        customers.append(Customer(f"C{i + 1:0{w}d}", int(clock), cls))
    return tellers, customers, patience


def write_example_files(folder="data"):
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, "example.txt"), "w") as f:
        f.write(EXAMPLE_TEXT)
    write_bank(os.path.join(folder, "random_60.txt"), *generate_bank(60, k=3, seed=4100, patience=10))


class EventLog:
    """Records the simulation and computes the statistics. Your handlers call
         log.arrival(t, customer)          log.start(t, customer, teller)
         log.completion(t, customer, teller)   log.abandon(t, customer)
    keep_events=False keeps only the totals (for very large experiments)."""

    def __init__(self, keep_events=True):
        self.keep = keep_events
        self.events = []                              # (time, kind, customer id, teller name)
        self.starts, self.abandons = [], []           # (customer id, time, teller name), (customer id, time)
        self.arrived = {c: 0 for c in CLASSES}
        self.served = {c: 0 for c in CLASSES}
        self.left = {c: 0 for c in CLASSES}
        self.wait_sum = {c: 0 for c in CLASSES}
        self.busy = {}
        self.last_completion = 0

    def arrival(self, t, c):
        self.arrived[c.cls] += 1
        if self.keep:
            self.events.append((t, "arrival", c.id, ""))

    def start(self, t, c, teller):
        self.served[c.cls] += 1
        self.wait_sum[c.cls] += t - c.arrival
        self.busy[teller.name] = self.busy.get(teller.name, 0) + teller.service_time
        if self.keep:
            self.events.append((t, "start", c.id, teller.name))
            self.starts.append((c.id, t, teller.name))

    def completion(self, t, c, teller):
        self.last_completion = max(self.last_completion, t)
        if self.keep:
            self.events.append((t, "completion", c.id, teller.name))

    def abandon(self, t, c):
        self.left[c.cls] += 1
        if self.keep:
            self.events.append((t, "abandon", c.id, ""))
            self.abandons.append((c.id, t))

    def summary(self, tellers):
        total = sum(self.arrived.values())
        return {
            "customers": total,
            "served": sum(self.served.values()),
            "abandoned": sum(self.left.values()),
            "avg_wait": {c: (self.wait_sum[c] / self.served[c] if self.served[c] else None) for c in CLASSES},
            "abandonment_rate": (sum(self.left.values()) / total) if total else 0.0,
            "utilization": {t.name: (self.busy.get(t.name, 0) / self.last_completion if self.last_completion else 0.0)
                            for t in tellers},
        }

    def print_events(self, limit=60):
        for t, kind, cid, tname in self.events[:limit]:
            print(f"t={t:<6} {kind:<11} {cid}" + (f" ({tname})" if tname else ""))
        if len(self.events) > limit:
            print(f"... ({len(self.events) - limit} more events)")

    def print_summary(self, tellers):
        s = self.summary(tellers)
        print(f"Customers: {s['customers']}, served: {s['served']}, abandoned: {s['abandoned']}")
        print("Average wait of served customers: " + ", ".join(
            f"{c} {s['avg_wait'][c]:.2f}" if s['avg_wait'][c] is not None else f"{c} -" for c in CLASSES) + " minutes")
        print(f"Abandonment rate: {s['abandoned']}/{s['customers']} = {100 * s['abandonment_rate']:.1f}%")
        print("Utilization: " + ", ".join(f"{k} {100 * v:.1f}%" for k, v in s["utilization"].items())
              + f" (last completion at minute {self.last_completion})")

    def plot_queue_length(self, path=None, title="Customers waiting"):
        """Step plot of the number of waiting customers over time (needs keep_events=True)."""
        plt = _plt()
        q, xs, ys = 0, [0], [0]
        for t, kind, cid, tname in self.events:
            if kind == "arrival":
                q += 1
            elif kind in ("start", "abandon"):
                q -= 1
            else:
                continue
            xs.append(t)
            ys.append(q)
        plt.figure(figsize=(7, 3))
        plt.step(xs, ys, where="post")
        plt.xlabel("minute")
        plt.ylabel("waiting")
        plt.title(title)
        plt.grid(True, alpha=0.3)
        _finish(plt, path)


# ---------- test cases -------------------------------------------------------

def _bank(tellers, customers, patience):
    return ([Teller(n, s) for n, s in tellers], [Customer(i, a, c) for i, a, c in customers], patience)


SCENARIOS = [
    ("events at the same minute: completions, then arrivals, then abandonments",
     _bank([("T1", 2)], [("C1", 0, "Regular"), ("C2", 0, "Regular"), ("C3", 2, "VIP")], 2),
     [("C1", 0, "T1"), ("C2", 2, "T1"), ("C3", 4, "T1")], []),
    ("priority by class, first come first served within a class",
     _bank([("T1", 10)], [("C1", 0, "Regular"), ("C2", 1, "Regular"), ("C3", 2, "Elderly"), ("C4", 3, "VIP"),
                          ("C5", 4, "VIP"), ("C6", 5, "Elderly")], 100),
     [("C1", 0, "T1"), ("C4", 10, "T1"), ("C5", 20, "T1"), ("C3", 30, "T1"), ("C6", 40, "T1"), ("C2", 50, "T1")], []),
    ("the fastest free teller serves an arriving customer",
     _bank([("T1", 3), ("T2", 4)], [("C1", 0, "Regular"), ("C2", 0, "Regular"), ("C3", 0, "VIP")], 10),
     [("C1", 0, "T1"), ("C2", 0, "T2"), ("C3", 3, "T1")], []),
    ("a waiting customer leaves at arrival + patience",
     _bank([("T1", 5)], [("C1", 0, "Regular"), ("C2", 1, "Regular"), ("C3", 2, "VIP")], 3),
     [("C1", 0, "T1"), ("C3", 5, "T1")], [("C2", 4)]),
]

# totals for generate_bank(300, k=3, seed=s, patience=8): (served, abandoned, total wait of served customers)
RANDOM_TOTALS = {0: (288, 12, 629), 1: (284, 16, 696), 2: (274, 26, 742)}


def _check_log_rules(tellers, customers, patience, log):
    arrival = {c.id: c.arrival for c in customers}
    seen = [cid for cid, t, tn in log.starts] + [cid for cid, t in log.abandons]
    assert sorted(seen) == sorted(arrival), "every customer must be served or leave exactly once"
    for cid, t in log.abandons:
        assert t == arrival[cid] + patience, f"{cid} must leave at arrival + patience = {arrival[cid] + patience}, not {t}"
    for cid, t, tn in log.starts:
        assert arrival[cid] <= t <= arrival[cid] + patience, f"{cid} starts at {t}: before arrival or after leaving"
    speed = {t.name: t.service_time for t in tellers}
    busy_until = {}
    for cid, t, tn in sorted(log.starts, key=lambda x: x[1]):
        assert busy_until.get(tn, -1) <= t, f"teller {tn} serves two customers at minute {t}"
        busy_until[tn] = t + speed[tn]


# ---------- checkers --------------------------------------------------------

def check_task1(MinHeap, UnsortedListPQ):
    def test():
        for PQ in (MinHeap, UnsortedListPQ):
            rng = random.Random(7)
            q, ref = PQ(), []
            for _ in range(3000):
                if ref and rng.random() < 0.45:
                    ref.sort()
                    got = q.delete_min()
                    assert got == ref.pop(0), f"{PQ.__name__}.delete_min returned {got}, not the smallest item"
                else:
                    x = (rng.randint(0, 40), rng.randint(0, 2), rng.randrange(10 ** 6))
                    q.insert(x)
                    ref.append(x)
                assert len(q) == len(ref), f"len() of {PQ.__name__} is wrong"
    return check("Task 1: MinHeap and UnsortedListPQ", test)


def check_task2(simulate):
    def test():
        tellers, customers, patience = parse_bank(EXAMPLE_TEXT)
        log = simulate(tellers, customers, patience)
        want = [("C1", 0, "T1"), ("C2", 1, "T2"), ("C3", 3, "T1"), ("C4", 6, "T1"), ("C6", 6, "T2"), ("C7", 9, "T1")]
        assert log.starts == want, f"example service starts: expected {want}, got {log.starts}"
        assert log.abandons == [("C5", 8)], f"example: C5 leaves at 8, got {log.abandons}"
        s = log.summary(tellers)
        assert s["avg_wait"] == {"VIP": 2.0, "Elderly": 1.0, "Regular": 1.0}, f"average waits: {s['avg_wait']}"
        assert abs(s["abandonment_rate"] - 1 / 7) < 1e-9, "abandonment rate should be 1/7"
        assert s["utilization"]["T1"] == 1.0 and abs(s["utilization"]["T2"] - 10 / 12) < 1e-9, \
            f"utilization: {s['utilization']}"
    return check("Tasks 2-4: simulation of the handout example", test)


def check_task3(simulate, MinHeap, UnsortedListPQ):
    def test():
        for name, (tellers, customers, patience), starts, abandons in SCENARIOS:
            log = simulate(tellers, customers, patience)
            assert log.starts == starts and log.abandons == abandons, \
                f"{name}: expected starts {starts} and leaves {abandons}, got {log.starts} and {log.abandons}"
        for seed in range(3):
            tellers, customers, patience = generate_bank(300, k=3, seed=seed, patience=8)
            log = simulate(tellers, customers, patience)
            _check_log_rules(tellers, customers, patience, log)
            if seed in RANDOM_TOTALS:
                got = (sum(log.served.values()), sum(log.left.values()), sum(log.wait_sum.values()))
                assert got == RANDOM_TOTALS[seed], f"random day {seed}: expected (served, left, total wait) {RANDOM_TOTALS[seed]}, got {got}"
            log2 = simulate(tellers, customers, patience, PQ=UnsortedListPQ)
            assert log2.starts == log.starts and log2.abandons == log.abandons, \
                "MinHeap and UnsortedListPQ must give the same simulation"
    return check("Tasks 2-4: special cases and random days", test)
