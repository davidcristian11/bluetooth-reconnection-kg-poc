# Neo4j Investigation Queries

## Purpose

This document describes the main Cypher queries used for traceability and failure investigation in the Bluetooth Reconnection Knowledge Graph PoC.

The queries demonstrate how connected engineering data can be explored across features, requirements, software components, tests, test executions, traces, and defect tickets.

The demo-oriented queries are stored under:

```text
cypher/queries/
```

The existing development file:

```text
cypher/04-investigation-queries.cypher
```

is kept temporarily while the final queries are reviewed. It contains earlier and supporting investigation queries.

---

## Query Set

### 1. Execution Investigation

File:

```text
cypher/queries/01-execution-investigation.cypher
```

**Engineering question:** What engineering context can be discovered starting from the failed Vehicle execution `EXEC-010`?

The query connects the execution to its:

* test;
* requirement;
* feature;
* implementing software component;
* test traces;
* defect ticket;
* affected component.

Main expected path:

```text
EXEC-010
→ TEST-002
→ REQ-002

REQ-002 ← COMP-002

EXEC-010 → DEF-001 → COMP-002

EXEC-010 → TRACE-006
         → TRACE-007
         → TRACE-008
```

This query is best viewed as a graph.

---

### 2. Missing Test Coverage

File:

```text
cypher/queries/02-missing-test-coverage.cypher
```

**Engineering question:** Which requirements are not verified by any test?

Expected result:

```text
REQ-007
```

`REQ-007` intentionally has no test coverage in the synthetic dataset.

This query is best viewed as a table.

---

### 3. Reconnection Threshold Violations

File:

```text
cypher/queries/03-reconnection-threshold.cypher
```

**Engineering question:** Which executions verifying `REQ-002` exceeded the accepted Bluetooth reconnection limit of 10 seconds?

Expected executions:

```text
EXEC-010   Vehicle   18.0
EXEC-006   HiL       15.4
EXEC-008   HiL       13.8
EXEC-003   SiL       12.1
EXEC-016   Vehicle   11.6
```

This demonstrates that similar problematic behavior appears in multiple test environments.

This query is best viewed as a table.

---

### 4. Cross-Environment Failure

File:

```text
cypher/queries/04-cross-environment-failure.cypher
```

**Engineering question:** Did the same defect appear in multiple test environments?

The main expected result is:

```text
DEF-001
```

It is connected to failed executions in:

```text
SiL
HiL
Vehicle
```

Known related executions are:

```text
EXEC-003
EXEC-006
EXEC-008
EXEC-010
EXEC-016
```

This is one of the main investigation scenarios of the PoC.

---

### 5. Feature-to-Defect Traceability

File:

```text
cypher/queries/05-feature-to-defect-traceability.cypher
```

**Engineering question:** Can a discovered defect be traced through the engineering artifacts that led to it?

The main graph pattern is:

```text
Feature
   |
HAS_REQUIREMENT
   v
Requirement
   ^
VERIFIES
   |
Test
   ^
EXECUTION_OF
   |
TestExecution
   |
HAS_DEFECT_TICKET
   v
DefectTicket
```

This demonstrates end-to-end traceability between product-level information, requirements, verification results, and defects.

This query is best viewed as a graph.

---

### 6. Pass / Fail Summary by Environment

File:

```text
cypher/queries/06-pass-fail-by-environment.cypher
```

**Engineering question:** How many test executions passed and failed in each test environment?

Expected result:

| Environment | Pass | Fail | Total |
| ----------- | ---: | ---: | ----: |
| HiL         |    2 |    2 |     4 |
| SiL         |    4 |    1 |     5 |
| Vehicle     |    3 |    4 |     7 |

This query demonstrates that Cypher can also produce aggregated reporting results, not only graph traversals.

This query is best viewed as a table.

---

## Supporting Investigation Queries

Additional investigation queries currently remain in:

```text
cypher/04-investigation-queries.cypher
```

They include supporting views such as:

* all failed executions;
* software components connected to failed executions;
* defect tickets and traces associated with failures.

These are useful during investigation but are not currently part of the main demo query set.

The file can be reviewed or removed later after the final query set has been fully validated.

---

## Graph Results vs Table Results

Graph visualization is most useful when the important information is the relationship between engineering entities.

Examples:

* execution investigation;
* feature-to-defect traceability.

Table output is more useful when the question asks for:

* lists;
* values;
* counts;
* grouped results;
* threshold violations.

The underlying information is still retrieved from the knowledge graph in both cases.

---

## Validation Workflow

Before considering this stage complete, each query should be run individually from VS Code.

For each query:

1. Execute the query against the local Neo4j database.
2. Check whether the returned data matches the expected synthetic scenario.
3. Inspect unexpected results against the CSV source data.
4. Modify the query only when necessary.
5. Confirm that the output is readable enough for the PoC demo.

The ontology and synthetic dataset should not be changed unless validation reveals a real inconsistency.

---

## Demo Query Set

The current recommended demo queries are:

1. `EXEC-010` execution investigation;
2. missing test coverage;
3. reconnection threshold violations;
4. cross-environment failure detection;
5. feature-to-defect traceability;
6. pass/fail counts by environment.

Together, these queries demonstrate failure investigation, traceability, coverage analysis, cross-environment correlation, and basic reporting using the knowledge graph.

---

## Current Status

The query structure and expected results have been prepared.

The remaining step is to run and review each query in VS Code before the investigation-query stage is considered complete and committed to Git.
