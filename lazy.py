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