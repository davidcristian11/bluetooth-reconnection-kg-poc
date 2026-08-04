# 02 — Ontology and Knowledge Graph Basics

## Ontology

An ontology defines the structure and meaning of a knowledge domain.

For this PoC, it describes which types of engineering information exist and how they are allowed to connect.

It defines:

* **Types** — general categories of things, such as `Requirement`, `Test`, or `SoftwareComponent`;
* **Relationship types** — allowed connections between types, such as `Test VERIFIES Requirement`;
* **Meaning** — what each type and relationship represents;
* **Rules** — how the information should be organized.

The ontology acts like a blueprint for the graph.

It does not contain a specific requirement, test, or defect ticket. Instead, it defines which kinds of items may exist.

## Knowledge graph

A knowledge graph contains the actual connected information.

It contains:

* **Instances** — specific items that belong to a type;
* **Nodes** — the individual items stored in the graph;
* **Relationships** — connections between nodes;
* **Properties** — details stored on nodes or relationships;
* **Labels** — identify the type of a node;
* **Unique IDs** — distinguish one instance from another.

For example:

* `REQ-BT-001` may be an instance of `Requirement`;
* `TEST-BT-004` may be an instance of `Test`;
* the relationship between them may be `VERIFIES`.

## Main difference

* **Ontology = structure, meaning, and rules**
* **Knowledge graph = actual items and their connections**

The ontology defines what the graph is allowed to contain.

The knowledge graph contains the concrete data that follows that structure.

## Neo4j terminology

In Neo4j:

* a **node** represents an item;
* a **label** identifies the node type;
* a **relationship** connects two nodes;
* a **property** stores a detail about a node or relationship.

Example:

```text
(:Test {testId: "TEST-BT-004"})
```

This represents:

* a node;
* with the label `Test`;
* with a property named `testId`;
* whose value is `TEST-BT-004`.

## Ontology and graph model in this PoC

For this small PoC, the ontology and the Neo4j graph model will be almost the same.

The ontology diagram will define:

* the main node types;
* the allowed relationship types;
* the direction of each relationship.

Later, the Neo4j knowledge graph will contain synthetic instances that follow this model.
