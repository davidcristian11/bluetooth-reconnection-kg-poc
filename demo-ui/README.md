# Bluetooth reconnection — visual demo

An isolated React + TypeScript + Vite presentation of the existing engineering PoC. React Flow displays the investigation graph; all data is bundled locally. No Python process, Docker, Neo4j connection, API key, or live LLM call is needed to present it.

## Run on Windows

Install Node.js 24 LTS (including npm), then open PowerShell:

```powershell
cd D:\David\personal_projects\bluetooth-reconnection-kg-poc\demo-ui
npx --yes pnpm@11.19.0 install --frozen-lockfile
npx --yes pnpm@11.19.0 dev
```

Open **http://127.0.0.1:5173**. Keep the PowerShell window running. Stop with Ctrl+C. If PowerShell blocks `npx.ps1`, use `npx.cmd` in place of `npx`.

For a recording, serve the production build:

```powershell
npx --yes pnpm@11.19.0 build
npx --yes pnpm@11.19.0 preview
```

Open **http://127.0.0.1:4173**. Ports are strict: if occupied, stop the other server or pass `--port 5174` to `dev` (or `--port 4174` to `preview`). Both servers bind only to the local machine.

Dependency downloads require internet for the initial installation. The built demo makes no API, font, analytics, or remote-asset requests. The React Flow attribution link only opens an external site when clicked.

## Presentation controls

- Five sidebar views, each with a shareable hash route (`#overview`, `#investigation`, `#sources`, `#retrieval`, `#agent`). Browser back/forward works.
- **Present** hides the sidebar and adds a compact chapter selector. The browser's own full-screen mode is optional.
- Keyboard: **1–5** switch views, **P** toggles presentation, **Esc** exits presentation or closes About. View shortcuts are inactive while an interactive control is focused; click a page heading first.
- Investigation: select nodes for all source properties and file provenance; pan, zoom, and fit the graph. **Run investigation** reveals six steps. Pause/resume, select a step, or reset with **Show full graph**. Changing views cancels pending playback.
- Source systems: select a source to highlight its ontology types and preview its records. Source systems remain metadata properties; the UI does not introduce new graph entities.
- Retrieval: switch the four featured cases, or use the dropdown for any of the ten cases. Inspect the exact observed Cypher. RET-005 retains the observed missing requirement/component evidence.
- Agent: switch the two recorded questions, or replay the selected decision. Recorded outputs are summarized from the saved answers. Tool calls are visual replays, not new agent executions.
- Responsive layouts support narrow screens; a desktop display is recommended for recording. Reduced-motion preferences disable visual transitions and animated edges.

## Suggested two-minute recording

| Time      | View          | Talking point                                                                                                         |
| --------- | ------------- | --------------------------------------------------------------------------------------------------------------------- |
| 0:00–0:20 | Overview      | Synthetic engineering systems become contract-validated, connected evidence, then feed retrieval and a minimal agent. |
| 0:20–1:10 | Investigation | Run the story; inspect TRACE-007's 8.9-second queue delay, REQ-002's timing requirement, and COMP-002.                |
| 1:10–1:40 | Retrieval     | Contrast filtering and precision; select RET-005 to explain graph capability versus retrieval decision.               |
| 1:40–2:00 | Agent         | Switch project-specific and conceptual questions: one graph call versus zero.                                         |

Source Systems is an optional detour or a useful slide screenshot. **1920 × 1080** gives the graph and property panel more room.

## Data derivation and boundaries

`scripts/export-data.mjs` reads only these repository inputs:

- `../contracts/*.yaml`: entity labels, CSV paths, relationship types and ordered primary keys.
- `../data/nodes/*.csv` and `../data/relationships/*.csv`: actual properties and directed relationships.
- `../evaluation/results/retrieval-experiment.json`: saved summary metrics, case evidence atoms, query attempts, and Cypher.
- `../evaluation/results/agent-evaluation.json`: saved summary checks, decisions, tool counts, and answers.

It writes **only** `src/data/demo.json`. The snapshot includes all 52 node records and 64 relationships, six source groups, ten retrieval cases, eight agent cases, and SHA-256 fingerprints of all inputs. The investigation scope follows EXEC-010's direct evidence, the test's verified requirements, and the defect's affected components. Other requirements implemented by the component remain outside this focused view.

The UI uses curated layout coordinates and narrative captions for this specific synthetic scenario. Engineering properties, provenance, case metrics, evidence omissions, and agent outputs come from the generated snapshot. If the underlying scenario changes, review the story captions and layout as well as regenerating the snapshot.

The snapshot regenerates before development and builds. To refresh or check it explicitly:

```powershell
npx --yes pnpm@11.19.0 data
node scripts/export-data.mjs --check
```

Saved evaluation artifacts are observations, not benchmark ground truth. Nothing in the demo reruns evaluations or writes to the backend, contracts, ontology, synthetic CSVs, benchmark definitions, or recorded results. The results remain small synthetic PoC evidence. Agent answer-value checks do not semantically validate every sentence.

## Checks

```powershell
npx --yes pnpm@11.19.0 lint
npx --yes pnpm@11.19.0 test
npx --yes pnpm@11.19.0 build
```

Build includes strict TypeScript checks. Data tests detect snapshot drift, incorrect investigation scope/directions, changes to copied retrieval evidence, and changes to copied agent outputs. To intentionally update repository data, regenerate the snapshot before running tests; the fixed EXEC-010 expectations should only change if the engineering scenario actually changes.

Formatting: `npx --yes pnpm@11.19.0 format`. The generated JSON and lockfile are excluded from formatting.

All frontend files, its lockfile, dependency policy, and local ignore rules live in this directory. Existing project files are untouched.

Library references: [React Flow](https://reactflow.dev/api-reference/react-flow), [Vite](https://vite.dev/guide/).
