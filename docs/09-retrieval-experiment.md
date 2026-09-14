# Retrieval Experiment

## Goal

The purpose of this experiment is to compare two retrieval strategies over the same synthetic automotive engineering data:

```text
Flat lexical retrieval
vs
Schema-guided graph retrieval
```

The experiment asks a practical question:

> When does explicit Knowledge Graph structure provide useful retrieval advantages compared with a simpler flat search baseline?

The goal is not to prove that graph retrieval is always better.

A useful result should also show cases where a simpler retrieval strategy is sufficient.

---

## Compared Retrieval Strategies

### Flat Retrieval

The flat baseline converts the existing synthetic source data into independent searchable documents.

Each node CSV row becomes one node document.

Example:

```text
TestExecution
id: EXEC-010
environment: Vehicle
result: FAIL
reconnectionTimeSeconds: 18.0
sourceSystem: TestManagementSystem
```

Each relationship CSV row becomes one relationship document.

Example:

```text
TestExecution EXEC-010
HAS_DEFECT_TICKET
DefectTicket DEF-001
```

The resulting corpus contains:

```text
52 node documents
64 relationship documents
-------------------------
116 flat documents
```

A deterministic BM25-style lexical retriever searches these documents.

The flat retriever does not perform graph traversal.

For example, it can retrieve:

```text
EXEC-010 -> DEF-001
```

and independently retrieve:

```text
DEF-001 -> COMP-002
```

but it does not explicitly follow the first relationship to discover the second one.

No embeddings, vector database, LLM, or graph database are used by this baseline.

---

### Graph Retrieval

Graph retrieval reuses the project's existing schema-guided Text-to-Cypher pipeline.

The retrieval flow is:

```text
Natural-language question
        ↓
LLM + complete graph schema
        ↓
Generated Cypher
        ↓
Cypher safety validation
        ↓
Neo4j
        ↓
Structured graph facts
```

For this experiment, final-answer generation is disabled.

This is important because the experiment measures retrieval behavior independently from LLM answer generation.

The graph strategy can use explicit relationships such as:

```text
TestExecution
    |
    | EXECUTION_OF
    v
Test
    |
    | VERIFIES
    v
Requirement
```

and:

```text
TestExecution
    |
    | HAS_DEFECT_TICKET
    v
DefectTicket
    |
    | AFFECTS
    v
SoftwareComponent
```

---

## Benchmark

The retrieval benchmark is defined in:

```text
evaluation/retrieval_benchmark.yaml
```

It contains 10 deterministic cases across:

```text
direct relationship
one-to-many relationship
multi-hop investigation
cross-source investigation
cross-environment analysis
filtering
aggregation
```

The same questions are used for both retrieval strategies.

Examples include:

```text
What requirement does TEST-006 verify?
```

```text
What happened during EXEC-010?
```

```text
Which source systems contribute facts to the investigation of EXEC-010?
```

```text
Which test executions verifying REQ-002 exceeded the 10-second reconnection requirement?
```

```text
How many test executions passed and failed in each environment?
```

The benchmark ground truth is derived from the deterministic synthetic dataset.

---

## Evaluation Model

The experiment evaluates retrieved evidence rather than final natural-language answers.

Expected facts are represented as evidence atoms.

Examples:

```text
id:REQ-002
id:EXEC-010
source_system:TraceRepository
environment:Vehicle
result:FAIL
```

The experiment reports three main measures.

### Recall

Recall measures how much required evidence was retrieved.

Conceptually:

```text
required evidence retrieved
---------------------------
total required evidence
```

For example, if 8 of 10 required facts are present:

```text
recall = 0.8
```

### Precision

Precision measures how much of the comparable retrieved evidence is relevant to the benchmark case.

A lower precision usually means that retrieval returned additional candidate entities or facts of the same evaluated type.

This is an evidence-level metric rather than a general document-ranking metric.

### Evidence Complete

A case is marked:

```text
evidence_complete = YES
```

when all required benchmark evidence is available in the retrieved result.

This means that the evidence is sufficient according to the benchmark.

It does not mean that the retrieval strategy has already performed the final reasoning or generated the final user-facing answer.

---

## Observed Experiment

The comparison was run once against the 10-case benchmark using:

```text
Flat strategy:
deterministic BM25-style lexical retrieval

Graph strategy:
schema-guided Text-to-Cypher + Neo4j

Configured LLM model:
auto

Final-answer generation:
disabled
```

Structured details from the observed run are stored in:

```text
evaluation/results/retrieval-experiment.json
```

---

## Overall Results

Observed results:

| Strategy | Execution Success | Complete Evidence | Mean Recall | Mean Precision |
| --- | ---: | ---: | ---: | ---: |
| Flat Retrieval | 10/10 | 7/10 | 0.847 | 0.492 |
| Graph Retrieval | 10/10 | 9/10 | 0.980 | 1.000 |

Both strategies executed successfully for all benchmark cases.

Graph retrieval returned complete expected evidence for 9 of 10 cases.

