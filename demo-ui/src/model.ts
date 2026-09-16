import snapshot from "./data/demo.json";
export type Entity = {
  id: string;
  label: string;
  properties: Record<string, string>;
  file: string;
};
export const data = snapshot;
export const entities: Entity[] = snapshot.nodes.map((node) => ({
  ...node,
  properties: Object.fromEntries(
    Object.entries(node.properties).filter(
      ([, value]) => typeof value === "string",
    ),
  ),
}));
export const entity = (id: string) => {
  const found = entities.find((n) => n.id === id);
  if (!found) throw new Error(`Missing entity: ${id}`);
  return found;
};
export const colors: Record<string, string> = {
  Feature: "#bce98c",
  Requirement: "#b4a0ed",
  SoftwareComponent: "#80c8ec",
  Test: "#8eaaf1",
  TestExecution: "#bcea8a",
  TestTrace: "#7fc9be",
  DefectTicket: "#efaa86",
};
export const pretty = (value: string) =>
  value.replace(/([a-z])([A-Z])/g, "$1 $2").replaceAll("_", " ");
export const title = (node: Entity) =>
  node.properties.title ||
  node.properties.name ||
  node.properties.message ||
  `${node.properties.environment} · ${node.properties.result}`;
