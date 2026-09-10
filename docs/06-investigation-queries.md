# Neo4j Investigation Queries

## Purpose

This document describes the main Cypher queries used for traceability and failure investigation in the Bluetooth Reconnection Knowledge Graph PoC.

The queries demonstrate how connected engineering data can be explored across features, requirements, software components, tests, test executions, traces, defect tickets, and synthetic source-system metadata.

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

- test;
- requirement;
- feature;
- implementing software component;
- test traces;
- defect ticket;
- affected component.

Main expected structure:

```text
EXEC-010
    |
    | EXECUTION_OF
    v
TEST-002
    |
    | VERIFIES
    v
REQ-002
    ^
    |
    | IMPLEMENTS
    |
COMP-002

EXEC-010
    |
    | HAS_DEFECT_TICKET
    v
DEF-001
    |
    | AFFECTS
    v
COMP-002

EXEC-010
    |
    | PRODUCES
    +--> TRACE-006
    +--> TRACE-007
    +--> TRACE-008
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

This query demonstrates that the same engineering problem is not limited to one test environment.

This query is best viewed as a table.

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
   | HAS_REQUIREMENT
   v
Requirement
   ^
   | VERIFIES
   |
Test
   ^
   | EXECUTION_OF
   |
TestExecution
   |
   | HAS_DEFECT_TICKET
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
| --- | ---: | ---: | ---: |
| HiL | 2 | 2 | 4 |
| SiL | 4 | 1 | 5 |
| Vehicle | 3 | 4 | 7 |

This query demonstrates that Cypher can produce aggregated reporting results, not only graph traversals.

This query is best viewed as a table.

---

### 7. Cross-Source Execution Investigation

File:

```text
cypher/queries/07-cross-source-investigation.cypher
```

**Engineering question:** What happened during `EXEC-010`, and which synthetic source systems contributed the connected engineering facts?

The query starts from the failed execution and traverses the existing ontology to retrieve:

- the executed test;
- the verified requirement;
- the related feature;
- the software component implementing the requirement;
- the produced traces;
- the linked defect ticket;
- the software component affected by the defect.

Expected source-system context:

```text
EXEC-010
    TestManagementSystem

TEST-002
    TestManagementSystem

REQ-002
    RequirementsSystem

FEAT-001
    ProductDefinitionSystem

COMP-002
    SoftwareArchitectureSystem

TRACE-006
TRACE-007
TRACE-008
    TraceRepository

DEF-001
    DefectTrackingSystem
```

The important point is not that these systems exist in a real company.

The source-system names are intentionally synthetic. They demonstrate that engineering records originating from different source-system categories can be normalized into a common ontology and investigated together through graph relationships.

Conceptually:

```text
different engineering source systems
            |
            v
      common ontology
            |
            v
    Knowledge Graph
            |
            v
cross-source investigation
```

This query is best viewed as a table because the `sourceSystem` metadata is an important part of the result.

---

## Supporting Investigation Queries

Additional investigation queries currently remain in:

```text
cypher/04-investigation-queries.cypher
```

They include supporting views such as:

- all failed executions;
- software components connected to failed executions;
- defect tickets and traces associated with failures.

These queries are useful during development and investigation but are not currently part of the main demo query set.

The file can be reviewed or removed later after the final query set has been fully validated.

---

## Graph Results vs Table Results

Graph visualization is most useful when the important information is the relationship between engineering entities.

Examples:

- execution investigation;
- feature-to-defect traceability.

Table output is more useful when the question asks for:

- lists;
- values;
- counts;
- grouped results;
- threshold violations;
- source-system metadata.

The underlying information is retrieved from the Knowledge Graph in both cases.

---

## Main Demo Scenarios

The investigation queries support two complementary scenarios.

### Scenario 1 — Deep Engineering Investigation

**Question:**

```text
What happened to this specific execution?
```

Start from a concrete execution such as:

```text
EXEC-010
```

Then retrieve its connected engineering context:

```text
execution
→ test
→ requirement
→ feature

