# Evaluation

## Purpose

The project contains two complementary evaluation tracks:

```text
1. AI pipeline evaluation
2. Retrieval strategy experiment
```

They answer different questions.

The AI benchmark evaluates the complete schema-guided Text-to-Cypher and grounded-answer pipeline.

The retrieval benchmark compares flat lexical retrieval with graph retrieval before final-answer generation.

---

# AI Evaluation Benchmark

## Goal

The AI benchmark measures the schema-guided Text-to-Cypher pipeline against deterministic ground truth derived from the project's synthetic Knowledge Graph dataset.

The benchmark evaluates three stages independently:

1. pipeline execution success;
2. Neo4j retrieval correctness;
3. grounded answer correctness.

A case is fully correct only when all three checks pass.

## Benchmark Dataset

The benchmark is defined in:

```text
evaluation/benchmark.yaml
```

It contains 12 questions across five categories:

- entity lookup;
- relationship traversal;
- multi-hop reasoning;
- aggregation and filtering;
- no-result handling.

Expected results are deterministic and are based on the synthetic graph.

## Run a Single Evaluation

From the repository root:

```cmd
python src\run_evaluation.py
```

Optionally write the complete result locally:

```cmd
python src\run_evaluation.py --output evaluation\baseline-run.json
```

Generated `*-run.json` files are local evaluation outputs and are not treated as permanent benchmark ground truth.

---

## Repeated Reliability Evaluation

The reliability runner executes the complete benchmark multiple times:

```cmd
python src\run_reliability_evaluation.py --runs 5
```

Optionally save the detailed result:

```cmd
python src\run_reliability_evaluation.py --runs 5 --output evaluation\reliability-run.json
```

The repeated evaluation measures:

- perfect benchmark runs;
- fully correct case executions;
- retry frequency;
- retry reasons;
- failures by type;
- distinct normalized Cypher formulations generated for each case.

## Reliability Behavior

The query pipeline supports one corrective Cypher retry.

Retries can be triggered by:

- Cypher validation errors;
- Neo4j execution errors;
- result-limit errors;
- suspicious empty results.

An empty result is considered suspicious when the user's question explicitly references entity IDs that can be confirmed to exist in the graph.

For example:

```text
REQ-999 does not exist
→ empty result can be valid

REQ-002 exists but retrieval unexpectedly returns no rows
→ retry the Cypher once
```

This keeps no-result questions valid while providing a recovery path for likely retrieval mistakes.

## Observed Reliability Baseline

On September 10, 2026, a five-run reliability experiment produced:

```text
Runs: 5
Case executions: 60
Perfect runs: 5/5 (100.0%)
Fully correct executions: 60/60 (100.0%)
Executions requiring retry: 0/60 (0.0%)
```

There were:

```text
0 execution failures
0 retrieval failures
0 answer failures
```

The model still generated multiple distinct normalized Cypher formulations for every benchmark case.

Across five runs, individual cases produced between two and five different Cypher formulations while remaining fully correct.

This demonstrates an important distinction:

```text
generation variability != observed functional failure
```

The goal is therefore not to force identical Cypher text.

The goal is to keep retrieval and grounded answers correct despite normal LLM generation variability.

---

# Retrieval Experiment

## Goal

The retrieval experiment compares:

```text
Flat lexical retrieval
vs
Schema-guided graph retrieval
```

over the same synthetic engineering data.

The purpose is to identify the kinds of engineering questions for which explicit graph structure provides retrieval value.

The benchmark is defined in:

```text
evaluation/retrieval_benchmark.yaml
```

It contains 10 questions across:

- direct relationships;
- one-to-many relationships;
- multi-hop investigation;
- cross-source investigation;
- cross-environment analysis;
- filtering;
- aggregation.

---

## Flat Retrieval

The flat baseline converts all source rows into independent searchable documents:

```text
52 node rows
+
64 relationship rows
=
116 flat documents
```

The baseline uses deterministic BM25-style lexical search.

It does not use:

```text
Neo4j
graph traversal
LLM generation
embeddings
vector search
```

Run the flat baseline independently:

```cmd
python src\run_flat_retrieval.py
```

---

## Graph Retrieval

The graph strategy reuses the existing:

```text
question
→ graph schema
→ Text-to-Cypher
→ Neo4j
→ records
```

pipeline.

For the retrieval experiment, final-answer generation is intentionally disabled.

This allows graph retrieval to be evaluated separately from answer generation.

---

## Run the Comparison

Run the complete retrieval experiment:

```cmd
python src\run_retrieval_experiment.py
```

Save structured results:

```cmd
python src\run_retrieval_experiment.py --output evaluation\results\retrieval-experiment.json
```

Run one case and inspect generated Cypher:

```cmd
python src\run_retrieval_experiment.py --case RET-005 --show-cypher
```

---

## Retrieval Metrics

The experiment evaluates expected evidence atoms.

The main metrics are:

### Recall

How much required evidence was retrieved.

### Precision

How much comparable retrieved evidence was relevant to the case.

### Evidence Complete

Whether all expected benchmark evidence was available in the retrieved result.

`evidence_complete` does not mean that final reasoning has already been performed.

It means the retrieved evidence is sufficient according to the benchmark definition.

---

## Observed Retrieval Result

The September 14, 2026 experiment produced:

| Strategy | Execution Success | Complete Evidence | Mean Recall | Mean Precision |
| --- | ---: | ---: | ---: | ---: |
| Flat Retrieval | 10/10 | 7/10 | 0.847 | 0.492 |
| Graph Retrieval | 10/10 | 9/10 | 0.980 | 1.000 |

The graph strategy showed its strongest advantages for:

```text
cross-source retrieval
structured filtering
cross-environment correlation
selective relationship traversal
```

Flat retrieval remained competitive for simpler direct relationship questions.

One broad multi-hop question:

```text
What happened during EXEC-010?
```

returned incomplete evidence from both strategies.

For graph retrieval, the generated Cypher retrieved the execution, test, traces, and defect but did not continue to the requirement and affected software component.

This demonstrates:

```text
graph capability != retrieval decision
```

The required context existed in Neo4j, but the generated query did not request all of it.

No benchmark-specific prompt tuning was performed to force this case to pass.

Detailed analysis is available in:

```text
docs/09-retrieval-experiment.md
```

The structured observed run is stored in:

```text
evaluation/results/retrieval-experiment.json
```

This result file is an observed experiment artifact.

It is not benchmark ground truth and future graph retrieval runs may differ because Cypher generation is non-deterministic.

---

# Evaluation Philosophy

Both evaluation tracks follow the same principle:

```text
measure behavior
before optimizing behavior
```

The project does not attempt to force identical Cypher queries or perfect benchmark scores when the observed behavior does not justify additional complexity.

The benchmarks are intended to reveal strengths and limitations of the current architecture.

They should not be modified simply to make the system appear more successful.

---

# Limitations

Both benchmarks are intentionally small and synthetic.

A strong result does not prove production-level reliability or retrieval performance.

Important limitations include:

- synthetic engineering data;
- small benchmark sizes;
- small graph schema;
- `COPILOT_MODEL=auto`;
- possible run-to-run Cypher variation;
- project-specific evaluation metrics;
- no production-scale retrieval workload;
- no vector or semantic retrieval comparison.

The results are best treated as controlled PoC evidence and regression tests for future architectural changes.