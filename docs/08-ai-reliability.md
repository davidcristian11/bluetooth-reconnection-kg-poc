# AI Reliability Improvements

## Goal

The purpose of this stage is to improve and measure the reliability of
the schema-guided Text-to-Cypher pipeline.

The previous evaluation benchmark established deterministic expected
results for 12 synthetic engineering questions.

This stage uses that benchmark to answer a different question:

> Does the AI pipeline remain correct across repeated executions even
> when the generated Cypher changes?

## Reliability improvements

### Corrective retry

The pipeline permits one corrective Cypher generation attempt.

The second attempt receives feedback about the first attempt so that the
LLM can correct the query rather than generating again without context.

Retry reasons are classified so that reliability experiments can
distinguish different recovery scenarios.

Examples include:

```text
cypher_validation_error
neo4j_error
result_limit_error
suspicious_empty_result
```

### Suspicious empty-result detection

An empty Neo4j result is not automatically considered an error.

This is important because questions about entities that do not exist can
legitimately produce no rows.

The pipeline extracts explicit entity IDs from the user's question and
checks whether those IDs exist in the graph.

If the referenced IDs exist but the generated query returns no records,
the result is considered suspicious and the pipeline retries the Cypher
once.

This provides a simple deterministic signal without requiring another
LLM to judge the query.

For example:

```text
REQ-999 does not exist
→ empty result can be valid

REQ-002 exists but retrieval unexpectedly returns no rows
→ retry the Cypher once
```

### Result-limit recovery

Queries that exceed the configured Neo4j result limit can also trigger a
corrective retry.

The LLM receives feedback asking it to generate a more selective query
instead of returning unnecessary graph records.

## Repeated reliability evaluation

The reliability runner executes the complete AI benchmark multiple
times.

For five runs:

```text
12 benchmark cases x 5 runs = 60 case executions
```

The runner records:

- execution correctness;
- retrieval correctness;
- answer correctness;
- perfect-run rate;
- retry rate;
- retry reasons;
- outcome classification;
- Cypher variation per benchmark case.

This makes reliability measurable rather than relying on one successful
demo run.

## Observed results

The September 10, 2026 reliability run produced:

```text
Perfect runs: 5/5 (100.0%)
Fully correct executions: 60/60 (100.0%)
Executions requiring retry: 0/60 (0.0%)

Execution failures: 0
Retrieval failures: 0
Answer failures: 0
```

All five runs were therefore fully correct on the current benchmark.

## Cypher variability

The generated Cypher was not deterministic.

Every benchmark case produced more than one normalized Cypher
formulation across the five runs.

Depending on the case, between two and five distinct formulations were
observed.

Despite this variation:

```text
60/60 case executions remained fully correct
```

This is an important result.

LLM reliability does not require identical generated text or identical
Cypher structure on every run.

For this PoC, the important contract is:

```text
question
   ↓
safe executable Cypher
   ↓
correct graph facts
   ↓
grounded correct answer
```

Different valid Cypher formulations are acceptable when they satisfy
that contract.

## Engineering decision

No additional prompt tuning was performed simply to reduce Cypher
variation.

The repeated benchmark did not demonstrate a functional reliability
problem that justified such tuning.

This avoids optimizing the system toward one specific benchmark or one
preferred query shape without evidence that doing so improves the user
outcome.

## Limitations

The current reliability evidence is intentionally PoC-level:

- the graph contains synthetic data;
- the benchmark contains 12 cases;
- the repeated experiment contains 60 case executions;
- the configured model is `auto`;
- Cypher variation is based on normalized text, not formal semantic
  equivalence;
- the result does not establish production reliability.

The benchmark is nevertheless useful as a regression test for future
changes to retrieval, prompting, or agent behavior.