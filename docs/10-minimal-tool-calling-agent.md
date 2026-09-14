# Minimal Tool-Calling Agent

## Goal

The purpose of this stage is to add a small agent layer on top of the existing Knowledge Graph retrieval pipeline.

Before this stage, the application followed a fixed flow:

```text
User question
      ↓
Text-to-Cypher
      ↓
Neo4j
      ↓
Retrieved graph facts
      ↓
Grounded answer
```

Every question sent through that pipeline resulted in graph retrieval.

The minimal agent introduces one additional decision:

```text
User question
      ↓
Minimal Agent
      ↓
Does the question require project graph data?
      ↓
   yes / no
   /      \
  v        v
graph      direct
tool       answer
  |
  v
existing graph retrieval
  |
  v
Neo4j facts
  |
  v
grounded final answer
```

The goal is not to build a general autonomous agent.

The goal is to demonstrate a small and controlled form of tool use:

> The LLM decides whether graph retrieval is necessary, calls the graph tool only when needed, and uses the returned evidence to produce the final answer.

---

## Design Principles

The agent was intentionally kept small.

The implementation uses:

```text
1 agent
1 custom tool
maximum 1 graph tool call per user question
existing graph retrieval pipeline
```

It does not introduce:

```text
LangChain
multi-agent orchestration
vector retrieval
MCP servers
external tools
planning loops
autonomous database modification
```

This keeps the experiment focused on the core concept of tool selection.

---

## Existing Retrieval Pipeline

The agent does not replace or redesign graph retrieval.

The existing retrieval path remains:

```text
Question
   ↓
QueryService.retrieve_question()
   ↓
LLM generates Cypher
   ↓
Cypher validation
   ↓
Neo4j execution
   ↓
Structured records
```

The existing retrieval controls are therefore reused:

- read-only Cypher validation;
- maximum two Cypher-generation attempts;
- corrective retry after validation errors;
- corrective retry after Neo4j errors;
- corrective retry after result-limit errors;
- conservative retry for suspicious empty results;
- Neo4j query timeout;
- maximum result count.

This distinction is important:

```text
agent tool call
!=
Cypher-generation attempt
```

The agent permits at most one `graph_retrieval` tool invocation for a user question.

Inside that single tool invocation, the existing retrieval service can still perform a second Cypher-generation attempt when its normal corrective retry rules apply.

---

## Graph Retrieval Tool

The agent exposes one custom tool:

```text
graph_retrieval
```

Its responsibility is deliberately narrow.

The tool accepts an engineering question and delegates retrieval to:

```text
QueryService.retrieve_question()
```

Conceptually:

```text
graph_retrieval(question)
        ↓
QueryService.retrieve_question(question)
        ↓
generated Cypher
        ↓
Neo4j
        ↓
records + retrieval metadata
```

The tool returns information including:

- the original question;
- the generated Cypher;
- retrieved Neo4j records;
- number of Cypher-generation attempts;
- retry reason when applicable.

The tool itself does not implement graph traversal logic.

It reuses the retrieval implementation that already existed before the agent stage.

---

## Tool-Call Limit

The graph tool can be invoked at most once for each agent question.

This is an explicit design decision for the PoC.

The goal is to demonstrate:

```text
minimal tool calling
```

rather than an open-ended agent loop.

If the model attempts to invoke `graph_retrieval` a second time during the same question, the tool rejects the second invocation.

This makes the behavior easier to understand, test, and evaluate.

---

## Agent Decision

The agent is instructed to use graph retrieval for factual questions about project engineering data.

Examples include questions about:

- Features;
- Requirements;
- SoftwareComponents;
- Tests;
- TestExecutions;
- TestTraces;
- DefectTickets;
- source systems;
- relationships between engineering artifacts;
- structured filters;
- counts;
- comparisons;
- graph-supported patterns.

For example:

```text
What requirement does TEST-006 verify?
```

requires project data and should use:

```text
graph_retrieval
```

A general conceptual question such as:

```text
What is a Knowledge Graph?
```

does not require project data.

The agent should answer it directly without calling Neo4j.

This creates two possible paths:

```text
project-specific factual question
→ graph tool
→ graph evidence
→ answer
```

and:

```text
general conceptual/conversational question
→ no graph tool
→ direct answer
```

---

## Grounding Rules

When the graph tool is used, the final answer must rely on the retrieved evidence.

The agent is instructed not to invent project-specific engineering facts.

If the returned evidence is incomplete, the answer should state that clearly.

A specific rule was also added for empty retrieval results.

An empty result:

```text
records = []
```

does not by itself prove:

```text
the entity does not exist in the entire Knowledge Graph
```

It proves only that the executed retrieval returned no matching records.

The preferred wording is therefore:

```text
No matching graph facts were retrieved for REQ-999.
```

rather than:

```text
REQ-999 does not exist in the Knowledge Graph.
```

unless the retrieved evidence explicitly establishes non-existence.

---

## Agent CLI

The agent can be run independently from the original AI query CLI.

Run:

