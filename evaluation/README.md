# AI Evaluation Benchmark

## Purpose

This benchmark measures the current schema-guided Text-to-Cypher
pipeline against deterministic ground truth derived from the project's
synthetic Knowledge Graph dataset.

The benchmark evaluates three stages independently:

1. pipeline execution success;
2. Neo4j retrieval correctness;
3. grounded answer correctness.

A case is fully correct only when all three checks pass.

## Benchmark dataset

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

## Run a single evaluation

From the repository root:

```cmd
python src\run_evaluation.py
```

Optionally write the complete result locally:

```cmd
python src\run_evaluation.py --output evaluation\baseline-run.json
```

Generated `*-run.json` files are local experiment outputs and are not
treated as permanent benchmark ground truth.

## Run repeated reliability evaluation

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

## Reliability behavior

The query pipeline supports one corrective Cypher retry.

Retries can be triggered by:

- Cypher validation errors;
- Neo4j execution errors;
- result-limit errors;
- suspicious empty results.

An empty result is considered suspicious when the user's question
explicitly references entity IDs that can be confirmed to exist in the
graph.

For example:

```text
REQ-999 does not exist
-> empty result can be valid

REQ-002 exists but retrieval unexpectedly returns no rows
-> retry the Cypher once
```

This keeps no-result questions valid while providing a recovery path
for likely retrieval mistakes.

## Observed baseline

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

The model still generated multiple distinct normalized Cypher
formulations for every benchmark case.

Across five runs, individual cases produced between two and five
different Cypher formulations while remaining fully correct.

This demonstrates an important distinction:

```text
generation variability != observed functional failure
```

The goal is therefore not to force identical Cypher text. The goal is
to keep retrieval and grounded answers correct despite normal LLM
generation variability.

## Limitations

The benchmark is intentionally small and synthetic.

A 100% result across 60 case executions demonstrates strong observed
behavior for this PoC, but it does not prove production-level
reliability.

`COPILOT_MODEL=auto` may also select different underlying models over
time.

The Cypher variation metric compares normalized query text. It is useful
for detecting run-to-run variation, but it is not a formal semantic
equivalence test for Cypher queries.