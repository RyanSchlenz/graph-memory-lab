# Measure how much memory each part of a node uses. Load graph.json and record
# current memory, delete the columns from every node and measure again, then
# delete joinCondition from every node and measure again. What's left is the
# light part of each node: id, name, nodeType, dependencies.
import json
import tracemalloc
import gc

# start tracking memory
tracemalloc.start()

# open graph.json and parse it into a list of nodes
with open("graph.json") as f:
    nodes = json.load(f)

# record current memory as before
before = tracemalloc.get_traced_memory()[0]
print(f"before:        {before / 1e6:.1f} MB")

# delete columns from every node
for node in nodes:
    del node["columns"]

# clean up leftover garbage with gc.collect()
gc.collect()

# record current memory as after_columns
after_columns = tracemalloc.get_traced_memory()[0]
print(f"after columns: {after_columns / 1e6:.1f} MB")

# delete joinCondition from every node
for node in nodes:
    del node["joinCondition"]

# clean up leftover garbage with gc.collect()
gc.collect()

# record current memory as after_sql
after_sql = tracemalloc.get_traced_memory()[0]
print(f"after SQL:     {after_sql / 1e6:.1f} MB")

# print one node to check that only id, name, nodeType, and dependencies are left
print(nodes[0])

# calculate the columns, SQL, and light-part percents, each out of before
columns_pct = (before - after_columns) / before * 100
sql_pct = (after_columns - after_sql) / before * 100
light_pct = after_sql / before * 100

# print the three percentages
print(f"columns: {columns_pct:.1f}%")
print(f"SQL:     {sql_pct:.1f}%")
print(f"light:   {light_pct:.1f}%")
print(f"total:   {columns_pct + sql_pct + light_pct:.1f}%")  # should be 100.0
