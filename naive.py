#Load everything from the graph.json, measures memory
import json
import time
import tracemalloc

tracemalloc.start()
start = time.perf_counter()

with open("graph.json") as f:
    nodes = json.load(f)

elapsed = time.perf_counter() - start
current, peak = tracemalloc.get_traced_memory()
print(f"load: {elapsed:.2f}s  current: {current / 1e6:.0f} MB  peak: {peak / 1e6:.0f} MB")