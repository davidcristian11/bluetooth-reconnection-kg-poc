# Bluetooth Reconnection Knowledge Graph PoC

A personal learning project demonstrating how synthetic automotive engineering data can be modeled in Neo4j and queried through a schema-guided LLM pipeline.

The AI experiment is best described as:

**Schema-guided Text-to-Cypher with graph-grounded answer generation.**

It is not a production GraphRAG system.

## Architecture

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

## Project structure

```text
contracts/       YAML Data Contracts for all CSV datasets
data/            Synthetic node and relationship CSV files
cypher/          Neo4j constraints, imports, and investigation queries
docs/            Project and architecture documentation
diagrams/        Ontology diagram
src/             Python AI experiment and data-quality pipeline
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

The project provides a controlled rebuild workflow that recreates
the local graph from the validated CSV source data.

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

The rebuild is intentionally destructive and is protected by two
safety checks:

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

This performs two complete rebuilds and compares deterministic graph
fingerprints. Both rebuilt graph states must be identical.

Detailed import instructions are available in [docs/05-neo4j-import.md](docs/05-neo4j-import.md).

## Run the AI experiment

Run the command from the repository root:

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

## AI evaluation benchmark

The current schema-guided Text-to-Cypher pipeline can be evaluated
against deterministic ground truth derived from the synthetic graph.

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

The configured model was `auto`, so this single baseline run is not
evidence of deterministic AI behavior. During calibration, structurally
different valid Cypher queries were observed across repeated runs.

See `evaluation/README.md` for benchmark design and scoring details.

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
- evaluation-runner success and failure behavior.

## Current safety controls

The prototype:

- validates generated Cypher before execution;
- blocks known write operations;
- permits only one Cypher statement;
- requires `MATCH` and `RETURN`;
- limits query execution time;
- limits the number of returned records;
- permits at most one Cypher correction attempt.

The Cypher validator is a best-effort safety filter, not a complete authorization boundary. The project should only use synthetic data in a local, isolated Neo4j instance.

## Current limitations

- The graph schema is manually provided to the LLM.
- A valid Cypher query can still be semantically incorrect.
- Empty results do not automatically trigger retry.
- `COPILOT_MODEL=auto` can select different models over time.
- There is no automated AI evaluation benchmark yet.
- There is no vector retrieval or hybrid retrieval.
- The pipeline is fixed and is not an autonomous agent.
- The Data Contract format is project-specific, not an industry-standard specification.
- The project is not intended for production use.

More details about the AI experiment are available in [docs/07-ontology-aware-ai-querying.md](docs/07-ontology-aware-ai-querying.md).