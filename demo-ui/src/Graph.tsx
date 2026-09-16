import { useMemo } from "react";
import {
  Background,
  Controls,
  Handle,
  MarkerType,
  Position,
  ReactFlow,
} from "@xyflow/react";
import type { Node, NodeProps } from "@xyflow/react";
import {
  Activity,
  Box,
  Bug,
  FileCheck2,
  FileText,
  Layers,
  Radio,
} from "lucide-react";
import { colors, data, entities, pretty, title } from "./model";
import type { Entity } from "./model";

export const nodeIcons = {
  Feature: Radio,
  Requirement: FileCheck2,
  SoftwareComponent: Box,
  Test: FileText,
  TestExecution: Activity,
  TestTrace: Layers,
  DefectTicket: Bug,
};
type EvidenceNode = Node<
  {
    entity: Entity;
    active: boolean;
    dim: boolean;
    choose: (id: string) => void;
  },
  "evidence"
>;
function Evidence({ data: d }: NodeProps<EvidenceNode>) {
  const Icon = nodeIcons[d.entity.label as keyof typeof nodeIcons];
  return (
    <div
      className={`evidence-node ${d.active ? "active" : ""} ${d.dim ? "dim" : ""}`}
      style={{ "--node-color": colors[d.entity.label] } as React.CSSProperties}
    >
      {[Position.Left, Position.Right, Position.Top, Position.Bottom].map(
        (p) => (
          <Handle key={p} id={p} type="source" position={p} />
        ),
      )}
      {[Position.Left, Position.Right, Position.Top, Position.Bottom].map(
        (p) => (
          <Handle key={`in-${p}`} id={`in-${p}`} type="target" position={p} />
        ),
      )}
      <button
        className="nodrag nopan"
        onClick={() => d.choose(d.entity.id)}
        aria-label={`Inspect ${d.entity.id}`}
        disabled={d.dim}
      >
        <span className="node-type">
          <Icon size={13} />
          {pretty(d.entity.label)}
        </span>
        <strong>{d.entity.id}</strong>
        <span className="node-subtitle">{title(d.entity)}</span>
      </button>
    </div>
  );
}
const nodeTypes = { evidence: Evidence };
const positions: Record<string, { x: number; y: number }> = {
  "EXEC-010": { x: 10, y: 216 },
  "TEST-002": { x: 300, y: 10 },
  "REQ-002": { x: 590, y: 10 },
  "TRACE-006": { x: 300, y: 155 },
  "TRACE-007": { x: 300, y: 280 },
  "TRACE-008": { x: 300, y: 405 },
  "DEF-001": { x: 10, y: 550 },
  "COMP-002": { x: 590, y: 550 },
};
const routes: Record<string, [Position, Position]> = {
  EXECUTION_OF: [Position.Top, Position.Left],
  VERIFIES: [Position.Right, Position.Left],
  PRODUCES: [Position.Right, Position.Left],
  HAS_DEFECT_TICKET: [Position.Bottom, Position.Top],
  AFFECTS: [Position.Right, Position.Left],
  IMPLEMENTS: [Position.Top, Position.Bottom],
};
export function InvestigationGraph({
  selected = "",
  onSelect,
  revealed,
  compact = false,
  missing = [],
}: {
  selected?: string;
  onSelect: (id: string) => void;
  revealed?: string[];
  compact?: boolean;
  missing?: string[];
}) {
  const nodes = useMemo(
    () =>
      entities
        .filter((n) => data.investigationIds.includes(n.id))
        .map((n) => ({
          id: n.id,
          position: positions[n.id] ?? { x: 0, y: 0 },
          type: "evidence",
          data: {
            entity: n,
            active: selected === n.id,
            dim: Boolean(
              (revealed && !revealed.includes(n.id)) || missing.includes(n.id),
            ),
            choose: onSelect,
          },
          draggable: false,
        })),
    [selected, onSelect, revealed, missing],
  );
  const edges = data.edges
    .filter(
      (e) =>
        data.investigationIds.includes(e.source) &&
        data.investigationIds.includes(e.target),
    )
    .map((e) => {
      const dim = Boolean(
        (revealed &&
          (!revealed.includes(e.source) || !revealed.includes(e.target))) ||
          missing.includes(e.source) ||
          missing.includes(e.target),
      );
      const [from, to] = routes[e.label] || [Position.Right, Position.Left];
      return {
        ...e,
        type: "smoothstep",
        sourceHandle: from,
        targetHandle: `in-${to}`,
        label: compact ? undefined : e.label,
        animated: selected === e.source && !dim,
        style: {
          stroke: dim ? "#384252" : "#61736e",
          strokeWidth: 1.3,
          opacity: dim ? 0.25 : 1,
        },
        labelStyle: { fill: "#c2cfcf", fontSize: 12, fontFamily: "monospace" },
        labelBgStyle: { fill: "#141b24", fillOpacity: 0.98 },
        labelBgPadding: [5, 5] as [number, number],
        labelBgBorderRadius: 4,
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: "#708879",
          width: 15,
          height: 15,
        },
      };
    });
  return (
    <div
      className={`graph-canvas ${compact ? "compact" : ""}`}
      aria-label="EXEC-010 evidence graph"
    >
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        onNodeClick={(_, node) => {
          if (!node.data.dim) onSelect(node.id);
        }}
        fitView
        fitViewOptions={{ padding: compact ? 0.08 : 0.1 }}
        minZoom={0.25}
        maxZoom={1.8}
        nodesConnectable={false}
        nodesDraggable={false}
        elementsSelectable={false}
        deleteKeyCode={null}
        colorMode="dark"
        preventScrolling={!compact}
        panOnDrag={!compact}
        zoomOnScroll={!compact}
        zoomOnDoubleClick={false}
      >
        <Background color="#3b4556" gap={23} size={1} />
        {!compact && <Controls showInteractive={false} />}
      </ReactFlow>
    </div>
  );
}
