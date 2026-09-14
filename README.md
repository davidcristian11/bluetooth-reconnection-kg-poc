# Bluetooth Reconnection Knowledge Graph PoC

A personal learning project demonstrating how synthetic automotive engineering data can be modeled in Neo4j, retrieved through schema-guided Text-to-Cypher, and exposed through a minimal tool-calling agent.

The core AI retrieval pipeline is best described as:

**Schema-guided Text-to-Cypher with graph-grounded answer generation.**

The project also contains a minimal agent that decides when to invoke the existing graph retrieval capability.

It is not a production GraphRAG or autonomous-agent system.

## Architecture

The core graph retrieval pipeline is:

```text
Natural-language question
        ↓
LLM + graph schema
        ↓
Generated Cypher
        ↓
Safety validation
        ↓
Neo4j
        ↓
Structured graph facts
        ↓
LLM
        ↓
Grounded answer
```

The minimal tool-calling agent adds a decision layer above that existing retrieval path:

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
graph tool   direct answer
    |
    v
existing Text-to-Cypher retrieval
    |
    v
Neo4j facts
    |
    v
grounded final answer
```

The agent currently exposes one custom tool:

```text
graph_retrieval
```

and permits at most one graph tool invocation per user question.

## Project structure

```text
contracts/       YAML Data Contracts for all CSV datasets
data/            Synthetic node and relationship CSV files
cypher/          Neo4j constraints, imports, and investigation queries
docs/            Project and architecture documentation
diagrams/        Ontology diagram
evaluation/      AI, retrieval, and agent benchmark definitions and results
src/             Python AI, retrieval, agent, and data-quality code
tests/           Automated unit and integration tests
compose.yaml     Local Neo4j configuration
```

## Prerequisites

- Docker Desktop
- Python 3.11 or newer
- GitHub Copilot access and token

Tested environment:

```text
Python                 3.14.5
neo4j                  6.2.0
python-dotenv          1.2.3
github-copilot-sdk     1.0.11
PyYAML                 6.0.3
pytest                 9.1.1
```

## Python setup

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install runtime and development dependencies:

```powershell
python -m pip install -r requirements-dev.txt
python -m pip check
```

Optionally download and cache the Copilot runtime in advance:

```powershell
python -m copilot download-runtime
```

## Environment configuration

Copy the example configuration:

```powershell
Copy-Item .env.example .env
```

Configure the following values:

```text
NEO4J_URI=neo4j://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-local-password
NEO4J_DATABASE=neo4j
NEO4J_QUERY_TIMEOUT_SECONDS=5
NEO4J_MAX_RECORDS=100

