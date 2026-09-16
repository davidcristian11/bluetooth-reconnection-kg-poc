import { useEffect, useState } from "react";
import type { CSSProperties } from "react";
import {
  Activity,
  ArrowRight,
  ArrowUpRight,
  Bluetooth,
  Check,
  ChevronLeft,
  ChevronRight,
  CircleHelp,
  Database,
  FileCheck2,
  GitBranch,
  Layers,
  LayoutDashboard,
  Maximize2,
  Network,
  Pause,
  Play,
  Radio,
  RotateCcw,
  ShieldCheck,
  Sparkles,
  Workflow,
  X,
} from "lucide-react";
import { InvestigationGraph, nodeIcons } from "./Graph";
import { colors, data, entities, entity, pretty, title } from "./model";

const views = [
  {
    id: "overview",
    label: "Project overview",
    icon: LayoutDashboard,
    title: "From disconnected data to connected evidence.",
    subtitle: "Bluetooth phone reconnection after a vehicle ignition cycle.",
  },
  {
    id: "investigation",
    label: "EXEC-010 investigation",
    icon: Network,
    title: "One failure. The full engineering context.",
    subtitle:
      "Follow the evidence from a failed vehicle execution to its requirement and affected component.",
  },
  {
    id: "sources",
    label: "Source systems",
    icon: Layers,
    title: "Different systems. A shared language.",
    subtitle:
      "Six synthetic engineering sources, connected through one common semantic model.",
  },
  {
    id: "retrieval",
    label: "Retrieval comparison",
    icon: GitBranch,
    title: "Better context. More selective retrieval.",
    subtitle:
      "Flat lexical search and schema-guided graph retrieval, measured against the same 10 cases.",
  },
  {
    id: "agent",
    label: "Minimal agent",
    icon: Sparkles,
    title: "The right tool. Only when needed.",
    subtitle:
      "One custom tool. One decision. Evidence when the question calls for it.",
  },
];
type View = (typeof views)[number]["id"];
const fromHash = () =>
  views.some((v) => v.id === location.hash.slice(1))
    ? location.hash.slice(1)
    : "overview";
const stages = [
  {
    name: "Failed execution",
    ids: ["EXEC-010"],
    text: "EXEC-010 failed in Vehicle testing. Reconnection took 18.0 seconds.",
  },
  {
    name: "Test definition",
    ids: ["TEST-002"],
    text: "EXECUTION_OF connects this run to TEST-002: reconnection time verification.",
  },
  {
    name: "Expected behavior",
    ids: ["REQ-002"],
    text: "TEST-002 verifies REQ-002: reconnect within 10 seconds after the Bluetooth subsystem becomes available.",
  },
  {
    name: "Diagnostic evidence",
    ids: ["TRACE-006", "TRACE-007", "TRACE-008"],
    text: "Three traces record ignition, an 8.9-second queue delay, and reconnection at 18.0 seconds.",
  },
  {
    name: "Linked defect",
    ids: ["DEF-001"],
    text: "DEF-001 documents delayed Bluetooth reconnection after ignition. Status: Open. Severity: Critical.",
  },
  {
    name: "Affected component",
    ids: ["COMP-002"],
    text: "DEF-001 affects COMP-002, the Bluetooth Connection Manager, which implements REQ-002.",
  },
];

