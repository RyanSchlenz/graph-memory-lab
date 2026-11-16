# Split graph.json into two files:
#   index.json      - the light part of each node (id, name, nodeType, dependencies)
#                     plus the offset and length of its payload in payloads.ndjson
#   payloads.ndjson - one line per node with its columns and joinCondition
import os
import json

# open graph.json and parse it into a list of nodes
with open("graph.json") as f:
    nodes = json.load(f)

# start an empty list for the index
index_list = []

# open payloads.ndjson in binary mode ("wb"), because offsets are counted in bytes
with open("payloads.ndjson", "wb") as out:
    # for each node:
    for node in nodes:
        # build the payload dict from the node's columns and joinCondition
        payload = {"columns": node["columns"], "joinCondition": node["joinCondition"]}
        # turn the payload into a JSON string and add "\n"
        line = json.dumps(payload) + "\n"
        # encode the string to bytes
        data = line.encode()
        # get the offset with out.tell(), right before writing
        offset = out.tell()
        # write the bytes to the file
        out.write(data)
        # get the length with len() of the bytes
        length = len(data)
        # build the index entry: the node's id, name, nodeType, dependencies, plus offset and length
        entry = {
            "id": node["id"],
            "name": node["name"],
            "nodeType": node["nodeType"],
            "dependencies": node["dependencies"],
            "offset": offset,
            "length": length,
        }
        # add the entry to the index list
        index_list.append(entry)

# save the index list to index.json (a normal text file, so plain "w" mode)
with open("index.json", "w") as f:
    json.dump(index_list, f)

# test: the last entry's offset + length should equal the size of payloads.ndjson
last = index_list[-1]
expected_size = last["offset"] + last["length"]
actual_size = os.path.getsize("payloads.ndjson")
print(f"last offset + length: {expected_size:,}")
print(f"payloads.ndjson size: {actual_size:,}")
print("PASS" if expected_size == actual_size else "FAIL")
