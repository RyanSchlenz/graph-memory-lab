# creates index.json and payloads.ndjson

# open graph.json and parse it into a list of nodes
# start an empty list for the index

# open payloads.ndjson in binary mode ("wb"), because offsets are counted in bytes
    # for each node:
        # build the payload dict from the node's columns and joinCondition
        # turn the payload into a JSON string and add "\n"
        # encode the string to bytes
        # get the offset with f.tell(), right before writing
        # write the bytes to the file
        # get the length with len() of the bytes
        # build the index entry: the node's id, name, nodeType, dependencies, plus offset and length
        # add the entry to the index list

# save the index list to index.json (a normal text file, so plain "w" mode)

# test: print the last entry's offset + length and the size of payloads.ndjson; they should match