function Badge({
  children,
  tone = "",
}: {
  children: React.ReactNode;
  tone?: string;
}) {
  return <span className={`badge ${tone}`}>{children}</span>;
}
function App() {
  const [view, setView] = useState<View>(fromHash);
  const [present, setPresent] = useState(false);
  const [help, setHelp] = useState(false);
  const current = views.find((v) => v.id === view)!;
  const go = (next: View) => {
    location.hash = next;
    setView(next);
    window.scrollTo({ top: 0 });
  };
  useEffect(() => {
    const change = () => setView(fromHash());
    window.addEventListener("hashchange", change);
    return () => window.removeEventListener("hashchange", change);
  }, []);
  useEffect(() => {
    const key = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setPresent(false);
        setHelp(false);
        return;
      }
      if (help) {
        if (e.key === "Tab") {
          e.preventDefault();
          document.querySelector<HTMLButtonElement>(".modal .close")?.focus();
        }
        return;
      }
      if (
        (e.target as HTMLElement).closest("button,input,select,textarea,a") ||
        e.ctrlKey ||
        e.altKey ||
        e.metaKey
      )
        return;
      if (/^[1-5]$/.test(e.key)) location.hash = views[Number(e.key) - 1].id;
      if (e.key.toLowerCase() === "p") setPresent((p) => !p);
    };
    window.addEventListener("keydown", key);
    return () => window.removeEventListener("keydown", key);
  }, [help]);
  return (
    <div className={`app ${present ? "presentation" : ""}`}>
      <aside className="sidebar">
        <a className="brand" href="#overview">
          <span className="brand-symbol">
            <Bluetooth size={25} />
          </span>
          <span>
            reconnection
            <span className="brand-sub">ENGINEERING INTELLIGENCE</span>
          </span>
        </a>
        <div className="workspace-label">
          KNOWLEDGE GRAPH <Badge>PoC</Badge>
        </div>
        <nav aria-label="Demo views">
          {views.map((v, i) => (
            <button
              key={v.id}
              className={v.id === view ? "nav-item selected" : "nav-item"}
              onClick={() => go(v.id)}
              aria-current={v.id === view ? "page" : undefined}
            >
              <v.icon size={18} />
              <span>{v.label}</span>
              <span className="nav-index">0{i + 1}</span>
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="scope-card">
            <span className="small-label">
              <Radio size={14} /> DEMO ENVIRONMENT
            </span>
            <strong>Built on connected facts.</strong>
            <p>
              Synthetic automotive data.
              <br />
              Real relationships. Recorded results.
            </p>
            <span className="status-dot" /> Static snapshot ready
          </div>
          <button className="quiet" onClick={() => setHelp(true)}>
            <CircleHelp size={16} /> About this demo <ArrowUpRight size={14} />
          </button>
        </div>
      </aside>
      <div className="workspace">
        <header className="topbar">
          <div className="breadcrumb">
            Workspace <ChevronRight size={14} />
            <span>Bluetooth reconnection</span>
          </div>
          <div className="top-actions">
            <span className="snapshot-status">
              <span className="status-dot" /> Repository snapshot
            </span>
            <button
              className="secondary small"
              onClick={() => setPresent(!present)}
            >
              <Maximize2 size={14} />
              {present ? "Exit presentation" : "Present"}
            </button>
          </div>
        </header>
        {present && (
          <nav className="presentation-nav" aria-label="Presentation views">
            {views.map((v, i) => (
              <button
                key={v.id}
                className={view === v.id ? "active" : ""}
                onClick={() => go(v.id)}
              >
                0{i + 1} {v.label}
              </button>
            ))}
          </nav>
        )}
        <main>
          <div className="page-heading">
            <div>
              <div className="eyebrow">
                <span /> AUTOMOTIVE ENGINEERING / {current.label.toUpperCase()}
              </div>
              <h1>{current.title}</h1>
              <p>{current.subtitle}</p>
            </div>
            <span className="chapter">
              0{views.indexOf(current) + 1}
              <span>/ 05</span>
            </span>
          </div>
          <div key={view} className="view-enter">
            {view === "overview" && <Overview go={go} />}{" "}
            {view === "investigation" && <Investigation />}{" "}
            {view === "sources" && <Sources go={go} />}{" "}
            {view === "retrieval" && <Retrieval go={go} />}{" "}
            {view === "agent" && <Agent />}
          </div>
          <footer>
            <span>
              BLUETOOTH RECONNECTION <span className="footer-separator">/</span>{" "}
              KNOWLEDGE GRAPH PoC
            </span>
            <span>
              Synthetic data · Saved observations · No live LLM required
            </span>
          </footer>
        </main>
      </div>
      {help && (
        <div className="modal-backdrop" onClick={() => setHelp(false)}>
          <section
            role="dialog"
            aria-modal="true"
            aria-label="About this demo"
            className="modal"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              autoFocus
              className="icon-button close"
              aria-label="Close about"
              onClick={() => setHelp(false)}
            >
              <X size={20} />
            </button>
            <div className="eyebrow">REPOSITORY-BACKED DEMO</div>
            <h2>Engineering evidence, made visible.</h2>
            <p>
              This presentation reads a static snapshot generated from the
              repository’s CSV datasets, Data Contracts, and saved evaluation
              JSON. It does not execute an agent, an LLM, or Neo4j.
            </p>
            <p>
              The small synthetic benchmarks show observed PoC behavior, not
              production reliability. Agent answer checks verify expected
              values; they do not verify every sentence.
            </p>
            <div className="keyboard-help">
              <kbd>1–5</kbd> Switch view <kbd>P</kbd> Present <kbd>Esc</kbd>{" "}
              Exit
            </div>
            <small>
              {data.provenance.inputs.length} source files recorded with SHA-256
              fingerprints.
            </small>
          </section>
        </div>
      )}
    </div>
  );
}

function Overview({ go }: { go: (v: View) => void }) {
  const pipeline = [
    {
      icon: Layers,
      title: "Source systems",
      sub: "Synthetic engineering data",
      view: "sources",
    },
    {
      icon: ShieldCheck,
      title: "Data contracts",
      sub: "Validate before import",
      view: "sources",
    },
    {
      icon: Workflow,
      title: "Ontology",
      sub: "7 shared entity types",
      view: "sources",
    },
    {
      icon: Database,
      title: "Neo4j graph",
      sub: "Connected evidence",
      view: "investigation",
    },
    {
      icon: GitBranch,
      title: "Text-to-Cypher",
      sub: "Schema-guided retrieval",
      view: "retrieval",
    },
    {
      icon: Activity,
      title: "Evaluation",
      sub: "Measure evidence quality",
      view: "retrieval",
    },
    {
      icon: Sparkles,
      title: "Minimal agent",
      sub: "Choose when to retrieve",
      view: "agent",
    },
  ];
  return (
    <>
      <section className="overview-hero panel">
        <div className="hero-copy">
          <Badge tone="green">
            <span className="status-dot" /> CONNECTED INVESTIGATION
          </Badge>
          <h2>
            A failed reconnection.
            <br />
            <em>A traceable story.</em>
          </h2>
          <p>
            Connect a vehicle test failure to its requirement, diagnostic
            traces, defect, and software component.
          </p>
          <button className="primary" onClick={() => go("investigation")}>
            Explore EXEC-010 <ArrowUpRight size={17} />
          </button>
          <div className="hero-meta">
            <span>
              <span className="fail-dot" /> FAIL
            </span>
            <span>Vehicle</span>
            <span>18.0 s reconnection</span>
          </div>
        </div>
        <div className="hero-graph">
          <div className="graph-top-label">
            <span className="status-dot" /> EXEC-010 · EVIDENCE NEIGHBORHOOD{" "}
            <span>8 NODES / 8 EDGES</span>
          </div>
          <InvestigationGraph compact onSelect={() => go("investigation")} />
          <span className="hero-graph-caption">
            Every connection has an engineering meaning.
          </span>
        </div>
      </section>
      <div className="stat-grid">
        {[
          {
            value: entities.length,
            label: "Engineering entities",
            icon: Database,
            detail: "Across 7 ontology types",
          },
          {
            value: data.edges.length,
            label: "Typed relationships",
            icon: Network,
            detail: "Explicit, traversable connections",
          },
          {
            value: data.sources.length,
            label: "Source systems",
            icon: Layers,
            detail: "One common semantic model",
          },
          {
            value: `${data.agent.summary.fullyCorrect}/${data.agent.summary.cases}`,
            label: "Agent cases correct",
            icon: Check,
            detail: "Observed benchmark result",
          },
        ].map((s) => (
          <div className="stat panel" key={s.label}>
            <div>
              <span className="stat-label">{s.label}</span>
              <s.icon size={17} />
            </div>
            <strong>{s.value}</strong>
            <span className="muted">{s.detail}</span>
          </div>
        ))}
      </div>
      <section className="panel pipeline-panel">
        <div className="section-title">
          <div>
            <div className="eyebrow">THE PROJECT, END TO END</div>
            <h2>From source records to a grounded answer</h2>
          </div>
          <Badge>7 stages</Badge>
        </div>
        <div className="pipeline">
          {pipeline.map((p, i) => (
            <button
              key={p.title}
              onClick={() => go(p.view)}
              className={`pipeline-step ${i === 3 ? "highlight" : ""}`}
            >
              <span className="pipeline-icon">
                <p.icon size={22} />
              </span>
              <span className="step-number">0{i + 1}</span>
              <strong>{p.title}</strong>
              <small>{p.sub}</small>
              {i < 6 && <ChevronRight className="pipeline-arrow" size={15} />}
            </button>
          ))}
        </div>
      </section>
      <div className="overview-bottom">
        <span>
          <ShieldCheck size={16} /> Contract-validated sources · Reproducible
          graph rebuild
        </span>
        <button className="text-button" onClick={() => go("retrieval")}>
          See what the experiments found <ArrowRight size={16} />
        </button>
      </div>
    </>
  );
}

function Investigation() {
  const [selected, setSelected] = useState("EXEC-010");
  const [stage, setStage] = useState<number | null>(null);
  const [running, setRunning] = useState(false);
  useEffect(() => {
    if (!running) return;
    const timer = window.setTimeout(() => {
      if (stage === null || stage >= stages.length - 1) {
        setRunning(false);
        return;
      }
      setStage(stage + 1);
      setSelected(stages[stage + 1].ids[0]);
    }, 2800);
    return () => clearTimeout(timer);
  }, [running, stage]);
  const selectedNode = entity(selected);
  const Icon = nodeIcons[selectedNode.label as keyof typeof nodeIcons];
  const revealed =
    stage === null
      ? undefined
      : stages.slice(0, stage + 1).flatMap((s) => s.ids);
  const moveStage = (next: number) => {
    setStage(next);
    setSelected(stages[next].ids[0]);
    setRunning(false);
  };
  return (
    <>
      <div className="investigation-toolbar">
        <div className="inline">
          <Badge tone="orange">FAIL</Badge>
          <span className="mono">EXEC-010</span>
          <span className="muted">Vehicle · 21 Jul 2026 · v2.3.0</span>
        </div>
        <div className="inline">
          <button
            className="secondary"
            onClick={() => {
              setStage(null);
              setRunning(false);
              setSelected("EXEC-010");
            }}
          >
            <RotateCcw size={14} /> Show full graph
          </button>
          <button
            className="primary"
            onClick={() => {
              if (running) setRunning(false);
              else {
                if (stage === null || stage === 5) {
                  setStage(0);
                  setSelected("EXEC-010");
                }
                setRunning(true);
              }
            }}
          >
            {running ? <Pause size={15} /> : <Play size={15} />}{" "}
            {running
              ? "Pause story"
              : stage !== null && stage < 5
                ? "Resume story"
                : "Run investigation"}
          </button>
        </div>
      </div>
      <div className="investigation-layout">
        <section className="panel graph-panel">
          <div className="panel-bar">
            <span>
              <Network size={15} /> Engineering evidence graph
            </span>
            <span className="muted">Select a node to inspect</span>
          </div>
          <InvestigationGraph
            selected={selected}
            onSelect={setSelected}
            revealed={revealed}
          />
          <div className="graph-legend">
            {Object.entries(colors)
              .filter(([name]) => name !== "Feature")
              .map(([name, color]) => (
                <span key={name}>
                  <i style={{ background: color }} />
                  {pretty(name)}
                </span>
              ))}
          </div>
        </section>
        <aside className="panel inspector" aria-live="polite">
          <div className="inspector-heading">
            <span className="small-label">ENTITY DETAILS</span>
            <ArrowUpRight size={16} />
          </div>
          <span
            className="entity-icon"
            style={{
              color: colors[selectedNode.label],
              background: `${colors[selectedNode.label]}15`,
            }}
          >
            <Icon size={25} />
          </span>
          <div
            className="small-label"
            style={{ color: colors[selectedNode.label] }}
          >
            {pretty(selectedNode.label)}
          </div>
          <h2>{selectedNode.id}</h2>
          <p>{title(selectedNode)}</p>
          <dl>
            {Object.entries(selectedNode.properties)
              .filter(
                ([k]) =>
                  !["id", "title", "name", "message", "sourceSystem"].includes(
                    k,
                  ),
              )
              .map(([key, value]) => (
                <div key={key}>
                  <dt>{pretty(key)}</dt>
                  <dd className={value === "FAIL" ? "orange-text" : ""}>
                    {value}
                  </dd>
                </div>
              ))}
          </dl>
          <div className="provenance">
            <span className="small-label">
              <Database size={13} /> SOURCE PROVENANCE
            </span>
            <strong>{selectedNode.properties.sourceSystem}</strong>
            <code>{selectedNode.file}</code>
          </div>
        </aside>
      </div>
      <section
        className={`panel story-panel ${stage !== null ? "playing" : ""}`}
      >
        <div className="story-caption">
          <span className="small-label">
            {stage === null
              ? "FOLLOW THE EVIDENCE"
              : `GUIDED INVESTIGATION · ${stage + 1} / ${stages.length}`}
          </span>
          <p aria-live="polite">
            {stage === null
              ? "From a failed execution to the component responsible for reconnection."
              : stages[stage].text}
          </p>
        </div>
        <div className="story-steps">
          {stages.map((s, i) => (
            <button
              key={s.name}
              className={
                stage === i
                  ? "current"
                  : stage !== null && i < stage
                    ? "done"
                    : ""
              }
              onClick={() => moveStage(i)}
              aria-label={`Step ${i + 1}: ${s.name}`}
            >
              <span>
                {stage !== null && i < stage ? <Check size={12} /> : i + 1}
              </span>
              {s.name}
            </button>
          ))}
        </div>
        {stage !== null && (
          <div className="story-controls">
            <button
              className="icon-button"
              aria-label="Previous investigation step"
              disabled={stage === 0}
              onClick={() => moveStage(stage - 1)}
            >
              <ChevronLeft size={16} />
            </button>
            <button
              className="icon-button"
              aria-label="Next investigation step"
              disabled={stage === 5}
              onClick={() => moveStage(stage + 1)}
            >
              <ChevronRight size={16} />
            </button>
          </div>
        )}
      </section>
    </>
  );
}

function Sources({ go }: { go: (v: View) => void }) {
  const [selected, setSelected] = useState(data.sources[0].name);
  const source = data.sources.find((s) => s.name === selected)!;
  return (
    <>
      <section className="sources-layout">
        <div className="source-stack">
          <div className="small-label">01 / SYNTHETIC SOURCE SYSTEMS</div>
          {data.sources.map((s) => (
            <button
              key={s.name}
              className={`source-card panel ${s.name === selected ? "active" : ""}`}
              onClick={() => setSelected(s.name)}
            >
              <span className="source-icon">
                <Layers size={19} />
              </span>
              <div>
                <strong>{s.name}</strong>
                <small>{s.labels.map(pretty).join(" + ")}</small>
              </div>
              <span className="source-count">{s.count}</span>
              <ChevronRight size={14} />
            </button>
          ))}
        </div>
        <div className="semantic-column">
          <div className="small-label">02 / COMMON SEMANTIC MODEL</div>
          <div className="semantic-model panel">
            <span className="semantic-orbit">
              <Network size={39} />
            </span>
            <Badge tone="green">SHARED ONTOLOGY</Badge>
            <h2>
              Meaning connects
              <br />
              the records.
            </h2>
            <p>
              Each source artifact becomes a typed entity. Explicit
              relationships connect the engineering lifecycle.
            </p>
            <div className="ontology-types">
              {Object.entries(colors).map(([name, color]) => (
                <span
                  key={name}
                  className={source.labels.includes(name) ? "lit" : ""}
                  style={{ "--node-color": color } as CSSProperties}
                >
                  <i style={{ background: color }} />
                  {pretty(name)}
                </span>
              ))}
            </div>
            <div className="ontology-foot">
              <ShieldCheck size={15} /> Data Contracts validate every source
              dataset
            </div>
          </div>
        </div>
        <div className="connected-column">
          <div className="small-label">03 / CONNECTED INVESTIGATION</div>
          <div className="panel source-detail">
            <Badge tone="green">SOURCE SPOTLIGHT</Badge>
            <h2>{pretty(selected)}</h2>
            <p>{source.count} artifacts contribute to the shared graph.</p>
            <div className="source-artifacts">
              {entities
                .filter((n) => n.properties.sourceSystem === selected)
                .slice(0, 5)
                .map((n) => (
                  <div key={n.id}>
                    <span className="mono">{n.id}</span>
                    <span>{title(n)}</span>
                  </div>
                ))}
            </div>
            {source.count > 5 && (
              <small className="muted">
                + {source.count - 5} more artifacts in the snapshot
              </small>
            )}
            <button className="primary" onClick={() => go("investigation")}>
              Follow connected evidence <ArrowRight size={16} />
            </button>
          </div>
          <div className="source-note">
            <GitBranch size={21} />
            <p>
              <strong>Provenance travels with the facts.</strong>
              <br />
              <code>sourceSystem</code> is an entity property, not a separate
              graph node.
            </p>
          </div>
        </div>
      </section>
      <div className="takeaway">
        <span className="small-label">THE CONNECTION</span>
        <strong>
          Different source systems <ArrowRight size={18} /> common semantic
          model <ArrowRight size={18} /> connected investigation
        </strong>
      </div>
    </>
  );
}

function Retrieval({ go }: { go: (v: View) => void }) {
  const [selected, setSelected] = useState("RET-009");
  const [showCypher, setShowCypher] = useState(false);
  const c = data.retrieval.cases.find((c) => c.id === selected)!;
  const missing = new Set<string>(c.graph.metrics.missing_atoms);
  const metrics = [
    { label: "Complete evidence", key: "evidence_complete", max: 10 },
    { label: "Mean recall", key: "mean_recall", max: 1 },
    { label: "Mean precision", key: "mean_precision", max: 1 },
  ] as const;
  return (
    <>
      <div className="comparison-grid">
        {(["flat", "graph"] as const).map((strategy) => (
          <section className={`panel strategy ${strategy}`} key={strategy}>
            <div className="section-title">
              <div className="inline">
                {strategy === "flat" ? (
                  <Layers size={22} />
                ) : (
                  <Network size={22} />
                )}
                <h2>
                  {strategy === "flat" ? "Flat Retrieval" : "Graph Retrieval"}
                </h2>
              </div>
              <Badge tone={strategy === "graph" ? "green" : ""}>
                {strategy === "flat" ? "LEXICAL BASELINE" : "SCHEMA-GUIDED"}
              </Badge>
            </div>
            <p>
              {strategy === "flat"
                ? "Independent source rows · BM25-style search"
                : "Text-to-Cypher · Explicit relationships · Neo4j"}
            </p>
            <div className="strategy-metrics">
              {metrics.map((m) => {
                const val = data.retrieval.summary[strategy][m.key];
                return (
                  <div key={m.key}>
                    <span>{m.label}</span>
                    <strong>
                      {m.max === 10 ? (
                        <>
                          {val}
                          <small>/10</small>
                        </>
                      ) : (
                        val.toFixed(3)
                      )}
                    </strong>
                    <div className="meter">
                      <span style={{ width: `${(val / m.max) * 100}%` }} />
                    </div>
                  </div>
                );
              })}
            </div>
          </section>
        ))}
      </div>
      <div className="comparison-caption">
        <span>
          <span className="status-dot" /> Saved observed run · 10 synthetic
          cases · Model: {data.retrieval.model}
        </span>
        <span>Evidence evaluated before final-answer generation</span>
      </div>
      <section className="panel case-panel">
        <div className="section-title">
          <div>
            <div className="eyebrow">BEHIND THE AVERAGES</div>
            <h2>Explore the evidence, case by case</h2>
          </div>
          <label className="case-select">
            All cases
            <select
              aria-label="Select retrieval case"
              value={selected}
              onChange={(e) => {
                setSelected(e.target.value);
                setShowCypher(false);
              }}
            >
              {data.retrieval.cases.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.id} · {pretty(c.category)}
                </option>
              ))}
            </select>
          </label>
        </div>
        <div className="case-tabs">
          {[
            { id: "RET-001", label: "Direct relationship" },
            { id: "RET-009", label: "Filtering" },
            { id: "RET-007", label: "Cross-source" },
            { id: "RET-005", label: "RET-005 · The boundary" },
          ].map((t) => (
            <button
              className={selected === t.id ? "active" : ""}
              key={t.id}
              onClick={() => {
                setSelected(t.id);
                setShowCypher(false);
              }}
            >
              {t.label}
            </button>
          ))}
        </div>
        <div className="case-content">
          <div className="case-question">
            <span className="small-label">
              {c.id} / {pretty(c.category).toUpperCase()}
            </span>
            <h3>{c.question}</h3>
            <button
              className="text-button"
              onClick={() => setShowCypher(!showCypher)}
            >
              {showCypher ? "Hide" : "Inspect"} observed Cypher{" "}
              <ChevronRight size={15} />
            </button>
            {c.graph.attempts > 1 && (
              <small className="retry-note">
                Recovered after {c.graph.attempts} query-generation attempts.
              </small>
            )}
          </div>
          <div className="case-results">
            {(["flat", "graph"] as const).map((s) => (
              <div key={s}>
                <span>{s === "flat" ? "Flat" : "Graph"}</span>
                <Badge
                  tone={c[s].metrics.evidence_complete ? "green" : "orange"}
                >
                  {c[s].metrics.evidence_complete ? "Complete" : "Incomplete"}
                </Badge>
                <strong>
                  {c[s].metrics.recall.toFixed(3)}
                  <small>recall</small>
                </strong>
                <strong>
                  {c[s].metrics.precision.toFixed(3)}
                  <small>precision</small>
                </strong>
              </div>
            ))}
          </div>
        </div>
        {selected === "RET-005" ? (
          <div className="boundary">
            <div>
              <Badge tone="orange">
                CONTEXT EXISTS. RETRIEVAL STOPS SHORT.
              </Badge>
              <h3>Graph capability ≠ retrieval decision</h3>
              <p>
                The observed query retrieved the execution, test, traces, and
                defect. It did not continue to the requirement or affected
                component.
              </p>
              <button
                className="text-button"
                onClick={() => go("investigation")}
              >
                Explore the full graph context <ArrowUpRight size={15} />
              </button>
            </div>
            <div className="evidence-atoms">
              <span className="small-label">
                EXPECTED EVIDENCE / GRAPH RESULT
              </span>
              {c.graph.metrics.expected_atoms.map((atom) => (
                <span
                  key={atom}
                  className={missing.has(atom) ? "missing" : "found"}
                >
                  {missing.has(atom) ? <X size={12} /> : <Check size={12} />}{" "}
                  {atom.replace(/^id:/, "")}
                </span>
              ))}
              <small>
                Dashed items exist in the graph but were not retrieved.
              </small>
            </div>
          </div>
        ) : (
          <div className="case-evidence">
            <span className="small-label">GRAPH: MATCHED EVIDENCE</span>
            <div>
              {c.graph.metrics.matched_atoms.map((a) => (
                <span className="atom" key={a}>
                  <Check size={12} />
                  {a.replace(/^(id|source_system):/, "")}
                </span>
              ))}
            </div>
            {c.flat.metrics.missing_atoms.length > 0 && (
              <p>
                Flat retrieval missed:{" "}
                {c.flat.metrics.missing_atoms
                  .map((a) => a.replace(/^(id|source_system):/, ""))
                  .join(" · ")}
              </p>
            )}
            {selected === "RET-001" && (
              <p>
                Both strategies found the required relationship. Graph retrieval
                returned more selective evidence.
              </p>
            )}
          </div>
        )}
        {showCypher && (
          <pre className="cypher">
            <code>{c.graph.cypher}</code>
          </pre>
        )}
      </section>
      <div className="takeaway">
        <span className="small-label">OBSERVED, NOT GUARANTEED</span>
        <p>
          A connected graph makes context available. Query generation still
          determines which evidence is retrieved.
        </p>
      </div>
    </>
  );
}

