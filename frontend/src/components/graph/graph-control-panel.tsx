"use client";

import { useState, useMemo, useRef, useEffect } from "react";
import { Search } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import type { GraphNodeResponse, GraphMeta } from "@/lib/graph-types";
import { cn } from "@/lib/utils";

interface ControlPanelProps {
  nodes: GraphNodeResponse[];
  meta: GraphMeta;
  depth: number;
  onDepthChange: (depth: number) => void;
  onFocusNode: (nodeId: string) => void;
}

export function GraphControlPanel({
  nodes,
  meta,
  depth,
  onDepthChange,
  onFocusNode,
}: ControlPanelProps) {
  const [search, setSearch] = useState("");
  const [showDropdown, setShowDropdown] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const results = useMemo(() => {
    if (!search.trim()) return [];
    const q = search.toLowerCase();
    return nodes
      .filter((n) => n.label.toLowerCase().includes(q))
      .slice(0, 8);
  }, [nodes, search]);

  useEffect(() => {
    setShowDropdown(results.length > 0 && search.trim().length > 0);
  }, [results, search]);

  return (
    <Card size="sm" className="w-[280px] bg-background/90 backdrop-blur-sm">
      <CardContent className="space-y-3">
        <div className="relative">
          <Search className="absolute left-2 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
          <Input
            ref={inputRef}
            placeholder="Find user or group..."
            className="h-7 pl-7 text-xs"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onBlur={() => setTimeout(() => setShowDropdown(false), 150)}
            onFocus={() => results.length > 0 && setShowDropdown(true)}
          />
          {showDropdown && (
            <div className="absolute left-0 right-0 top-full z-50 mt-1 rounded-md border bg-popover p-1 shadow-md">
              {results.map((n) => (
                <button
                  key={n.id}
                  className={cn(
                    "flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-xs",
                    "hover:bg-accent hover:text-accent-foreground",
                  )}
                  onMouseDown={() => {
                    onFocusNode(n.id);
                    setSearch("");
                    setShowDropdown(false);
                  }}
                >
                  <span
                    className={cn(
                      "h-2 w-2 rounded-full",
                      n.type === "user" ? "bg-blue-500" : "bg-purple-500",
                    )}
                  />
                  <span className="truncate">{n.label}</span>
                  <span className="ml-auto text-muted-foreground">
                    {n.type}
                  </span>
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="flex items-center gap-2">
          <label className="text-xs text-muted-foreground">Depth</label>
          <select
            value={depth}
            onChange={(e) => onDepthChange(Number(e.target.value))}
            className="h-7 rounded-md border bg-transparent px-2 text-xs"
          >
            <option value={1}>1</option>
            <option value={2}>2</option>
            <option value={3}>3</option>
          </select>
        </div>

        <p className="text-[11px] text-muted-foreground">
          {meta.node_count} nodes · {meta.edge_count} edges
        </p>
      </CardContent>
    </Card>
  );
}
