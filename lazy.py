# Lazy load: keep only the light part of each node in memory, and read the
# heavy fields from disk only when asked.
# Reads the two files split.py made: index.json (each node's id, name, nodeType,
# dependencies, offset, length) and payloads.ndjson (one line per node with its
# columns and joinCondition).
# 1. Load only index.json, timing it and measuring memory the same way as
#    naive.py (tracemalloc started before the timer, MB = 1,000,000 bytes).
# 2. get_payload(node_id): look up the node's offset and length in the index,
#    open payloads.ndjson in "rb" mode, jump to the offset, read that many
#    bytes, and return them as a dict.
# 3. Time get_payload twice on the same node.
# 4. Time fetching every node's payload, then check every payload against
#    graph.json: all 10,000 must match exactly.

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

# define get_payload(node_id):
def get_payload(node_id):
    # look up this node's entry in the index (index[node_id])
    entry = index[node_id]
    # open payloads.ndjson in "rb" mode
    with open("payloads.ndjson", "rb") as f:
        # jump to the entry's offset with seek()
        f.seek(entry["offset"])
        # read the entry's length in bytes with read()
        data = f.read(entry["length"])
    # turn the bytes into a dict with json.loads()
    payload = json.loads(data)
    # return the dict
    return payload

# sanity check: node 0's payload should have columns and joinCondition
print("payload keys:", list(get_payload(0).keys()))

# stop tracking memory with tracemalloc.stop(), since part 1 is done measuring and it slows timing down
tracemalloc.stop()

# pick a node id to test (not 0, which the try-it line already fetched)
node_id = 9000

# start the timer
start = time.perf_counter()

# call get_payload on that node
get_payload(node_id)

# stop the timer and convert to milliseconds
first_ms = (time.perf_counter() - start) * 1000

# start the timer again
start = time.perf_counter()

# call get_payload on the same node again
get_payload(node_id)

# stop the timer and convert to milliseconds
second_ms = (time.perf_counter() - start) * 1000

# print both times in milliseconds
print(f"first call: {first_ms:.3f} ms   second call: {second_ms:.3f} ms")

# 4a. average fetch time across all 10,000 nodes
# start the timer
start = time.perf_counter()
# for each entry in index:
for entry in index:
    # call get_payload on that entry's id
    get_payload(entry["id"])
# stop the timer and divide by the number of nodes to get the average in ms
average_ms = (time.perf_counter() - start) / len(index) * 1000
# print the average
print(f"average fetch: {average_ms:.3f} ms over {len(index):,} nodes")

# 4b. correctness test: check every node against graph.json
# open graph.json and parse it into a list called nodes
with open("graph.json") as f:
    nodes = json.load(f)
# start a mismatch counter at 0
mismatches = 0
# for each node in nodes:
for node in nodes:
    # get its payload with get_payload(node["id"])
    payload = get_payload(node["id"])
    # build the expected payload from the node's columns and joinCondition
    expected = {"columns": node["columns"], "joinCondition": node["joinCondition"]}
    # if the two aren't equal, add 1 to the mismatch counter
    if payload != expected:
        mismatches += 1
# print the number of mismatches (it should be 0)
print(f"mismatches: {mismatches} out of {len(nodes):,}")