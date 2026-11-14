#Load everything from the graph.json, measures memory
import json
import time
import tracemalloc

# start tracking memory 
tracemalloc.start()

# start the timer 
start = time.perf_counter()

#open graph.json and parse it into a list of nodes 
with open("graph.json") as f:
    nodes = json.load(f)

# stop the timer
elapsed = time.perf_counter() - start

# read current and peak memory 
current, peak = tracemalloc.get_traced_memory()

# print the time and both memory numbers
print(f"load: {elapsed:.2f}s  current: {current / 1e6:.0f} MB  peak: {peak / 1e6:.0f} MB")