```cmd
python src\agent_cli.py
```

The CLI shows the tool decision together with the final answer.

Example project-data question:

```text
What requirement does TEST-006 verify?
```

Observed behavior:

```text
graph_retrieval: USED
Tool calls: 1
Successful calls: 1
```

Example conceptual question:

```text
What is a Knowledge Graph?
```

Observed behavior:

```text
graph_retrieval: NOT USED
```

Keeping `agent_cli.py` separate from the original `cli.py` preserves both experiments:

```text
cli.py
→ fixed schema-guided Text-to-Cypher pipeline

agent_cli.py
→ minimal tool-calling agent
```

---

## Agent Benchmark

The agent benchmark is defined in:

```text
evaluation/agent_benchmark.yaml
```

It contains eight cases.

Five cases require graph retrieval:

```text
AGT-001  direct relationship
AGT-002  multi-hop
AGT-003  filtering
AGT-004  cross-environment
AGT-005  no-result handling
```

Three cases should be answered without graph retrieval:

```text
AGT-006  conceptual
AGT-007  capability
AGT-008  conversational
```

This split allows the benchmark to test both sides of the agent decision.

The goal is not simply:

```text
Can the agent call a tool?
```

It is also:

```text
Can the agent avoid calling the tool when it is unnecessary?
```

---

## Evaluation Metrics

The benchmark evaluates five behaviors.

### Tool Selection Correct

Checks whether the agent used `graph_retrieval` when required and avoided it when it was not required.

### Tool Call Count Correct

Checks that graph questions use no more than the allowed number of calls.

For the current PoC:

```text
graph question
→ maximum 1 graph tool call

non-graph question
→ 0 graph tool calls
```

### Tool Execution Success

Checks whether the requested graph tool invocation completed successfully.

### Answer Values Complete

For factual benchmark cases, the evaluator checks whether required expected values are present in the final answer.

For example:

```text
TEST-006
REQ-006
```

or:

```text
DEF-002
COMP-005
```

This is a deterministic answer check.

It is not a complete semantic judge of every sentence in the answer.

### No-Result Handling Correct

For the no-result case, the evaluator verifies that:

```text
retrieved record count = 0
```

and that the answer communicates the absence of matching retrieved information.

---

## Deterministic Evaluation

The agent benchmark does not use another LLM to judge the answer.

Evaluation is performed with deterministic Python logic.

This was chosen to keep the PoC:

- reproducible;
- understandable;
- inexpensive to run;
- independent from another probabilistic evaluator.

The tradeoff is that:

```text
answer_values_complete = true
```

does not prove that every statement in the generated answer is correct.

It confirms that the expected benchmark values are present.

Grounding is therefore supported by both:

```text
agent prompt rules
+
deterministic benchmark checks
```

but the benchmark is not a production-grade factuality evaluator.

---

## Observed Benchmark Result

The final observed benchmark run was executed with:

```text
Configured model: auto
Benchmark cases: 8
```

Result:

```text
Execution:                  8/8
Fully correct:              8/8
Tool selection correct:     8/8
Tool call count correct:    8/8
Tool execution success:     8/8
Answer values complete:     8/8
No-result handling correct: 8/8
```

The structured result is stored in:

```text
evaluation/results/agent-evaluation.json
```

The result file is an observed experiment artifact.

It is not deterministic ground truth because the agent and Text-to-Cypher steps use an LLM.

Future runs can produce different natural-language answers or Cypher queries.

---

## Tool-Selection Result

The five engineering-data cases all selected graph retrieval:

```text
AGT-001 → USED
AGT-002 → USED
AGT-003 → USED
AGT-004 → USED
AGT-005 → USED
```

Each used exactly:

```text
1 graph tool call
```

The three non-data cases correctly avoided graph retrieval:

```text
AGT-006 → NOT USED
AGT-007 → NOT USED
AGT-008 → NOT USED
```

Therefore the observed run produced:

```text
Graph-required cases:
5/5 correct tool selection

Graph-not-required cases:
3/3 correct tool avoidance
```

This is the main result of the Minimal Tool-Calling Agent stage.

---

## Example: Direct Relationship

Question:

```text
What requirement does TEST-006 verify?
```

Observed agent behavior:

```text
graph_retrieval: USED
tool calls: 1
retrieved records: 1
```

The final answer identified:

```text
TEST-006
→ verifies
REQ-006
```

This demonstrates the complete agent path:

```text
question
→ tool decision
→ graph retrieval
→ graph evidence
→ final answer
```

---

## Example: Structured Filtering

Question:

```text
Which test executions verifying REQ-002 exceeded the 10-second reconnection requirement?
```

The agent called graph retrieval once.

Five records were retrieved:

```text
EXEC-003
EXEC-006
EXEC-008
EXEC-010
EXEC-016
```

All required values appeared in the final answer.

This demonstrates that the agent layer can reuse the more complex filtering behavior already available through graph retrieval.

The agent itself does not implement the filtering logic.

Neo4j retrieval does.

---