Flat retrieval returned complete expected evidence for 7 of 10 cases.

The largest observed difference was precision:

```text
Flat mean precision:  0.492
Graph mean precision: 1.000
```

This indicates that the flat baseline often retrieved the required evidence together with additional unrelated candidate evidence, while graph queries were substantially more selective in this run.

---

## Results by Category

| Category | Flat Recall | Flat Precision | Flat Complete | Graph Recall | Graph Precision | Graph Complete |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| aggregation | 1.000 | 1.000 | 1/1 | 1.000 | 1.000 | 1/1 |
| cross-environment | 1.000 | 0.667 | 1/1 | 1.000 | 1.000 | 1/1 |
| cross-source | 0.667 | 1.000 | 0/1 | 1.000 | 1.000 | 1/1 |
| direct relationship | 1.000 | 0.183 | 2/2 | 1.000 | 1.000 | 2/2 |
| filtering | 0.000 | 0.000 | 0/1 | 1.000 | 1.000 | 1/1 |
| multi-hop | 0.900 | 0.567 | 1/2 | 0.900 | 1.000 | 1/2 |
| one-to-many | 1.000 | 0.375 | 2/2 | 1.000 | 1.000 | 2/2 |

---

## Direct Relationship Retrieval

Flat retrieval performed well on simple relationship questions.

For example:

```text
What requirement does TEST-006 verify?
```

Both strategies found:

```text
REQ-006
```

Similarly:

```text
Which traces were produced by EXEC-006?
```

Both strategies recovered:

```text
TRACE-003
TRACE-004
TRACE-005
```

This is an important result.

A Knowledge Graph is not automatically necessary for every retrieval problem.

For simple lookups where the relevant relationship fact is already easy to identify lexically, flat retrieval can recover all required evidence.

However, the flat baseline returned significantly more unrelated evidence in these cases.

For example, the direct relationship category produced:

```text
Flat precision:  0.183
Graph precision: 1.000
```

The graph therefore provided substantially more selective retrieval.

---

## Multi-Hop Investigation

The most interesting multi-hop case was:

```text
What happened during EXEC-010?
```

Expected investigation evidence included:

```text
EXEC-010
TEST-002
REQ-002
TRACE-006
TRACE-007
TRACE-008
DEF-001
COMP-002
FAIL
18.0
```

Observed results:

```text
Flat:
recall = 0.800
precision = 0.800

Graph:
recall = 0.800
precision = 1.000
```

Both strategies missed:

```text
REQ-002
COMP-002
```

The reason for the graph result was inspected separately.

The generated Cypher was conceptually:

```text
EXEC-010
├── EXECUTION_OF → Test
├── PRODUCES → TestTrace
└── HAS_DEFECT_TICKET → DefectTicket
```

It did not continue the available graph paths:

```text
Test
→ VERIFIES
→ Requirement
```

or:

```text
DefectTicket
→ AFFECTS
→ SoftwareComponent
```

This distinction is important.

The missing evidence was not absent from the Knowledge Graph.

Instead:

```text
graph capability
!=
retrieval decision
```

The graph contains the required multi-hop context, but the Text-to-Cypher generation step chose a narrower interpretation of the broad question.

The experiment therefore demonstrates that graph structure alone does not guarantee complete retrieval.

Query generation remains part of retrieval quality.

No prompt tuning was performed to force this benchmark case to pass.

---

## Explicit Multi-Hop Retrieval

A more explicit multi-hop question behaved differently:

```text
Which defect ticket is linked to EXEC-012 and which software component does that defect affect?
```

Graph retrieval followed:

```text
EXEC-012
→ DEF-002
→ COMP-005
```

and achieved:

```text
recall = 1.000
precision = 1.000
```

This suggests that graph retrieval is particularly effective when the question makes the required traversal explicit.

---

## Cross-Source Investigation

The cross-source case asked:

```text
Which source systems contribute facts to the investigation of EXEC-010?
```

Expected evidence included all six synthetic source-system categories:

```text
ProductDefinitionSystem
RequirementsSystem
SoftwareArchitectureSystem
TestManagementSystem
TraceRepository
DefectTrackingSystem
```

Observed results:

```text
Flat:
recall = 0.667
precision = 1.000
evidence complete = NO

Graph:
recall = 1.000
precision = 1.000
evidence complete = YES
```

Flat retrieval missed:

```text
TraceRepository
DefectTrackingSystem
```

Graph retrieval successfully connected evidence across the synthetic engineering source boundaries.

This directly demonstrates the intended source-system scenario:

```text
different engineering source systems
            ↓
       common ontology
            ↓
      Knowledge Graph
            ↓
cross-source investigation
```

The graph case required two Cypher-generation attempts because the first query produced a Neo4j error.

The existing corrective retry mechanism recovered successfully.

---

## Cross-Environment Analysis

The benchmark asked:

```text
Which defect ticket is linked to failed executions in more than one test environment, and which environments are involved?
```

