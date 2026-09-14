# Evaluation

## Purpose

The project contains three complementary evaluation tracks:

```text
1. AI pipeline evaluation
2. Retrieval strategy experiment
3. Minimal tool-calling agent evaluation
```

They answer different questions.

The AI benchmark evaluates the complete schema-guided Text-to-Cypher and grounded-answer pipeline.

The retrieval benchmark compares flat lexical retrieval with graph retrieval before final-answer generation.

The agent benchmark evaluates whether the minimal agent:

- selects graph retrieval when project data is required;
- avoids graph retrieval when it is unnecessary;
- respects the one-tool-call limit;
- successfully executes the graph tool;
- includes expected evidence in the final answer;
- handles empty retrieval results carefully.

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

# Minimal Tool-Calling Agent Evaluation

## Goal

The agent evaluation measures the decision layer added above the existing graph retrieval pipeline.

It asks:

```text
Should the agent use graph retrieval for this question?
```

and, when retrieval is required:

```text
Did it use the tool minimally and produce an answer containing the expected evidence?
```

The benchmark is defined in:

```text
evaluation/agent_benchmark.yaml
```

It contains eight cases.

Five require graph retrieval:

```text
AGT-001  direct relationship
AGT-002  multi-hop
AGT-003  filtering
AGT-004  cross-environment
AGT-005  no-result handling
```

Three should not use graph retrieval:

```text
AGT-006  conceptual
AGT-007  capability
AGT-008  conversational
```

---

## Agent Architecture

The agent has one custom tool:

```text
graph_retrieval
```

The tool delegates to the existing:

```text
QueryService.retrieve_question()
```

pipeline.

The agent therefore does not implement a second retrieval architecture.

The flow is:

```text
User question
      ↓
Minimal Agent
      ↓
graph evidence required?
   /             \
 yes              no
  ↓                ↓
graph_retrieval   direct answer
  ↓
Text-to-Cypher
  ↓
Neo4j
  ↓
graph facts
  ↓
final answer
```

The graph tool is limited to one invocation per user question.

A single graph tool invocation can still contain the existing corrective Cypher retry behavior inside `QueryService`.

---

## Agent Metrics

The benchmark reports:

### Tool Selection Correct

Whether `graph_retrieval` was used exactly when the benchmark expects graph evidence.

### Tool Call Count Correct

Whether the agent respected the configured maximum number of graph tool calls.

For the current PoC:

```text
graph question → maximum 1 call
non-graph question → 0 calls
```

### Tool Execution Success

Whether the graph tool invocation completed successfully.

### Answer Values Complete

Whether all required benchmark values are present in the final natural-language answer.

This is a deterministic proxy for answer correctness.

It does not semantically validate every sentence generated by the agent.

### No-Result Handling Correct

For no-result questions, whether retrieval returned zero records and the answer communicates that no matching graph facts were retrieved.

### Fully Correct

A case is fully correct only when all applicable checks pass.

---

## Run the Agent Benchmark

Run all eight cases:

```cmd
python src\run_agent_evaluation.py
```

Save the structured observed result:

```cmd
python src\run_agent_evaluation.py --output evaluation\results\agent-evaluation.json
```

Run one specific case:

```cmd
python src\run_agent_evaluation.py --case AGT-005
```

---

## Observed Agent Result

The final September 14, 2026 run produced:

```text
Execution:                  8/8
Fully correct:              8/8
Tool selection correct:     8/8
Tool call count correct:    8/8
Tool execution success:     8/8
Answer values complete:     8/8
No-result handling correct: 8/8
```

All five engineering-data questions used:

```text
graph_retrieval
```

exactly once.

All three questions that did not require project graph data used:

```text
0 graph tool calls
```

The structured observed result is stored in:

```text
evaluation/results/agent-evaluation.json
```

This is an observed experiment artifact rather than deterministic ground truth.

Tool selection, Cypher generation, and natural-language generation can vary between runs because they depend on an LLM.

Detailed analysis is available in:

```text
docs/10-minimal-tool-calling-agent.md
```

---

## Agent Calibration

An earlier run produced:

```text
Fully correct: 7/8
```

The no-result case exposed two issues:

- the deterministic evaluator did not recognize `No results found` as valid no-result wording;
- the agent could interpret an empty retrieval result too strongly by claiming that an entity did not exist.

The benchmark definition was not changed.

Instead:

- the deterministic no-result evaluator was corrected;
- the agent grounding instructions were strengthened.

The no-result case was then validated independently before the final full benchmark run.

The final eight-case run produced:

```text
Fully correct: 8/8
```

This preserves the benchmark as a way to identify behavior problems rather than changing the expected result simply to obtain a perfect score.

---

# Evaluation Philosophy

All three evaluation tracks follow the same principle:

```text
measure behavior
before optimizing behavior
```

The project does not attempt to force identical Cypher queries or perfect benchmark scores when the observed behavior does not justify additional complexity.

The benchmarks are intended to reveal strengths and limitations of the retrieval, answer-generation, and agent layers of the current architecture.

They should not be modified simply to make the system appear more successful.

---

# Limitations

All three evaluation tracks are intentionally small and synthetic.

A strong result does not prove production-level reliability, retrieval performance, or autonomous-agent capability.

Important limitations include:

- synthetic engineering data;
- small benchmark sizes;
- small graph schema;
- `COPILOT_MODEL=auto`;
- possible run-to-run Cypher and answer variation;
- project-specific evaluation metrics;
- no production-scale retrieval workload;
- no vector or semantic retrieval comparison;
- an eight-case agent benchmark;
- only one custom agent tool;
- at most one graph tool invocation per user question;
- deterministic answer checks based on expected values rather than full semantic judging;
- no multi-agent workflows;
- no autonomous write actions;
- no MCP tools in the current agent stage.

The results are best treated as controlled PoC evidence and regression tests for future architectural changes.