COPILOT_GITHUB_TOKEN=your-token
COPILOT_MODEL=auto
```

Never commit the `.env` file.

## Data contracts and data-quality validation

Each CSV dataset has a corresponding YAML contract in the `contracts/` directory.

The contracts define:

- required columns;
- data types and allowed values;
- identifier patterns;
- primary-key and uniqueness rules;
- references between datasets;
- relationship coverage;
- domain-specific business rules.

Run validation from the repository root before importing data into Neo4j:

```powershell
python src\validate_data.py
```

A successful validation returns exit code `0`:

```text
DATA VALIDATION PASSED: 14 datasets validated.
```

A failed validation returns exit code `1` and reports the detected issues. The Neo4j import should not be executed when data validation fails.

The validation pipeline runs in this order:

```text
Contract loading
→ CSV structure validation
→ Row-value validation
→ Reference validation
→ Relationship coverage validation
→ Business-rule validation
```

The implemented business rules include:

- executions verifying `REQ-002` must be marked `FAIL` when reconnection exceeds 10 seconds;
- every `TestExecution` belongs to exactly one `Test`;
- every `TestTrace` belongs to exactly one `TestExecution`;
- trace and execution calendar dates must match;
- passed executions cannot have defect tickets;
- every defect ticket must be linked to a failed execution;
- required graph entities must have their mandatory relationships.

Data Contracts validate the source CSV files before import. They complement, rather than replace, the constraints enforced inside Neo4j.

## Start Neo4j

Validate the source data first:

```powershell
python src\validate_data.py
```

Start the local Neo4j instance:

```powershell
docker compose config --quiet
docker compose up -d
docker compose ps
```

## Rebuild Neo4j

The project provides a controlled rebuild workflow that recreates the local graph from the validated CSV source data.

The workflow runs:

```text
source-data validation
→ Neo4j connection
→ reset safety guard
→ graph cleanup
→ constraints
→ node import
→ relationship import
→ post-import validation
```

Run a rebuild from the repository root:

```powershell
python src\rebuild_neo4j.py --confirm-reset "RESET bluetooth-reconnection-kg-poc/neo4j"
```

The rebuild is intentionally destructive and is protected by two safety checks:

- the configured Neo4j host must be local;
- the reset confirmation must exactly match the target project and database.

Post-import validation checks:

- node and relationship counts against the source CSV files;
- duplicate or missing node IDs;
- required relationship coverage;
- the expected `EXEC-010` investigation scenario.

To verify reproducibility, run:

```powershell
python src\rebuild_neo4j.py --confirm-reset "RESET bluetooth-reconnection-kg-poc/neo4j" --verify-repeatability
```

This performs two complete rebuilds and compares deterministic graph fingerprints. Both rebuilt graph states must be identical.

Detailed import instructions are available in [docs/05-neo4j-import.md](docs/05-neo4j-import.md).

## Run the AI experiment

Run the fixed schema-guided query pipeline from the repository root:

```powershell
python src\cli.py
```

Example question:

```text
Why did EXEC-010 fail?
```

The CLI displays:

```text
GENERATED CYPHER
NEO4J RESULT
AI ANSWER
```

This CLI always uses the graph retrieval pipeline.

## Run the minimal tool-calling agent

Run:

```powershell
python src\agent_cli.py
```

The agent decides whether the user question requires project-specific graph evidence.

For an engineering-data question such as:

```text
What requirement does TEST-006 verify?
```

the expected behavior is:

```text
graph_retrieval: USED
Tool calls: 1
```

For a conceptual question such as:

```text
What is a Knowledge Graph?
```

the expected behavior is:

```text
graph_retrieval: NOT USED
```

The agent currently exposes only:

```text
graph_retrieval
```

and permits at most one graph tool invocation per user question.

## AI evaluation benchmark

The schema-guided Text-to-Cypher pipeline can be evaluated against deterministic ground truth derived from the synthetic graph.

The benchmark contains 12 questions across:

- entity lookup;
- relationship traversal;
- multi-hop reasoning;
- aggregation and filtering;
- no-result handling.

Run the benchmark:

```cmd
python src\run_evaluation.py
```

Optionally write the complete run details to a local JSON file:

```cmd
python src\run_evaluation.py --output evaluation\baseline-run.json
```

The benchmark measures separately:

- pipeline execution success;
- Neo4j retrieval correctness;
- grounded answer correctness.

A calibrated baseline run produced:

```text
Execution success: 12/12
Retrieval correct: 12/12
Answer correct: 12/12
Fully correct: 12/12
```

The configured model was `auto`, so this single baseline run is not evidence of deterministic AI behavior. During calibration, structurally different valid Cypher queries were observed across repeated runs.

See `evaluation/README.md` for benchmark design and scoring details.

### Repeated AI reliability evaluation

Run the complete benchmark repeatedly to measure run-to-run reliability:

```cmd
python src\run_reliability_evaluation.py --runs 5
```

The reliability experiment measures perfect-run rate, fully correct case rate, retries, failure types, and Cypher variation.

A five-run experiment on September 10, 2026 produced:

```text
60/60 fully correct case executions
5/5 perfect benchmark runs
0/60 executions requiring retry
```

Multiple valid Cypher formulations were observed for every benchmark case, showing that generation can vary while retrieval and answer correctness remain stable.

See [docs/08-ai-reliability.md](docs/08-ai-reliability.md) for details.

### Retrieval experiment

The project also contains a controlled retrieval experiment comparing:

```text
Flat lexical retrieval
vs
Schema-guided graph retrieval
```

Both strategies are evaluated against the same 10-case benchmark before final-answer generation.

An observed run produced:

```text
                     Flat        Graph
