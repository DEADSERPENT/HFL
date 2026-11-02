/**
 * Deterministic, schematic layout shared by the 3D scene and the 2D diagram.
 * Node counts are illustrative: they are not patients, hospitals or devices.
 */

export type P3 = { x: number; y: number; z: number };

export type FlowPath = {
  kind: "device-edge" | "edge-cloud";
  from: P3;
  to: P3;
  /** Deterministic phase offset in [0, 1). */
  phase: number;
  edgeIndex: number;
};

export type SceneLayout = {
  edges: P3[];
  devices: (P3 & { edge: number })[];
  cloud: P3;
  paths: FlowPath[];
  deviceRadius: number;
  tierY: { device: number; edge: number; cloud: number };
};

export const TIER_Y = { device: -2.3, edge: 0, cloud: 2.4 } as const;

export function schematicDeviceCount(edges: number): number {
  if (edges <= 2) return 12;
  if (edges <= 8) return 24;
  return 32;
}

const GOLDEN = 0.6180339887;

export function buildLayout(edgeCount: number, opts: { compact?: boolean } = {}): SceneLayout {
  const nDev = opts.compact ? Math.min(12, schematicDeviceCount(edgeCount)) : schematicDeviceCount(edgeCount);
  const deviceRadius = edgeCount <= 2 ? 4.2 : 4.8;
  const edgeRadius = edgeCount <= 2 ? 2.1 : 3.0;
  const perEdge = nDev / edgeCount;

  const devices = Array.from({ length: nDev }, (_, j) => {
    const a = (j / nDev) * Math.PI * 2 + Math.PI / nDev;
    return {
      x: Math.cos(a) * deviceRadius,
      y: TIER_Y.device,
      z: Math.sin(a) * deviceRadius,
      edge: Math.min(edgeCount - 1, Math.floor(j / perEdge)),
    };
  });

  const edges = Array.from({ length: edgeCount }, (_, e) => {
    // Edge sits at the mean angle of the devices it serves.
    const first = e * perEdge;
    const mid = first + (perEdge - 1) / 2;
    const a = (mid / nDev) * Math.PI * 2 + Math.PI / nDev;
    return { x: Math.cos(a) * edgeRadius, y: TIER_Y.edge, z: Math.sin(a) * edgeRadius };
  });

  const cloud = { x: 0, y: TIER_Y.cloud, z: 0 };

  const paths: FlowPath[] = [];
  devices.forEach((d, j) => {
    const to = edges[d.edge]!;
    for (let k = 0; k < 2; k++)
      paths.push({ kind: "device-edge", from: d, to, phase: ((j * 2 + k) * GOLDEN) % 1, edgeIndex: d.edge });
  });
  edges.forEach((e, i) => {
    for (let k = 0; k < 3; k++) paths.push({ kind: "edge-cloud", from: e, to: cloud, phase: ((i * 3 + k) * GOLDEN + 0.37) % 1, edgeIndex: i });
  });

  return { edges, devices, cloud, paths, deviceRadius, tierY: TIER_Y };
}

export function lerp3(a: P3, b: P3, t: number): P3 {
  return { x: a.x + (b.x - a.x) * t, y: a.y + (b.y - a.y) * t, z: a.z + (b.z - a.z) * t };
}

/** Where along a device-edge path the compression step is drawn. */
export const COMPRESSION_AT = 0.38;