Both strategies retrieved enough evidence to answer the question.

Observed precision differed:

```text
Flat precision:  0.667
Graph precision: 1.000
```

Flat retrieval included additional defect candidates:

```text
DEF-002
DEF-003
```

Graph retrieval returned only the relevant cross-environment result:

```text
DEF-001

SiL
HiL
Vehicle
```

This demonstrates the value of combining filtering and relationships inside the graph query rather than retrieving a larger candidate set and resolving the correlation later.

---

## Filtering

The clearest difference appeared in:

```text
Which test executions verifying REQ-002 exceeded the 10-second reconnection requirement?
```

Expected executions:

```text
EXEC-003
EXEC-006
EXEC-008
EXEC-010
EXEC-016
```

Observed result:

```text
Flat recall:  0.000
Graph recall: 1.000
```

Flat retrieval found highly related facts such as:

```text
REQ-002
tests verifying REQ-002
traces mentioning the 10-second limit
```

but it did not recover the required execution set.

The graph strategy combined:

```text
Requirement
← VERIFIES
Test
← EXECUTION_OF
TestExecution
```

with a structured numeric filter:

```text
reconnectionTimeSeconds > 10
```

This is one of the strongest examples in the experiment of graph retrieval providing value through explicit structure plus filtering.

---

## Aggregation

The aggregation case asked:

```text
How many test executions passed and failed in each environment?
```

Both strategies achieved complete evidence.

This does not mean that flat lexical retrieval itself calculated the aggregation.

Flat retrieval returned all required `TestExecution` records within the configured Top-K window.

The evaluator could therefore derive the expected counts from the retrieved evidence.

Graph retrieval instead performed the aggregation directly through Cypher.

This is an important distinction:

```text
evidence sufficient for aggregation
!=
retriever performed aggregation
```

The experiment intentionally measures retrieval evidence first.

---

## Main Findings

### Flat retrieval is a meaningful baseline

Flat retrieval successfully recovered complete evidence for 7 of 10 benchmark cases.

It performed particularly well for:

```text
direct relationship lookup
one-to-many lookup
aggregation evidence collection
```

The experiment therefore does not show that every engineering question requires a Knowledge Graph.

### Graph retrieval was substantially more selective

Observed mean precision was:

```text
Flat:  0.492
Graph: 1.000
```

Flat retrieval frequently recovered correct facts together with unrelated candidates.

Graph retrieval used explicit relationships and filters to return smaller, more targeted result sets.

### Graph retrieval showed its clearest advantage for structured questions

The strongest graph advantages appeared for:

```text
cross-source investigation
structured filtering
cross-environment correlation
explicit multi-hop traversal
```

These questions depend on relationships between engineering entities rather than only textual similarity.

### A Knowledge Graph does not remove retrieval uncertainty

`RET-005` demonstrates that having the correct information in the graph is not enough.

The system still needs to generate a Cypher query that asks for the relevant part of the graph.

For broad questions:

```text
available graph context
```

may be larger than:

```text
context selected by generated Cypher
```

This is a useful limitation to preserve rather than hide through benchmark-specific prompt tuning.

---

## Engineering Decision

No additional optimization is introduced as a result of this experiment.

In particular, the project does not add:

```text
vector search
embeddings
hybrid retrieval
rerankers
LangChain
schema retrieval
prompt tuning specifically for RET-005
```

The current experiment already provides the intended learning result.

The next project stage can therefore build on the existing retrieval capabilities rather than continuing to optimize retrieval scores.

---

## Limitations

The experiment is intentionally PoC-level.

Important limitations include:

- all engineering data is synthetic;
- the benchmark contains only 10 retrieval cases;
- the graph contains only seven node labels and seven relationship types;
- the flat corpus contains only 116 records;
- flat retrieval uses a simple deterministic lexical baseline;
- graph retrieval depends on an LLM configured with `COPILOT_MODEL=auto`;
- the reported graph results come from one observed benchmark run;
- graph retrieval can vary between runs because Cypher generation is non-deterministic;
- evidence precision is benchmark-specific and considers comparable evidence atoms rather than every token or field returned;
- `evidence_complete` measures availability of expected evidence, not final reasoning correctness;
- the experiment does not compare vector or semantic retrieval systems;
- the results do not establish production-level retrieval performance.

The experiment should therefore be interpreted as a controlled learning exercise, not as a general claim that graph retrieval outperforms other retrieval technologies.

---

## Conclusion

The experiment suggests that both retrieval approaches have useful roles.

A simple flat retriever can be sufficient when the required engineering fact is directly searchable.

The Knowledge Graph becomes more valuable when questions depend on:

```text
explicit relationships
multi-hop traversal
cross-source context
structured filtering
cross-environment correlation
```

The main observed distinction is therefore not:

```text
graph retrieval is always better
```

but:

```text
graph structure becomes increasingly useful
as the question depends more strongly on
relationships between engineering artifacts
```

This is the main conclusion of the Retrieval Experiment stage.