Complete evidence     7/10        9/10
Mean recall           0.847       0.980
Mean precision        0.492       1.000
```

The experiment showed that flat retrieval can be sufficient for simple direct lookups, while graph retrieval was substantially more selective and showed its clearest advantage for cross-source investigation, structured filtering, and relationship-dependent analysis.

The experiment also preserved one incomplete graph case, demonstrating that:

```text
graph capability != retrieval decision
```

The graph can contain relevant context that a generated Cypher query does not retrieve.

Run the comparison:

```cmd
python src\run_retrieval_experiment.py --output evaluation\results\retrieval-experiment.json
```

See [docs/09-retrieval-experiment.md](docs/09-retrieval-experiment.md) for methodology, results, and limitations.

### Minimal tool-calling agent evaluation

The project contains a separate benchmark for the minimal agent layer.

The benchmark contains:

```text
5 graph-required questions
3 no-graph-required questions
```

It evaluates:

- correct graph-tool selection;
- correct graph-tool avoidance;
- maximum tool-call count;
- tool execution success;
- presence of expected answer values;
- no-result handling.

The final observed run produced:

```text
Execution:                  8/8
Fully correct:              8/8
Tool selection correct:     8/8
Tool call count correct:    8/8
Tool execution success:     8/8
Answer values complete:     8/8
No-result handling correct: 8/8
```

All five project-data questions used `graph_retrieval` exactly once.

All three questions that did not require project graph data used zero graph tool calls.

Run the agent benchmark:

```cmd
python src\run_agent_evaluation.py
```

Run it and save the structured observed result:

```cmd
python src\run_agent_evaluation.py --output evaluation\results\agent-evaluation.json
```

The benchmark uses deterministic checks rather than an LLM judge.

`Answer values complete` verifies that required benchmark values appear in the generated answer. It does not semantically verify every sentence produced by the agent.

See [docs/10-minimal-tool-calling-agent.md](docs/10-minimal-tool-calling-agent.md) for architecture, benchmark design, results, and limitations.

## Run automated tests

Run the complete test suite:

```powershell
python -m pytest
```

For compact output:

```powershell
python -m pytest -q
```

The test suite covers:

- Cypher safety validation;
- query-service behavior and retry limits;
- Neo4j result limits;
- Data Contract loading;
- CSV structure and row-value validation;
- cross-dataset references;
- relationship coverage;
- domain-specific business rules;
- end-to-end validation of the repository datasets;
- Neo4j rebuild safety guards;
- rebuild execution order and fail-fast behavior;
- post-import validation and `EXEC-010`;
- deterministic graph fingerprint behavior;
- AI benchmark definition validation;
- deterministic retrieval and answer scoring;
- benchmark outcome classification;
- evaluation-runner success and failure behavior;
- retrieval benchmark definition validation;
- deterministic flat lexical retrieval;
- retrieval evidence scoring and flat-vs-graph experiment behavior;
- minimal graph-retrieval tool behavior;
- agent service behavior with and without tool use;
- agent benchmark definition validation;
- deterministic agent-response evaluation;
- agent evaluation runner behavior.

## Current safety controls

The prototype:

- validates generated Cypher before execution;
- blocks known write operations;
- permits only one Cypher statement;
- requires `MATCH` and `RETURN`;
- limits query execution time;
- limits the number of returned records;
- permits at most one Cypher correction attempt;
- exposes only one custom tool to the minimal agent;
- permits at most one graph tool invocation per user question;
- does not expose graph write operations to the agent.

The Cypher validator is a best-effort safety filter, not a complete authorization boundary. The project should only use synthetic data in a local, isolated Neo4j instance.

## Current limitations

- The graph schema is manually provided to the LLM.
- A valid Cypher query can still be semantically incorrect.
- Empty-result retry is conservative and currently requires explicit entity IDs from the question that can be confirmed in the graph.
- `COPILOT_MODEL=auto` can select different models over time.
- The automated AI benchmark contains 12 synthetic cases and should be treated as PoC regression evidence, not production-level reliability evidence.
- The retrieval experiment contains only 10 synthetic benchmark cases.
- There is no vector retrieval or hybrid retrieval.
- The agent is intentionally minimal: it exposes only one custom graph-retrieval tool and permits at most one graph tool invocation per question.
- The agent benchmark contains only eight synthetic cases and should be treated as PoC evidence, not production-level agent reliability evidence.
- Agent answer evaluation checks required values and selected no-result behavior; it does not semantically verify every generated statement.
- The project does not include multi-agent workflows, autonomous write actions, or MCP tools.
- The Data Contract format is project-specific, not an industry-standard specification.
- The project is not intended for production use.

More details about the AI retrieval pipeline are available in [docs/07-ontology-aware-ai-querying.md](docs/07-ontology-aware-ai-querying.md).

Detailed agent documentation is available in [docs/10-minimal-tool-calling-agent.md](docs/10-minimal-tool-calling-agent.md).