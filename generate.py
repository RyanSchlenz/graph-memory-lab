"""Generate graph.json, the fake data-lineage graph used by the rest of this project.

The file is a JSON list of 10,000 nodes. Each node looks like a warehouse table
(Stage, Hub, Satellite, Dimension, or Fact) with a list of columns, a fake SQL
join, and the ids of the upstream nodes it depends on.

Standard library only. The random seed is fixed, so every run writes the same file.

Usage (from the repo folder):
    python3 generate.py
"""

import json
import os
import random

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

SEED = 42  # same seed -> same sequence of "random" choices -> same file
NUM_NODES = 10_000
MIN_COLUMNS, MAX_COLUMNS = 10, 60
MIN_SQL_CHARS, MAX_SQL_CHARS = 500, 2_000
MAX_DEPENDENCIES = 5
OUTPUT_FILE = "graph.json"

# ---------------------------------------------------------------------------
# Vocabulary: the building blocks the random choices are made from
# ---------------------------------------------------------------------------

NODE_TYPES = ["Stage", "Hub", "Satellite", "Dimension", "Fact"]

# Name prefix per node type: a Stage node with id 123 is named "STG_NODE_123".
NAME_PREFIXES = {
    "Stage": "STG",
    "Hub": "HUB",
    "Satellite": "SAT",
    "Dimension": "DIM",
    "Fact": "FCT",
}

# Column names are "<subject>_<attribute>", e.g. "customer_status".
SUBJECTS = [
    "customer", "order", "product", "account", "supplier", "employee",
    "store", "invoice", "payment", "shipment", "campaign", "contract",
]

# attribute: (dataType, description template)
ATTRIBUTES = {
    "id":         ("BIGINT",        "Unique surrogate key for each {subject}."),
    "hash_key":   ("CHAR(32)",      "MD5 hash of the {subject} business key."),
    "code":       ("VARCHAR(20)",   "Short business code for the {subject}."),
    "name":       ("VARCHAR(255)",  "Display name of the {subject}."),
    "status":     ("VARCHAR(20)",   "Current lifecycle status of the {subject}."),
    "amount":     ("DECIMAL(18,2)", "Monetary amount associated with the {subject}."),
    "quantity":   ("INTEGER",       "Number of units recorded for the {subject}."),
    "score":      ("FLOAT",         "Model-derived score for the {subject}."),
    "is_active":  ("BOOLEAN",       "True if the {subject} is currently active."),
    "created_at": ("TIMESTAMP",     "When the {subject} record was first created."),
    "updated_at": ("TIMESTAMP",     "When the {subject} record was last changed."),
    "valid_from": ("DATE",          "First day this version of the {subject} is valid."),
    "valid_to":   ("DATE",          "Last day this version of the {subject} is valid."),
}

SOURCE_SYSTEMS = [
    "SAP", "Salesforce", "Workday", "Shopify", "Oracle EBS",
    "the legacy CRM", "the web events stream",
]

# Every subject x attribute combination as (name, dataType, description).
# It needs at least MAX_COLUMNS entries so a node can get 60 distinct columns.
COLUMN_POOL = [
    (f"{subject}_{attribute}", data_type, template.format(subject=subject))
    for subject in SUBJECTS
    for attribute, (data_type, template) in ATTRIBUTES.items()
]

JOIN_TYPES = ["INNER JOIN", "LEFT JOIN"]

# Filters that pad the SQL out to length.
# {a} and {b} are table aliases, {col} is a column name, {n} is a number.
FILTER_TEMPLATES = [
    "AND {a}.{col} = {b}.{col}",
    "AND {a}.{col} IS NOT NULL",
    "AND {a}.{col} <> 'N/A'",
    "AND COALESCE({a}.{col}, 0) > {n}",
    "AND ({a}.{col} > {n} OR {b}.{col} IS NULL)",
    "AND {a}.{col} >= DATEADD(day, -{n}, CURRENT_DATE)",
    "AND UPPER(TRIM({a}.{col})) IN ('ACTIVE', 'PENDING', 'CLOSED')",
]

