"use client";

import { memo } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";
import { cn } from "@/lib/utils";

export interface UserNodeData {
  label: string;
  sam_account_name?: string;
  mail?: string;
  disabled?: boolean;
  [key: string]: unknown;
}

function getInitials(name: string): string {
  return name
    .split(/\s+/)
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase() ?? "")
    .join("");
}

function UserNodeComponent({ data, selected }: NodeProps) {
  const nodeData = data as unknown as UserNodeData;
  const initials = getInitials(nodeData.label);

  return (
    <>
      <Handle type="target" position={Position.Top} className="!invisible" />
      <div className="flex flex-col items-center gap-1.5">
        <div
          className={cn(
            "flex h-12 w-12 items-center justify-center rounded-full",
            "border bg-blue-50 text-blue-900",
            "transition-all duration-150",
            "hover:scale-105 hover:border-blue-400",
            "dark:bg-blue-950/40 dark:text-blue-100 dark:border-blue-800",
            "dark:hover:border-blue-500",
            selected && "ring-2 ring-blue-500 dark:ring-blue-400",
            nodeData.disabled && "opacity-50",
          )}
        >
          <span className="text-sm font-medium select-none">{initials}</span>
        </div>
        <span className="max-w-[100px] truncate text-xs text-foreground">
          {nodeData.label}
        </span>
      </div>
      <Handle type="source" position={Position.Bottom} className="!invisible" />
    </>
  );
}

export const UserNode = memo(UserNodeComponent);
