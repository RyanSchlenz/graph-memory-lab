# creates index.json and payloads.ndjson
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
        # break  # stop after one node while testing
        
        # turn the payload into a JSON string and add "\n"
        line = json.dumps(payload) + "\n"
        # encode the string to bytes
        data = line.encode()
        # get the offset with f.tell(), right before writing
        offset = out.tell()
        # write the bytes to the file
        out.write(data)
        # get the length with len() of the bytes
        length = len(data)
        print(offset, length)
        # break # stop after one node for testing
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
    json.dump(index_list,f)
# test: print the last entry's offset + length and the size of payloads.ndjson; they should match
last = index_list[-1]
print(last["offset"] + last["length"],
os.path.getsize("payloads.ndjson"))