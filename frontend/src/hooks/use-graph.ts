"use client";

import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "@/lib/query-keys";
import type { GraphResponse } from "@/lib/graph-types";

const baseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export function useGraphData(
  directoryId: string,
  rootDn: string | null,
  depth: number,
) {
  return useQuery({
    queryKey: queryKeys.graph.view(directoryId, rootDn, depth),
    queryFn: async (): Promise<GraphResponse> => {
      const params = new URLSearchParams();
      if (rootDn) params.set("root_dn", rootDn);
      params.set("depth", String(depth));
      params.set("node_limit", "500");

      const res = await fetch(
        `${baseUrl}/api/directories/${directoryId}/graph?${params}`,
      );
      if (!res.ok) throw new Error(`Graph fetch failed: ${res.status}`);
      return res.json();
    },
    enabled: !!directoryId,
  });
}
