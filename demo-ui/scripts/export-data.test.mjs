import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { buildSnapshot, output, root } from "./export-data.mjs";

test("committed presentation snapshot exactly matches current repository sources", async () => {
  assert.deepEqual(
    JSON.parse(await readFile(output, "utf8")),
    await buildSnapshot(),
  );
});

test("investigation preserves all eight entities and correctly directed relationships", async () => {
  const d = await buildSnapshot();
  assert.deepEqual(d.investigationIds, [
    "COMP-002",
    "DEF-001",
    "EXEC-010",
    "REQ-002",
    "TEST-002",
    "TRACE-006",
    "TRACE-007",
    "TRACE-008",
  ]);
  assert.deepEqual(
    d.edges
      .filter(
        (e) =>
          d.investigationIds.includes(e.source) &&
          d.investigationIds.includes(e.target),
      )
      .map((e) => `${e.source} ${e.label} ${e.target}`)
      .sort(),
    [
      "COMP-002 IMPLEMENTS REQ-002",
      "DEF-001 AFFECTS COMP-002",
      "EXEC-010 EXECUTION_OF TEST-002",
      "EXEC-010 HAS_DEFECT_TICKET DEF-001",
      "EXEC-010 PRODUCES TRACE-006",
      "EXEC-010 PRODUCES TRACE-007",
      "EXEC-010 PRODUCES TRACE-008",
      "TEST-002 VERIFIES REQ-002",
    ],
  );
  const execution = d.nodes.find((n) => n.id === "EXEC-010");
  assert.equal(execution.properties.reconnectionTimeSeconds, "18.0");
  assert.equal(execution.properties.result, "FAIL");
});

test("retrieval metrics and RET-005 omissions are preserved from saved observations", async () => {
  const d = await buildSnapshot();
  const original = JSON.parse(
    await readFile(
      path.join(root, "evaluation/results/retrieval-experiment.json"),
      "utf8",
    ),
  );
  assert.deepEqual(d.retrieval.summary, original.summary);
  for (const c of d.retrieval.cases) {
    const source = original.results.find((s) => s.case_id === c.id);
    assert.deepEqual(c.flat.metrics, source.flat.metrics);
    assert.deepEqual(c.graph.metrics, source.graph.metrics);
    assert.equal(c.graph.cypher, source.graph.cypher);
  }
  const boundary = d.retrieval.cases.find((c) => c.id === "RET-005");
  assert.deepEqual(boundary.graph.metrics.missing_atoms, [
    "id:COMP-002",
    "id:REQ-002",
  ]);
  assert.equal(boundary.graph.metrics.evidence_complete, false);
});

test("agent replay retains observed answers and zero-versus-one tool decisions", async () => {
  const d = await buildSnapshot();
  const original = JSON.parse(
    await readFile(
      path.join(root, "evaluation/results/agent-evaluation.json"),
      "utf8",
    ),
  );
  assert.deepEqual(d.agent.summary, original.summary);
  for (const c of d.agent.cases)
    assert.deepEqual(
      c.response,
      original.results.find((r) => r.caseId === c.id).response,
    );
  assert.equal(
    d.agent.cases.find((c) => c.id === "AGT-001").response.graph_tool_calls,
    1,
  );
  assert.equal(
    d.agent.cases.find((c) => c.id === "AGT-006").response.graph_tool_calls,
    0,
  );
});
