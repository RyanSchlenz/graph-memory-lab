# graph-memory-lab

How much memory does a pipeline graph use when every node is loaded in full, where does that memory go, and how much does lazy loading save? This lab measures it on a generated data-lineage graph of 10,000 nodes. Each node is a warehouse table with 10 to 60 columns of metadata, 500 to 2,000 characters of SQL, and up to 5 dependencies.

## The idea

A graph view only needs each node's id, name, type, and dependencies. The heavy parts, the column metadata and the SQL, are only needed when someone opens a node. It's like selecting only the fields you need instead of `SELECT *`.

So `split.py` writes each node's columns and SQL (its payload) as one line in `payloads.ndjson`. It also writes an index with each node's light fields plus the byte offset and length of its payload. `lazy.py` keeps only the index in memory. Fetching a node's details means jumping to its offset in the payload file and reading that many bytes.

Step-by-step notes, including my predictions before each run, are in [LOG.md](LOG.md).

## How to run

Run these from the repo folder, in order:

```
python3 generate.py      # creates graph.json: 10,000 nodes, 62,231,920 bytes, fixed seed
python3 naive.py         # loads everything, measures load time and memory
python3 breakdown.py     # measures how much memory the columns, SQL, and light fields use
python3 split.py         # creates index.json and payloads.ndjson, checks the offsets
python3 lazy.py          # loads only the index, fetches payloads on demand, checks every node
```

Standard library only, no packages to install. Requires Python 3.9 or newer. The generated data files aren't committed; `generate.py` recreates the same graph.json on every run. Each script keeps its step-by-step plan as comments, written before the code.

The results below were measured with Python 3.11.4 on an Apple M1 MacBook Air with 8 GB of RAM. Memory numbers shift a little between Python versions because object sizes change (Python 3.13 used 161 MB for the naive load), so use Python 3.11 to reproduce them exactly. MB means 1,000,000 bytes.

## Results

| Approach | Load time | Current memory | Peak memory |
|---|---|---|---|
| Naive (load everything) | 0.83 s | 170 MB | 232 MB |
| Lazy (index in memory, payloads on disk) | 0.06 s | 6 MB | 8 MB |

Memory is measured with Python's `tracemalloc`. Current is what's still allocated after loading, and peak is the most that was allocated at any point during the load. It counts Python's own allocations, so the whole process uses somewhat more. Both load times were measured with tracemalloc running, which slows loading down. Without it, the naive load takes about 0.21 s and the lazy load about 0.01 s.

**Where the naive 170 MB goes** (`breakdown.py`):

| Part of each node | Share of memory |
|---|---|
| Columns (name, dataType, and description for each column) | 88.7% |
| SQL (joinCondition) | 7.8% |
| Light part (id, name, nodeType, dependencies) | 3.5% |

**Fetching one node's columns and SQL on demand** (`lazy.py`):

| Fetch | Time |
|---|---|
| First fetch of a node (after one earlier, untimed fetch) | about 0.5 ms |
| A different node, after warm-up* | about 0.25 ms |
| The same node again | about 0.05 ms |
| Average over all 10,000 nodes, fetched in id order | 0.04 ms |

Single measurements vary from run to run. *Measured with a temporary edit to lazy.py; see LOG.md.

All 10,000 fetched payloads matched graph.json exactly. To make sure that check could fail, I broke the expected value on purpose, and it reported 10,000 mismatches.

## Findings

1. **Lazy loading cut memory from 170 MB to 6 MB, and load time from 0.83 s to 0.06 s.** Only the index stays in memory, and it's 1.3 MB on disk versus 62 MB for the full graph.
2. **Column metadata, not SQL, is where the memory goes: 88.7%, or 150.7 MB.** The column text itself is only 31 MB. Most of the rest is Python object overhead: 350,410 columns, each a dict holding three strings, average 430 bytes in memory for 88 characters of text. That makes about 79% of the column memory overhead. The SQL is 10,000 long strings, so its memory (13.3 MB) is close to its text size (12.8 MB).
3. **Peak minus current is about the file size.** For the naive load, 232 − 170 = 62 MB, which matches graph.json (62.2 MB). `json.load` holds the whole file as one string while it builds the objects.
4. **Fetching on demand is cheap.** Fetching all 10,000 nodes in id order averaged 0.04 ms each. A single fetch took about 0.05 to 0.3 ms, and the first one about 0.5 ms, all far below anything a user would notice. In one run after clearing the macOS file cache (`sudo purge`), fetches were no slower, so the disk isn't the slow part at this size. I haven't pinned down exactly what the first-fetch cost is.

## What surprised me

I predicted the SQL would be the biggest piece (70%) and the columns about 20%. It was the opposite. Even as plain text, the columns are bigger than the SQL (31 MB vs. 12.8 MB), but what really multiplied them was per-object overhead. About 1.4 million small objects (350,410 dicts and 1.05 million strings) cost far more than their characters.

I also expected the disk to be the slow part of lazy loading, but clearing the file cache made no visible difference.

## What I'd try next

- **Lineage queries:** walk upstream and downstream dependencies (breadth-first search) on both versions, to show the index alone can answer lineage questions. `lineage.py` is a placeholder for this.
- **Random-order fetches:** the 10,000-fetch average reads the file in order, which is the friendliest case for every cache. Shuffled ids would be more realistic.
- **Keep the payload file open and cache recent payloads,** instead of reopening the file on every fetch.
- **Share repeated strings:** the generated columns use only 1,258 distinct strings, so interning them could remove much of the overhead without lazy loading. Real metadata repeats less, especially descriptions.
- **Lighter column objects,** such as tuples instead of dicts, to see how much of the overhead goes away.