## Example: Cross-Environment Investigation

Question:

```text
Which defect ticket is linked to failed executions in more than one test environment, and which environments are involved?
```

The final answer identified:

```text
DEF-001

SiL
HiL
Vehicle
```

The agent performed one graph tool call.

This shows that the tool-calling layer can expose relationship-dependent graph investigations without requiring the user to know Cypher.

---

## Example: No-Result Handling

Question:

```text
What information is available for requirement REQ-999?
```

The graph tool was correctly selected and returned:

```text
0 records
```

The final calibrated behavior was:

```text
No matching graph facts were retrieved for requirement REQ-999.
```

The answer did not treat an empty query result as definitive proof that the entity is absent from the entire graph.

This case was useful because it tested not only tool selection, but also careful interpretation of retrieval evidence.

---

## Example: No Tool Required

Question:

```text
What is a Knowledge Graph?
```

Observed behavior:

```text
graph_retrieval: NOT USED
tool calls: 0
```

The agent answered directly.

This is important because a useful tool-calling agent should not call an external tool merely because one is available.

Tool avoidance is part of correct agent behavior.

---

## Relationship to the Retrieval Experiment

The Minimal Tool-Calling Agent does not replace or alter the previous Retrieval Experiment.

The stages answer different questions.

The Retrieval Experiment asked:

```text
How does flat lexical retrieval compare with graph retrieval?
```

The Minimal Agent experiment asks:

```text
Should graph retrieval be used for this user question?
```

The architecture is therefore layered:

```text
Retrieval Experiment
→ evaluates retrieval strategies

Minimal Tool-Calling Agent
→ decides when to invoke existing graph retrieval
```

The previously observed retrieval results remain unchanged:

```text
Flat complete evidence:  7/10
Graph complete evidence: 9/10
```

The agent was added above the graph retrieval layer.

---

## Calibration Note

An earlier agent benchmark run produced:

```text
Fully correct: 7/8
```

The failing case was the no-result case.

That run revealed two issues:

1. the deterministic evaluator did not recognize the phrase `No results found` as valid no-result wording;
2. the agent wording could overstate what an empty result proved.

The benchmark definition and expected graph behavior were not changed.

Instead:

- the no-result evaluator vocabulary was corrected;
- the agent grounding instructions were strengthened.

The no-result case was then tested independently and passed.

A final full benchmark run produced:

```text
8/8 fully correct
```

This calibration is useful because it demonstrates that the benchmark was used to identify a real behavior issue rather than modified simply to produce a perfect score.

---

## What This Stage Demonstrates

The stage demonstrates four main concepts.

### 1. Tool selection

The LLM can decide whether project-specific graph evidence is required.

### 2. Minimal tool calling

The system performs at most one graph tool invocation per user question.

### 3. Tool reuse

The agent reuses the existing tested retrieval service rather than implementing a second graph-access path.

### 4. Grounded answer generation

When graph retrieval is used, structured Neo4j evidence is returned to the agent before the final answer is generated.

---

## What This Stage Does Not Demonstrate

The implementation should not be interpreted as a production autonomous agent.

It does not demonstrate:

- long-running autonomous workflows;
- multi-step planning across many tools;
- multi-agent collaboration;
- write actions;
- human approval workflows;
- persistent agent memory;
- production authorization;
- production observability;
- semantic answer judging;
- large-scale agent reliability.

Those capabilities are outside the scope of this PoC.

---

## Limitations

Important limitations include:

- the benchmark contains only eight synthetic cases;
- five cases require graph retrieval and three do not;
- the Knowledge Graph is small and synthetic;
- only one custom tool is available;
- only one graph tool call is permitted per question;
- tool selection depends on an LLM;
- Cypher generation inside the graph tool also depends on an LLM;
- `COPILOT_MODEL=auto` can change the selected model over time;
- the benchmark checks required answer values rather than every statement in the answer;
- the final 8/8 result is one observed run, not proof of deterministic reliability;
- no vector retrieval or hybrid retrieval is used;
- no MCP tools are used;
- no graph write operations are exposed to the agent.

---

## Conclusion

The Minimal Tool-Calling Agent adds a small decision layer above the existing Knowledge Graph retrieval system.

The final architecture is:

```text
User
 ↓
Minimal Agent
 ↓
Does this question need project graph evidence?
 ↓
 ├── no  → direct answer
 │
 └── yes
      ↓
 graph_retrieval
      ↓
 existing Text-to-Cypher retrieval
      ↓
 Neo4j
      ↓
 graph evidence
      ↓
 grounded final answer
```

The observed benchmark showed:

```text
8/8 correct tool selection
8/8 correct tool-call count
8/8 successful tool behavior
8/8 complete expected answer values
8/8 fully correct benchmark cases
```

The main learning result is:

> An agent does not need many tools or a complex framework to demonstrate useful agentic behavior. A small decision layer can selectively invoke an existing retrieval capability and keep unnecessary tool calls out of simpler interactions.

This completes the Minimal Tool-Calling Agent stage.