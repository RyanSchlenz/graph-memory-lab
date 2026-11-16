# Lab log

Each step in order, with predictions written before running where I made them. Python 3.11.4 on an Apple M1 MacBook Air (8 GB). MB means 1,000,000 bytes.

## 1. Generate the graph (`generate.py`)

- 10,000 nodes. graph.json is 62,231,920 bytes.
- The seed is fixed, so regenerating produces the identical file. Every memory result below repeats exactly on the same Python version. Timings vary a little from run to run.

## 2. Naive load (`naive.py`)

- Load 0.83 s, current 170 MB, peak 232 MB.
- Peak minus current is 62 MB, about the size of graph.json. While parsing, `json.load` holds the raw file text and the parsed objects at the same time.

## 3. Where the memory goes (`breakdown.py`)

| Part | Predicted | Measured |
|---|---|---|
| Columns | 20% | 88.7% |
| SQL (joinCondition) | 70% | 7.8% |
| Light part (id, name, nodeType, dependencies) | 10% | 3.5% |

- Columns use 150.7 MB, but their text is only 31.0 MB. There are 350,410 columns (a dict and three strings each), averaging 430 bytes in memory for 88 characters of text, so about 79% is Python object overhead.
- The SQL text is 12.8 MB, close to the 13.3 MB of memory it uses, because it's one long string per node.
- The counts and text sizes were measured with a separate short script, not breakdown.py.

## 4. Split the file (`split.py`)

- index.json: 1,314,330 bytes. payloads.ndjson: 61,285,813 bytes.
- Check: the last entry's offset + length equals the size of payloads.ndjson (61,285,813). Passed.
- Check, with two temporary print lines: entry 0's length equals entry 1's offset, so each payload starts where the one before it ends. Passed.

## 5. Lazy load (`lazy.py`)

- Load 0.06 s (0.07 s on the first run), current 6 MB (6.49 MB exactly), peak 8 MB.
- Compared to naive: about 26x less memory (169.9 MB vs. 6.5 MB) and about 14x faster to load, with tracemalloc running for both.
- Without tracemalloc (best of 3 loads): graph.json 0.21 s, index.json 0.009 s.

## 6. Fetch timing (`lazy.py`)

These runs used temporary edits to lazy.py: a different node id, and an extra timed call on a second node.

| Run | First call | Same node again | Different node, after warm-up |
|---|---|---|---|
| Node 5000 | 0.500 ms | 0.056 ms | |
| Node 9000 | 0.477 ms | 0.048 ms | |
| Node 9000, then node 7000 | 0.531 ms | 0.054 ms | 0.265 ms |
| Same, after `sudo purge` | 0.472 ms | 0.064 ms | 0.235 ms |

- Average across all 10,000 nodes, fetched in id order: 0.041 ms (0.038 ms on another run).
- The "first call" isn't the first fetch in the run: lazy.py fetches node 0 once, untimed, before the timed calls.
- In one run after clearing the OS file cache, nothing got slower, so at this size the SSD isn't the bottleneck.
- Payload size doesn't explain why node 7000 was slower than repeating node 9000. Node 7000's payload is smaller (7,667 bytes and 50 columns, vs. 8,109 bytes and 54 columns). The slower fetch more likely comes from reading a part of the file that run hadn't touched yet.

## 7. Correctness (`lazy.py`)

- Every one of the 10,000 fetched payloads matches graph.json exactly: 0 mismatches.
- Tested the test with a temporary edit: with the expected joinCondition blanked out, it reported 10,000 mismatches.
