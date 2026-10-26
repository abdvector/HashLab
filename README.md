# HashLab

A focused Python and Streamlit hash collision simulator.

## Run

Requires Python 3.10 or newer. From the project folder:

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open http://localhost:8501. An optional virtual environment can be created with
`python -m venv .venv` before installing dependencies.

## Application scope

**Simulator:** choose a strategy and capacity, insert/search/delete integer keys,
inspect the table and operation steps, load five colliding sample keys, or clear
the table. Changing strategy or capacity starts a new table. Duplicate keys are
not inserted. Earlier steps show the state before the operation; the final step
shows its result.

Select **Library books** to add a book by its positive integer ID, title and shelf
location, find its details by ID, or remove it. Book records live inside the same
custom hash table: in linked nodes for chaining and corresponding array slots
for probing. A matching hash index never substitutes for matching the full ID.
Existing IDs keep their original details. Blank titles or shelf locations are
rejected. Switching data mode also clears the table; records are session-only.

For a short library demo, choose capacity 11 and load the collision sample.
IDs 12 and 23 both start at bucket 1. Find book 23 to retrieve "Python Basics",
shelf B3, through the selected collision strategy. Remove book 12, then find 23
again to demonstrate that deleting one colliding record preserves the others.

**Compare strategies:** run identical random or same-bucket workloads through all
three strategies. Compare average key comparisons across increasing load factors,
view the final results, and download measurements. Comparisons run only when
requested. The last completed run stays visible until the next run.

The interface contains operational controls and results. Theory, complexity
analysis, presentation notes, and team responsibilities belong in documentation
and slides rather than the application.

## Team of three

| Member | Code ownership | Demonstration responsibility |
| --- | --- | --- |
| 1 | `hashing.py`, algorithm tests in `tests/test_hashing.py` | Show insertion, search and deletion; explain chains, probing and deleted markers. |
| 2 | `app.py`, `styles.css`, `tests/test_app.py` | Demonstrate the user flow, collision sample and step inspection. |
| 3 | `experiments.py`, experiment tests in `tests/test_hashing.py` | Run random versus colliding inputs, compare graphs and explain the results. |

All members should understand the shared data flow: the interface calls the hash
table engine; the comparison module uses that same engine to collect measurements.

## Implementation notes

- Chaining uses actual linked-list nodes. Probing stores keys directly in an array.
- Prime capacities ensure `1 + k % (m - 1)` is a valid double-hashing step.
- Probe loops inspect at most `m` slots. Full tables return a result rather than loop indefinitely.
- Deleted markers preserve search paths. Insertion checks for duplicates before reusing a marker.
- Fixed capacities make comparisons reproducible. There is no resizing, database or external service.
- Random workloads use seed 42 in the interface. Present and absent keys come from disjoint ranges.
- `styles.css` contains only display styling; no JavaScript or external fonts are needed.

## Measurements

Load factor is stored keys divided by capacity. A bucket/slot visit counts one
array access; a key comparison counts equality testing against a live key.
Following chain nodes adds comparisons but not extra array bucket visits.

An insertion collision counts each unequal live key encountered during an
insertion attempt. Failed or duplicate attempts can add collisions too. Searches
and deletions do not add to this count. The simulator's total resets with its table.

Comparisons use unique keys, no deletions, and loads at or below 1 so every
strategy can store the same keys. Insertion averages include all keys inserted
so far. Successful searches cover every key present at a checkpoint; unsuccessful
searches use the same fixed sample of up to 100 absent keys for every strategy
and checkpoint. CSV exports also include insertion probe counts.

For presentation analysis: chaining search has expected cost O(1 + load factor)
under uniform hashing assumptions. Expected constant-time operations require
suitable hashing and controlled load; adverse inputs can require linear work.
The application reports operation counts rather than machine-dependent timings.

## Verification

```powershell
python -m unittest discover -s tests -v
```

Tests cover collisions, duplicates, deletion, full tables, complete double-hash
probe cycles, randomized operations against a reference set, reproducible
comparisons, and the Streamlit user flows.
