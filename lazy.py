# Lazy load: keep only the light part of each node in memory, and read the
# heavy fields from disk only when asked.
# Reads the two files split.py made: index.json (each node's id, name, nodeType,
# dependencies, offset, length) and payloads.ndjson (one line per node with its
# columns and joinCondition).
# 1. Load only index.json, timing it and measuring memory the same way as
#    naive.py (tracemalloc started before the timer, MB = 1,000,000 bytes).
#    Compare to step 2: 0.83 s load, 170 MB current, 232 MB peak.
# 2. get_payload(node_id): look up the node's offset and length in the index,
#    open payloads.ndjson in "rb" mode, jump to the offset, read that many
#    bytes, and return them as a dict.
# 3. Time get_payload twice on the same node.
# 4. Test: for a few ids, get_payload(id) must exactly match that node's
#    columns and joinCondition in graph.json.

import json
import time
import tracemalloc

# start tracking memory 
tracemalloc.start()

# start the timer 
start = time.perf_counter()

# open index.json and parse it into a list called index
with open("index.json") as f:
    index = json.load(f)

# stop the timer
elapsed = time.perf_counter() - start

# read current and peak memory 
current, peak = tracemalloc.get_traced_memory()

# print the time and both memory numbers
print(f"load: {elapsed:.2f}s  current: {current / 1e6:.0f} MB  peak: {peak / 1e6:.0f} MB")


