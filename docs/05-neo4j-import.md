# Neo4j Dataset Import

## Purpose

This document explains how the synthetic Bluetooth reconnection dataset is imported into the local Neo4j database.

The import is designed to be repeatable. Running the import scripts again does not create duplicate nodes or relationships.

## Prerequisites

Before importing:

* Neo4j must be running through Docker Compose.
* The repository `data/` directory must be mounted as Neo4j’s `/import` directory.
* The node CSV files must exist under `data/nodes/`.
* The relationship CSV files must exist under `data/relationships/`.

## Import scripts

Run the scripts in this order:

1. `cypher/01-create-constraints.cypher`
2. `cypher/02-import-nodes.cypher`
3. `cypher/03-import-relationships.cypher`

The constraints must be created before importing nodes.

The nodes must be imported before the relationships because the relationship script uses `MATCH` to find existing nodes.

## Constraints

A uniqueness constraint is created for the `id` property of every node label:

* `Feature`
* `Requirement`
* `SoftwareComponent`
* `Test`
* `TestExecution`
* `TestTrace`
* `DefectTicket`

The constraints prevent duplicate IDs and support efficient node lookup.

## Node import

The node import uses:

```cypher
LOAD CSV WITH HEADERS
```

to read the CSV files.

Nodes are imported using `MERGE` with their unique IDs. Their remaining properties are added or updated using `SET`.

The expected node counts are:

| Label             | Expected count |
| ----------------- | -------------: |
| Feature           |              1 |
| Requirement       |              7 |
| SoftwareComponent |              5 |
| Test              |             10 |
| TestExecution     |             16 |
| TestTrace         |             10 |
| DefectTicket      |              3 |
| **Total**         |         **52** |

## Relationship import

The relationship import uses `MATCH` to locate the existing start and end nodes.

It uses `MERGE` to create each relationship only when it does not already exist.

The imported relationship types are:

* `HAS_REQUIREMENT`
* `IMPLEMENTS`
* `VERIFIES`
* `EXECUTION_OF`
* `PRODUCES`
* `HAS_DEFECT_TICKET`
* `AFFECTS`

The imported relationship counts were validated against the number of rows in the relationship CSV files.

## Investigation query

The file below contains a query for investigating test execution `EXEC-010`:

```text
cypher/04-investigation-queries.cypher
```

The query displays the execution’s:

* test;
* requirement;
* traces;
* defect ticket;
* affected software component.

## Controlled graph rebuild

The recommended way to recreate the graph is the controlled Python
rebuild workflow rather than manually deleting and re-importing data.

Run:

```powershell
python src\rebuild_neo4j.py --confirm-reset "RESET bluetooth-reconnection-kg-poc/neo4j"
```

The rebuild runs in this order:

```text
validate source data
→ connect to Neo4j
→ verify reset safety
→ clean graph
→ apply constraints
→ import nodes
→ import relationships
→ run post-import validation
```

The reset is allowed only when Neo4j is configured on a local host and
the exact project/database confirmation string is supplied.

Any failure stops the workflow immediately.

To prove that the rebuild is reproducible, run:

```powershell
python src\rebuild_neo4j.py --confirm-reset "RESET bluetooth-reconnection-kg-poc/neo4j" --verify-repeatability
```

The command performs two full rebuild cycles and compares deterministic
fingerprints of all nodes, relationships, labels, IDs, and properties.

## Validation

Post-import validation automatically confirms:

- total node counts match the node CSV files;
- node counts match per label;
- total relationship counts match the relationship CSV files;
- relationship counts match per type;
- node IDs are present and not duplicated;
- mandatory relationship coverage is satisfied;
- the `EXEC-010` investigation scenario matches the expected graph path.

The current synthetic dataset produces:

- 52 nodes;
- 64 relationships.

A successful rebuild also prints a deterministic graph fingerprint.
When `--verify-repeatability` is used, fingerprints from both rebuild
cycles must be identical.