execution
→ traces

execution
→ defect
→ affected software component

software component
→ implemented requirement
```

With `sourceSystem` metadata, the same investigation also demonstrates that the retrieved facts originated from multiple synthetic engineering systems.

The purpose is to answer:

```text
What happened?
Why is this execution relevant?
What evidence is connected to it?
Which requirement was being verified?
Which defect and component are involved?
Where did the connected records originate?
```

This is the primary scenario for demonstrating cross-source Knowledge Graph investigation.

---

### Scenario 2 — Cross-Environment Analysis

**Question:**

```text
What patterns can we observe across multiple executions?
```

Instead of investigating only one execution, this scenario analyzes several executions together.

Relevant questions include:

```text
Which executions exceeded the reconnection threshold?

Does the same defect occur in SiL, HiL, and Vehicle?

How do PASS and FAIL counts differ between environments?
```

This moves from individual investigation to pattern discovery:

```text
one execution
      |
      v
many executions
      |
      v
compare and aggregate
      |
      v
identify patterns
```

The threshold, cross-environment failure, and pass/fail summary queries support this scenario.

---

## Why the Two Scenarios Matter

Together, the scenarios demonstrate two different strengths of the Knowledge Graph.

```text
Scenario 1
Specific execution
→ deep investigation
→ connected engineering context
→ cross-source traceability

Scenario 2
Multiple executions
→ aggregation and comparison
→ cross-environment analysis
→ pattern discovery
```

A natural engineering investigation can therefore evolve like this:

```text
"There is a failure in EXEC-010."
              |
              v
"What happened?"
              |
              v
"Which engineering artifacts are connected?"
              |
              v
"Is this an isolated failure?"
              |
              v
"Does the same pattern occur elsewhere?"
```

---

## Synthetic Source-System Interpretation

The `sourceSystem` property represents lightweight provenance metadata.

In this PoC, provenance means:

```text
Where did this engineering record originate?
```

The configured synthetic mapping is:

| Graph entity | Synthetic source system |
| --- | --- |
| Feature | ProductDefinitionSystem |
| Requirement | RequirementsSystem |
| SoftwareComponent | SoftwareArchitectureSystem |
| Test | TestManagementSystem |
| TestExecution | TestManagementSystem |
| TestTrace | TraceRepository |
| DefectTicket | DefectTrackingSystem |

These names are intentionally generic.

They do not represent real Porsche systems, ownership boundaries, or enterprise architecture.

The goal is only to simulate the common real-world situation in which engineering information originates from different systems but must be investigated together.

---

## Validation Workflow

Before considering the stage complete, each query should be run individually against the rebuilt local Neo4j database.

For each query:

1. Execute the query against Neo4j.
2. Check whether the returned data matches the expected synthetic scenario.
3. Inspect unexpected results against the CSV source data.
4. Modify the query only if a real inconsistency is found.
5. Confirm that the result is understandable enough for the PoC demo.

The ontology and synthetic dataset should not be changed simply to make a query look better.

---

## Demo Query Set

The current recommended demo queries are:

1. `EXEC-010` execution investigation;
2. missing test coverage;
3. reconnection threshold violations;
4. cross-environment failure detection;
5. feature-to-defect traceability;
6. pass/fail counts by environment;
7. cross-source investigation for `EXEC-010`.

Together, these queries demonstrate:

- failure investigation;
- requirements traceability;
- test coverage analysis;
- cross-environment correlation;
- aggregation;
- synthetic source-system provenance;
- cross-source engineering investigation.

---

## Current Status

The query structure and expected results are defined.

The remaining validation step for the synthetic source-system stage is to:

1. rebuild the Neo4j graph;
2. confirm post-import validation succeeds;
3. confirm rebuild repeatability;
4. execute `07-cross-source-investigation.cypher`;
5. verify that the returned entities contain the expected `sourceSystem` metadata.