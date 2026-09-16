import { readFile, readdir, mkdir, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { createHash } from "node:crypto";
import { parse as parseCsv } from "csv-parse/sync";
import { parse as parseYaml } from "yaml";

export const root = fileURLToPath(new URL("../../", import.meta.url));
export const output = fileURLToPath(
  new URL("../src/data/demo.json", import.meta.url),
);

export async function buildSnapshot() {
  const inputs = [];
  const read = async (relative) => {
    const content = await readFile(path.join(root, relative), "utf8");
    inputs.push({
      path: relative,
      sha256: createHash("sha256").update(content).digest("hex"),
    });
    return content;
  };
  const nodes = [];
  const edges = [];
  for (const file of (await readdir(path.join(root, "contracts")))
    .filter((f) => f.endsWith(".yaml"))
    .sort()) {
    const contract = parseYaml(await read(`contracts/${file}`));
    const rows = parseCsv(await read(contract.dataset.path), {
      columns: true,
      skip_empty_lines: true,
      bom: true,
    });
    if (contract.dataset.kind === "relationship") {
      const [source, target] = contract.primaryKey;
      for (const row of rows)
        edges.push({
          id: `${contract.dataset.relationshipType}:${row[source]}:${row[target]}`,
          source: row[source],
          target: row[target],
          label: contract.dataset.relationshipType,
          file: contract.dataset.path,
        });
    } else {
      for (const row of rows)
        nodes.push({
          id: row.id,
          label: contract.dataset.entity,
          properties: row,
          file: contract.dataset.path,
        });
    }
  }
  const ids = new Set(nodes.map((n) => n.id));
  if (
    ids.size !== nodes.length ||
    edges.some((e) => !ids.has(e.source) || !ids.has(e.target))
  )
    throw new Error(
      "Invalid snapshot: duplicate node or dangling relationship.",
    );
  const retrieval = JSON.parse(
    await read("evaluation/results/retrieval-experiment.json"),
  );
  const agent = JSON.parse(
    await read("evaluation/results/agent-evaluation.json"),
  );
  // Follow execution evidence, its test's requirements, and its defects' components.
  // Other requirements implemented by that component are outside this investigation.
  const investigationIds = new Set(["EXEC-010"]);
  const direct = edges.filter((e) => e.source === "EXEC-010");
  direct.forEach((e) => investigationIds.add(e.target));
  const tests = direct
    .filter((e) => e.label === "EXECUTION_OF")
    .map((e) => e.target);
  const defects = direct
    .filter((e) => e.label === "HAS_DEFECT_TICKET")
    .map((e) => e.target);
  edges
    .filter(
      (e) =>
        (tests.includes(e.source) && e.label === "VERIFIES") ||
        (defects.includes(e.source) && e.label === "AFFECTS"),
    )
    .forEach((e) => investigationIds.add(e.target));
  if (!ids.has("EXEC-010"))
    throw new Error("EXEC-010 is missing from the repository dataset.");
  return {
    provenance: {
      description:
        "Static presentation snapshot derived from repository sources. Evaluation results are saved observations, not live executions.",
      inputs: inputs.sort((a, b) => a.path.localeCompare(b.path)),
    },
    nodes,
    edges,
    investigationIds: [...investigationIds].sort(),
    sources: [...new Set(nodes.map((n) => n.properties.sourceSystem))]
      .sort()
      .map((name) => ({
        name,
        labels: [
          ...new Set(
            nodes
              .filter((n) => n.properties.sourceSystem === name)
              .map((n) => n.label),
          ),
        ],
        count: nodes.filter((n) => n.properties.sourceSystem === name).length,
      })),
    retrieval: {
      model: retrieval.configured_model,
      summary: retrieval.summary,
      cases: retrieval.results.map((c) => ({
        id: c.case_id,
        category: c.category,
        question: c.question,
        flat: { metrics: c.flat.metrics, count: c.flat.retrieved_count },
        graph: {
          metrics: c.graph.metrics,
          count: c.graph.retrieved_count,
          cypher: c.graph.cypher,
          attempts: c.graph.generation_attempts,
          retryReason: c.graph.retry_reason,
        },
      })),
    },
    agent: {
      summary: agent.summary,
      cases: agent.results.map((c) => ({
        id: c.caseId,
        question: c.question,
        response: c.response,
        evaluation: c.evaluation,
      })),
    },
  };
}

if (
  process.argv[1] &&
  path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)
) {
  const snapshot = await buildSnapshot();
  const json = JSON.stringify(snapshot, null, 2) + "\n";
  if (process.argv.includes("--check")) {
    if ((await readFile(output, "utf8")) !== json)
      throw new Error("Snapshot is stale. Run npm run data.");
    console.log("Snapshot matches repository sources.");
  } else {
    await mkdir(path.dirname(output), { recursive: true });
    await writeFile(output, json);
    console.log(
      `Exported ${snapshot.nodes.length} entities, ${snapshot.edges.length} relationships, ${snapshot.retrieval.cases.length} retrieval cases, and ${snapshot.agent.cases.length} agent cases.`,
    );
  }
}
