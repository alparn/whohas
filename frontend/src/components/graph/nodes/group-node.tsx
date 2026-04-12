"use client";

import { memo } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";
import { cn } from "@/lib/utils";

export interface GroupNodeData {
  label: string;
  member_count?: number;
  description?: string;
  [key: string]: unknown;
}

function GroupNodeComponent({ data, selected }: NodeProps) {
  const nodeData = data as unknown as GroupNodeData;

  return (
    <>
      <Handle type="target" position={Position.Top} className="!invisible" />
      <div className="relative">
        <div
          className={cn(
            "flex h-11 min-w-[120px] max-w-[180px] items-center justify-center rounded-xl px-3",
            "border bg-purple-50 text-purple-900",
            "transition-all duration-150",
            "hover:scale-105 hover:border-purple-400",
            "dark:bg-purple-950/40 dark:text-purple-100 dark:border-purple-800",
            "dark:hover:border-purple-500",
            selected && "ring-2 ring-purple-500 dark:ring-purple-400",
          )}
        >
          <span className="truncate text-[13px] font-medium">
            {nodeData.label}
          </span>
        </div>
        {nodeData.member_count != null && nodeData.member_count > 0 && (
          <span
            className={cn(
              "absolute -right-2 -top-2 flex h-5 min-w-5 items-center justify-center",
              "rounded-full bg-purple-600 px-1 text-[10px] font-medium text-white",
              "dark:bg-purple-500",
            )}
          >
            {nodeData.member_count}
          </span>
        )}
      </div>
      <Handle type="source" position={Position.Bottom} className="!invisible" />
    </>
  );
}

export const GroupNode = memo(GroupNodeComponent);
