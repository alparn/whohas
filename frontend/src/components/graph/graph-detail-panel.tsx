"use client";

import { X, ArrowRight } from "lucide-react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import type { GraphNodeResponse } from "@/lib/graph-types";
import { cn } from "@/lib/utils";

interface DetailPanelProps {
  node: GraphNodeResponse;
  directoryId: string;
  onClose: () => void;
  onCenterOnGroup: (dn: string) => void;
}

function getInitials(name: string): string {
  return name
    .split(/\s+/)
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase() ?? "")
    .join("");
}

export function GraphDetailPanel({
  node,
  directoryId,
  onClose,
  onCenterOnGroup,
}: DetailPanelProps) {
  return (
    <Card
      size="sm"
      className={cn(
        "w-[320px] bg-background/90 backdrop-blur-sm",
        "animate-in slide-in-from-right-4 fade-in-0 duration-200",
      )}
    >
      <CardHeader className="relative">
        <Button
          variant="ghost"
          size="icon-xs"
          className="absolute right-2 top-2"
          onClick={onClose}
        >
          <X className="h-3.5 w-3.5" />
        </Button>
        <CardTitle className="text-sm">
          {node.type === "user" ? "User" : "Group"}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {node.type === "user" ? (
          <UserDetail node={node} directoryId={directoryId} />
        ) : (
          <GroupDetail node={node} onCenterOnGroup={onCenterOnGroup} />
        )}
      </CardContent>
    </Card>
  );
}

function UserDetail({
  node,
  directoryId,
}: {
  node: GraphNodeResponse;
  directoryId: string;
}) {
  const initials = getInitials(node.label);

  return (
    <>
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-50 text-sm font-medium text-blue-900 dark:bg-blue-950/40 dark:text-blue-100">
          {initials}
        </div>
        <div className="min-w-0">
          <p className="truncate text-sm font-medium">{node.label}</p>
          {node.data.sam_account_name && (
            <p className="truncate text-xs text-muted-foreground">
              @{node.data.sam_account_name}
            </p>
          )}
        </div>
      </div>
      {node.data.mail && (
        <p className="text-xs text-muted-foreground">{node.data.mail}</p>
      )}
      {node.data.disabled && (
        <p className="text-xs text-destructive">Account disabled</p>
      )}
      <Link
        href={`/directories/${directoryId}/users?q=${encodeURIComponent(node.label)}`}
        className="inline-flex items-center gap-1 text-xs text-primary hover:underline"
      >
        View full profile
        <ArrowRight className="h-3 w-3" />
      </Link>
    </>
  );
}

function GroupDetail({
  node,
  onCenterOnGroup,
}: {
  node: GraphNodeResponse;
  onCenterOnGroup: (dn: string) => void;
}) {
  return (
    <>
      <p className="text-sm font-medium">{node.label}</p>
      {node.data.description && (
        <p className="text-xs text-muted-foreground">{node.data.description}</p>
      )}
      {node.data.member_count != null && (
        <p className="text-xs text-muted-foreground">
          {node.data.member_count} direct members
        </p>
      )}
      <Button
        variant="outline"
        size="sm"
        className="w-full"
        onClick={() => onCenterOnGroup(node.id)}
      >
        Center on this group
      </Button>
    </>
  );
}
