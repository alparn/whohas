"use client";

import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  type MouseEvent as ReactMouseEvent,
} from "react";
import { useParams, useSearchParams, useRouter } from "next/navigation";
import {
  ReactFlow,
  Background,
  useReactFlow,
  useNodesState,
  useEdgesState,
  ReactFlowProvider,
  type Node,
  type Edge,
  type OnSelectionChangeParams,
} from "@xyflow/react";
import { Loader2, AlertCircle, Monitor } from "lucide-react";

import { useGraphData } from "@/hooks/use-graph";
import { computeRadialLayout } from "@/lib/graph-layout";
import type { GraphNodeResponse } from "@/lib/graph-types";
import { UserNode } from "@/components/graph/nodes/user-node";
import { GroupNode } from "@/components/graph/nodes/group-node";
import { GraphControlPanel } from "@/components/graph/graph-control-panel";
import { GraphLegend } from "@/components/graph/graph-legend";
import { GraphDetailPanel } from "@/components/graph/graph-detail-panel";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

const nodeTypes = {
  user: UserNode,
  group: GroupNode,
};

function GraphPageInner() {
  const params = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();
  const { setCenter, getZoom } = useReactFlow();

  const directoryId = params.id as string;
  const rootDn = searchParams.get("root_dn");
  const depth = Number(searchParams.get("depth") ?? "2");

  const { data, isLoading, isError, refetch } = useGraphData(
    directoryId,
    rootDn,
    depth,
  );

  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null);

  const activeNodeId = selectedNodeId ?? hoveredNodeId;

  const selectedNodeData: GraphNodeResponse | undefined = useMemo(
    () => data?.nodes.find((n) => n.id === selectedNodeId),
    [data, selectedNodeId],
  );

  const connectedEdgeSet = useMemo(() => {
    if (!activeNodeId || !data) return new Set<string>();
    const set = new Set<string>();
    for (const e of data.edges) {
      if (e.source === activeNodeId || e.target === activeNodeId) {
        set.add(e.id);
      }
    }
    return set;
  }, [activeNodeId, data]);

  const connectedNodeSet = useMemo(() => {
    if (!activeNodeId || !data) return new Set<string>();
    const set = new Set<string>([activeNodeId]);
    for (const e of data.edges) {
      if (e.source === activeNodeId) set.add(e.target);
      if (e.target === activeNodeId) set.add(e.source);
    }
    return set;
  }, [activeNodeId, data]);

  const layoutNodes = useMemo(() => {
    if (!data) return [];

    const rawNodes: Node[] = data.nodes.map((n) => ({
      id: n.id,
      type: n.type,
      data: { ...n.data, label: n.label },
      position: { x: 0, y: 0 },
    }));

    return computeRadialLayout({
      nodes: rawNodes,
      edges: data.edges.map((e) => ({
        id: e.id,
        source: e.source,
        target: e.target,
      })),
      rootId: rootDn,
    });
  }, [data, rootDn]);

  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);

  useEffect(() => {
    setNodes(layoutNodes);
  }, [layoutNodes, setNodes]);

  useEffect(() => {
    if (!data) {
      setEdges([]);
      return;
    }
    setEdges(
      data.edges.map((e) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        type: "default",
        style: {
          stroke: "#9ca3af",
          strokeWidth: 1,
          opacity: 1,
          transition: "opacity 120ms, stroke-width 120ms",
        },
        className: "dark:[&>path]:!stroke-zinc-500",
      })),
    );
  }, [data, setEdges]);

  useEffect(() => {
    const hasActive = activeNodeId !== null;

    setNodes((nds) =>
      nds.map((n) => ({
        ...n,
        style: hasActive && !connectedNodeSet.has(n.id) ? { opacity: 0.3 } : undefined,
      })),
    );

    setEdges((eds) =>
      eds.map((e) => {
        const isConnected = connectedEdgeSet.has(e.id);
        return {
          ...e,
          style: {
            stroke: hasActive && isConnected ? "#6b7280" : "#9ca3af",
            strokeWidth: hasActive && isConnected ? 2 : 1,
            opacity: hasActive ? (isConnected ? 1 : 0.15) : 1,
            transition: "opacity 120ms, stroke-width 120ms",
          },
        };
      }),
    );
  }, [activeNodeId, connectedNodeSet, connectedEdgeSet, setNodes, setEdges]);

  const updateUrl = useCallback(
    (updates: { root_dn?: string | null; depth?: number }) => {
      const p = new URLSearchParams(searchParams.toString());
      if (updates.root_dn !== undefined) {
        if (updates.root_dn) p.set("root_dn", updates.root_dn);
        else p.delete("root_dn");
      }
      if (updates.depth !== undefined) p.set("depth", String(updates.depth));
      router.replace(`/directories/${directoryId}/graph?${p.toString()}`);
    },
    [directoryId, router, searchParams],
  );

  const handleSelectionChange = useCallback(
    ({ nodes: selectedNodes }: OnSelectionChangeParams) => {
      if (selectedNodes.length > 0) {
        setSelectedNodeId(selectedNodes[0].id);
      } else {
        setSelectedNodeId(null);
      }
    },
    [],
  );

  const handleNodeMouseEnter = useCallback(
    (_: ReactMouseEvent, node: Node) => setHoveredNodeId(node.id),
    [],
  );

  const handleNodeMouseLeave = useCallback(
    () => setHoveredNodeId(null),
    [],
  );

  const handlePaneClick = useCallback(() => {
    setSelectedNodeId(null);
  }, []);

  const handleFocusNode = useCallback(
    (nodeId: string) => {
      const node = nodes.find((n) => n.id === nodeId);
      if (node) {
        setSelectedNodeId(nodeId);
        setCenter(node.position.x, node.position.y, {
          zoom: getZoom(),
          duration: 400,
        });
      }
    },
    [nodes, setCenter, getZoom],
  );

  const handleCenterOnGroup = useCallback(
    (dn: string) => {
      setSelectedNodeId(null);
      updateUrl({ root_dn: dn });
    },
    [updateUrl],
  );

  const handleDepthChange = useCallback(
    (d: number) => updateUrl({ depth: d }),
    [updateUrl],
  );

  // Mobile guard
  const [isMobile] = useState(
    typeof window !== "undefined" && window.innerWidth < 768,
  );
  if (isMobile) {
    return (
      <div className="flex h-full items-center justify-center p-8">
        <Card className="max-w-sm text-center">
          <CardContent className="space-y-3 py-8">
            <Monitor className="mx-auto h-10 w-10 text-muted-foreground" />
            <p className="text-sm text-muted-foreground">
              The graph view is best on desktop. Resize your window or open this
              on a larger screen.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="flex items-center gap-2 text-muted-foreground">
          <Loader2 className="h-5 w-5 animate-spin" />
          <span className="text-sm">Loading graph...</span>
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex h-full items-center justify-center p-8">
        <Card className="max-w-sm text-center">
          <CardContent className="space-y-3 py-8">
            <AlertCircle className="mx-auto h-10 w-10 text-destructive" />
            <p className="text-sm text-muted-foreground">
              Failed to load graph data.
            </p>
            <Button variant="outline" size="sm" onClick={() => refetch()}>
              Retry
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!data || data.nodes.length === 0) {
    return (
      <div className="flex h-full items-center justify-center p-8">
        <p className="max-w-sm text-center text-sm text-muted-foreground">
          No nodes match this view. Try adjusting the depth or searching for a
          specific user or group.
        </p>
      </div>
    );
  }

  return (
    <div className="relative h-full w-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        onSelectionChange={handleSelectionChange}
        onNodeMouseEnter={handleNodeMouseEnter}
        onNodeMouseLeave={handleNodeMouseLeave}
        onPaneClick={handlePaneClick}
        fitView
        fitViewOptions={{ padding: 0.3 }}
        minZoom={0.1}
        maxZoom={2}
        proOptions={{ hideAttribution: true }}
      >
        <Background gap={40} size={1} />
      </ReactFlow>

      {data.meta.truncated && (
        <div className="absolute left-1/2 top-3 -translate-x-1/2 rounded-md border bg-background/90 px-3 py-1.5 text-xs text-muted-foreground backdrop-blur-sm">
          Showing {data.meta.node_count} nodes (limited). Narrow your search to
          see more.
        </div>
      )}

      {/* Control panel — top left */}
      <div className="absolute left-4 top-4 z-10">
        <GraphControlPanel
          nodes={data.nodes}
          meta={data.meta}
          depth={depth}
          onDepthChange={handleDepthChange}
          onFocusNode={handleFocusNode}
        />
      </div>

      {/* Legend — top right */}
      <div className="absolute right-4 top-4 z-10">
        <GraphLegend />
      </div>

      {/* Detail panel — bottom right */}
      {selectedNodeData && (
        <div className="absolute bottom-4 right-4 z-10">
          <GraphDetailPanel
            node={selectedNodeData}
            directoryId={directoryId}
            onClose={() => setSelectedNodeId(null)}
            onCenterOnGroup={handleCenterOnGroup}
          />
        </div>
      )}
    </div>
  );
}

export default function GraphPage() {
  return (
    <ReactFlowProvider>
      <GraphPageInner />
    </ReactFlowProvider>
  );
}
