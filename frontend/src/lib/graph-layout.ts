import type { Node, Edge } from "@xyflow/react";

const RADIUS_STEP = 200;

interface LayoutInput {
  nodes: Node[];
  edges: Edge[];
  rootId: string | null;
}

/**
 * Compute a radial layout around a root node.
 * - Root sits at (0, 0)
 * - Direct neighbors in a circle at radius 200
 * - 2nd-level at 400, 3rd at 600, etc.
 * - Nodes are evenly distributed per ring
 *
 * If no rootId is provided, returns nodes with random positions
 * as a sensible fallback (user will search/click to focus).
 */
export function computeRadialLayout({ nodes, edges, rootId }: LayoutInput): Node[] {
  if (!rootId || !nodes.find((n) => n.id === rootId)) {
    return spreadRandom(nodes);
  }

  const adjacency = buildAdjacency(edges);
  const visited = new Set<string>();
  const positions = new Map<string, { x: number; y: number }>();

  // BFS from root
  const queue: { id: string; depth: number }[] = [{ id: rootId, depth: 0 }];
  const rings: Map<number, string[]> = new Map();
  visited.add(rootId);

  while (queue.length > 0) {
    const { id, depth } = queue.shift()!;
    if (!rings.has(depth)) rings.set(depth, []);
    rings.get(depth)!.push(id);

    for (const neighbor of adjacency.get(id) ?? []) {
      if (!visited.has(neighbor)) {
        visited.add(neighbor);
        queue.push({ id: neighbor, depth: depth + 1 });
      }
    }
  }

  // Place root at center
  positions.set(rootId, { x: 0, y: 0 });

  // Place each ring
  for (const [depth, ids] of rings) {
    if (depth === 0) continue;
    const radius = depth * RADIUS_STEP;
    const angleStep = (2 * Math.PI) / ids.length;
    const offset = depth % 2 === 0 ? 0 : angleStep / 2;

    ids.forEach((id, i) => {
      const angle = offset + i * angleStep;
      positions.set(id, {
        x: Math.cos(angle) * radius,
        y: Math.sin(angle) * radius,
      });
    });
  }

  // Nodes not connected to root get placed outside
  const unplaced = nodes.filter((n) => !positions.has(n.id));
  if (unplaced.length > 0) {
    const outerRadius = (rings.size + 1) * RADIUS_STEP;
    const step = (2 * Math.PI) / unplaced.length;
    unplaced.forEach((n, i) => {
      positions.set(n.id, {
        x: Math.cos(i * step) * outerRadius,
        y: Math.sin(i * step) * outerRadius,
      });
    });
  }

  return nodes.map((node) => ({
    ...node,
    position: positions.get(node.id) ?? { x: 0, y: 0 },
  }));
}

function buildAdjacency(edges: Edge[]): Map<string, string[]> {
  const adj = new Map<string, string[]>();
  for (const e of edges) {
    if (!adj.has(e.source)) adj.set(e.source, []);
    if (!adj.has(e.target)) adj.set(e.target, []);
    adj.get(e.source)!.push(e.target);
    adj.get(e.target)!.push(e.source);
  }
  return adj;
}

function spreadRandom(nodes: Node[]): Node[] {
  const cols = Math.ceil(Math.sqrt(nodes.length));
  return nodes.map((node, i) => ({
    ...node,
    position: {
      x: (i % cols) * 200 + (Math.random() - 0.5) * 60,
      y: Math.floor(i / cols) * 200 + (Math.random() - 0.5) * 60,
    },
  }));
}
