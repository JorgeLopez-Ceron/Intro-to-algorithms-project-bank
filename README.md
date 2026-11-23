# Project 4 — Bank Queue Simulation with a Priority Queue: Starter Kit

Read the project handout first. This kit gives you the "environment" so you can spend your time on the heap and the event logic.

## Files
| File | What it is | Edit? |
|---|---|---|
| `starter.py` | **Your code.** The priority queues, the event handlers (TODO), and the provided `Bank` state and `simulate` loop. | yes |
| `p4_env.py` | Provided environment: `Teller`, `Customer`, input reader, random bank-day generator, `EventLog` (event log, statistics, queue-length plot), checkers, timing and plotting helpers. | no |
| `run_checks.py` | Runs the tests (handout example, special cases for the tie rules, random days). | no |
| `run_example.py` | Event log, statistics, and queue-length plot for an input file. | no |
| `run_experiment.py` | Doubling experiment (MinHeap against the unsorted list); saves `results/experiment.csv` and `results/experiment.png`. | sizes only |
| `data/` | `example.txt` (handout example), `random_60.txt`. | add your own |
| `Project_4_Bank_Simulation_Colab.ipynb` | The same kit as one notebook for Google Colab. | yes |

## How to run
Python 3.9+ and matplotlib (for the plots).
```
python run_checks.py                        # tests: aim for all ✅
python run_example.py                       # report for data/example.txt
python run_example.py data/random_60.txt    # another input file
python run_experiment.py                    # experiment (a few minutes for 10^6 customers)
```
In Colab: upload the notebook (File → Upload notebook) and run it from the top.

## What you write (starter.py)
| Handout task | Functions |
|---|---|
| 1. Your own binary min-heap as the event queue | `MinHeap.insert`, `MinHeap.delete_min` |
| 2. A second heap for the waiting line | used in `on_arrival` and `on_completion` |
| 3. Run the simulation, print the event log | `start_service`, `on_arrival`, `on_completion`, `on_abandon` (the provided `simulate` calls them; `EventLog` prints the log) |
| 4. Statistics | computed by `EventLog.summary` from what your handlers log |
| 5. Experiment | `UnsortedListPQ` + run `run_experiment.py` |

## Rules
Implement both priority queues yourself (no `heapq`, no sorting). You may add helper functions and change anything in `starter.py`, but keep the names and arguments so the checkers still work. Passing the checkers is necessary but not the whole grade.