# ---------------------------------------------------------------------------
# Builders: each one makes one piece of a node
# ---------------------------------------------------------------------------


def make_columns() -> list[dict]:
    """Return 10 to 60 column dicts. No name repeats within a node."""
    count = random.randint(MIN_COLUMNS, MAX_COLUMNS)
    columns = []
    # sample() picks `count` *different* entries from the pool.
    for name, data_type, description in random.sample(COLUMN_POOL, count):
        source = random.choice(SOURCE_SYSTEMS)
        columns.append({
            "name": name,
            "dataType": data_type,
            "description": f"{description} Sourced from {source}.",
        })
    return columns


def pick_dependencies(node_id: int) -> list[int]:
    """Return 1 to 5 distinct ids smaller than node_id. Node 0 gets none."""
    if node_id == 0:
        return []
    # Node 3 only has 3 earlier nodes (0, 1, 2) to pick from, hence min().
    count = random.randint(1, min(MAX_DEPENDENCIES, node_id))
    return sorted(random.sample(range(node_id), count))


def make_join_condition(table_names: list[str], column_names: list[str]) -> str:
    """Return fake SQL, 500 to 2,000 characters long, that joins the given tables."""
    target_length = random.randint(MIN_SQL_CHARS, MAX_SQL_CHARS)

    # Node 0 has no dependencies, so it reads from a made-up raw source instead.
    tables = table_names or ["RAW_SOURCE_FEED"]
    aliases = [f"t{i}" for i in range(len(tables))]  # t0, t1, t2, ...

    # FROM the first table, then JOIN each of the others to it.
    sql = f"FROM {tables[0]} AS t0"
    for table, alias in zip(tables[1:], aliases[1:]):
        join = random.choice(JOIN_TYPES)
        key = random.choice(column_names)
        sql += f" {join} {table} AS {alias} ON t0.{key} = {alias}.{key}"
    sql += " WHERE 1 = 1"  # a no-op filter, so every filter after it can start with AND

    # Add filters until the string reaches its target length.
    while len(sql) < target_length:
        template = random.choice(FILTER_TEMPLATES)
        # format() ignores any values the template doesn't mention.
        sql += " " + template.format(
            a=random.choice(aliases),
            b=random.choice(aliases),
            col=random.choice(column_names),
            n=random.randint(1, 1000),
        )

    # The loop guarantees at least MIN_SQL_CHARS. The last filter can overshoot,
    # so the slice caps the length at MAX_SQL_CHARS (cutting that filter short,
    # which is fine for fake SQL).
    return sql[:MAX_SQL_CHARS]


def make_node(node_id: int, nodes: list[dict]) -> dict:
    """Build one node. `nodes` holds every node built so far (ids 0 to node_id - 1)."""
    node_type = random.choice(NODE_TYPES)
    columns = make_columns()
    dependencies = pick_dependencies(node_id)

    # Ids match list positions, so nodes[dep_id] is the node with that id.
    dependency_names = [nodes[dep_id]["name"] for dep_id in dependencies]
    column_names = [column["name"] for column in columns]

    return {
        "id": node_id,
        "name": f"{NAME_PREFIXES[node_type]}_NODE_{node_id}",
        "nodeType": node_type,
        "columns": columns,
        "joinCondition": make_join_condition(dependency_names, column_names),
        "dependencies": dependencies,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    random.seed(SEED)

    nodes = []
    for node_id in range(NUM_NODES):
        nodes.append(make_node(node_id, nodes))

    # json.dump writes the JSON text to the file in pieces as it goes.
    # json.dumps would build the entire text as one string in memory first.
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(nodes, f)

    size_bytes = os.path.getsize(OUTPUT_FILE)
    size_mb = size_bytes / (1024 * 1024)  # 1 MB = 1,048,576 bytes here
    print(f"Wrote {len(nodes):,} nodes to {OUTPUT_FILE}")
    print(f"File size: {size_mb:.1f} MB ({size_bytes:,} bytes)")


if __name__ == "__main__":
    main()