function Agent() {
  const [caseId, setCaseId] = useState("AGT-001");
  const [step, setStep] = useState(5);
  const [running, setRunning] = useState(false);
  const c = data.agent.cases.find((c) => c.id === caseId)!;
  const used = c.response.graph_tool_used;
  const route = used
    ? [
        { label: "Agent", icon: Sparkles },
        { label: "graph_retrieval", icon: Workflow },
        { label: "Neo4j", icon: Database },
        { label: "Evidence", icon: FileCheck2 },
        { label: "Answer", icon: Check },
      ]
    : [
        { label: "Agent", icon: Sparkles },
        { label: "Direct answer", icon: Check },
      ];
  useEffect(() => {
    if (!running) return;
    const timer = window.setTimeout(() => {
      if (step >= route.length) {
        setRunning(false);
        return;
      }
      setStep((s) => s + 1);
    }, 850);
    return () => clearTimeout(timer);
  }, [step, running, route.length]);
  const choose = (id: string) => {
    setCaseId(id);
    setStep(0);
    setRunning(true);
  };
  const done = step >= route.length;
  return (
    <>
      <div className="agent-layout">
        <section className="panel agent-demo">
          <div className="section-title">
            <div>
              <div className="eyebrow">THE DECISION LAYER</div>
              <h2>Does this question need project data?</h2>
            </div>
            <Badge>RECORDED REPLAY</Badge>
          </div>
          <div className="question-picker">
            {data.agent.cases
              .filter((c) => ["AGT-001", "AGT-006"].includes(c.id))
              .map((c) => (
                <button
                  key={c.id}
                  className={caseId === c.id ? "active" : ""}
                  onClick={() => choose(c.id)}
                >
                  <span className="radio-dot" />
                  <span>
                    <small>
                      {c.id === "AGT-001"
                        ? "PROJECT-SPECIFIC QUESTION"
                        : "CONCEPTUAL QUESTION"}
                    </small>
                    {c.question}
                  </span>
                  <ArrowUpRight size={17} />
                </button>
              ))}
          </div>
          <div className="decision">
            <span className="decision-line" />
            <div>
              <Sparkles size={19} />
              <strong>Graph evidence required?</strong>
              <Badge tone={used ? "green" : ""}>{used ? "YES" : "NO"}</Badge>
            </div>
            <span className="decision-line" />
          </div>
          <div className={`agent-route ${!used ? "direct" : ""}`}>
            {route.map((r, i) => (
              <div key={r.label} className={step > i ? "reached" : ""}>
                <span className="route-icon">
                  <r.icon size={23} />
                </span>
                <strong>{r.label}</strong>
                {i < route.length - 1 && (
                  <ArrowRight size={19} className="route-arrow" />
                )}
              </div>
            ))}
          </div>
          <div className="tool-status" aria-live="polite">
            <span>
              <span className={`status-dot ${!used ? "neutral" : ""}`} />
              <code>graph_retrieval</code>{" "}
              <strong>{used ? "USED" : "NOT USED"}</strong>
            </span>
            <span>
              {c.response.graph_tool_calls} tool{" "}
              {c.response.graph_tool_calls === 1 ? "call" : "calls"}{" "}
              <span className="muted">/ maximum 1</span>
            </span>
          </div>
          <div
            className={`agent-answer ${done ? "visible" : ""}`}
            aria-live="polite"
          >
            <div className="small-label">
              <Check size={14} />{" "}
              {used ? "GRAPH-GROUNDED ANSWER" : "DIRECT CONCEPTUAL ANSWER"}{" "}
              <span>CONCISE SAVED OUTPUT</span>
            </div>
            <h3>
              {used
                ? "TEST-006 verifies REQ-006."
                : "Knowledge is connected information."}
            </h3>
            <p>
              {used
                ? c.response.answer.replaceAll("**", "").split("\n\n")[0]
                : c.response.answer
                    .replaceAll("**", "")
                    .split(" It organizes")[0]}
            </p>
            {used && (
              <div className="answer-evidence">
                <span className="atom">TEST-006</span>
                <span className="mono muted">
                  VERIFIES <ArrowRight size={12} />
                </span>
                <span className="atom">REQ-006</span>
              </div>
            )}
          </div>
          <div className="replay-footer">
            <span className="muted">
              Saved agent result · {c.id} · No live model call
            </span>
            <button
              className="secondary"
              onClick={() => {
                setStep(0);
                setRunning(true);
              }}
              disabled={running}
            >
              <RotateCcw size={14} />
              {running ? "Replaying…" : "Replay decision"}
            </button>
          </div>
        </section>
        <aside className="panel agent-benchmark">
          <div className="eyebrow">OBSERVED BENCHMARK</div>
          <span className="score">
            {data.agent.summary.fullyCorrect}
            <span>/{data.agent.summary.cases}</span>
          </span>
          <h2>Fully correct cases</h2>
          <p>
            5 project-data questions.
            <br />3 questions without graph retrieval.
          </p>
          <div className="benchmark-checks">
            {[
              { key: "executed", label: "Execution" },
              { key: "toolSelectionCorrect", label: "Tool selection" },
              { key: "toolCallCountCorrect", label: "Tool call count" },
              { key: "toolExecutionSuccess", label: "Tool execution" },
              { key: "answerValuesComplete", label: "Answer values complete" },
              { key: "noResultHandlingCorrect", label: "No-result handling" },
            ].map((m) => (
              <div key={m.key}>
                <Check size={14} />
                <span>{m.label}</span>
                <strong>
                  {data.agent.summary[m.key as keyof typeof data.agent.summary]}
                  /{data.agent.summary.cases}
                </strong>
              </div>
            ))}
          </div>
          <div className="benchmark-note">
            <ShieldCheck size={18} />
            <p>
              Deterministic checks on eight synthetic cases. Answer-value
              completeness does not validate every generated sentence.
            </p>
          </div>
        </aside>
      </div>
      <div className="takeaway">
        <span className="small-label">A SMALL, DELIBERATE AGENT</span>
        <strong>
          Question <ArrowRight size={18} /> tool decision{" "}
          <ArrowRight size={18} /> existing retrieval pipeline{" "}
          <ArrowRight size={18} /> grounded answer
        </strong>
      </div>
    </>
  );
}

export default App;
