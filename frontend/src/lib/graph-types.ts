export interface GraphNodeData {
  sam_account_name?: string | null;
  mail?: string | null;
  disabled?: boolean | null;
  member_count?: number | null;
  description?: string | null;
}

export interface GraphNodeResponse {
  id: string;
  type: "user" | "group";
  label: string;
  data: GraphNodeData;
}

export interface GraphEdgeResponse {
  id: string;
  source: string;
  target: string;
  type: string;
}

export interface GraphMeta {
  node_count: number;
  edge_count: number;
  truncated: boolean;
}

export interface GraphResponse {
  nodes: GraphNodeResponse[];
  edges: GraphEdgeResponse[];
  meta: GraphMeta;
}
