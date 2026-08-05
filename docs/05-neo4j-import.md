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

## Resetting the graph

Resetting removes all nodes and relationships from the current Neo4j database.

The constraints remain in place.

To reset the graph, run:

```cypher
MATCH (n)
DETACH DELETE n;
```

This command should only be used when a complete re-import is required.

After resetting, run the scripts again in this order:

```text
01-create-constraints.cypher
02-import-nodes.cypher
03-import-relationships.cypher
```

Because the scripts use `IF NOT EXISTS` and `MERGE`, they can be executed repeatedly without creating duplicates.

## Validation

After importing, confirm the following:

* the graph contains 52 nodes;
* node counts match the expected counts;
* relationship counts match the CSV row counts;
* every `TestExecution` has an `EXECUTION_OF` relationship;
* every `TestTrace` is connected through `PRODUCES`;
* defect tickets are connected to executions and affected components;
* the intentionally uncovered requirement remains identifiable.
