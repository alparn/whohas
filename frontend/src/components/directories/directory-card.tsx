"use client";

import Link from "next/link";
import { ChevronRight, Server } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import type { DirectoryRead } from "@/lib/api-types";

function formatRelativeTime(iso: string | null): string {
  if (!iso) return "Never synced";
  const diff = Date.now() - new Date(iso).getTime();
  const minutes = Math.floor(diff / 60_000);
  if (minutes < 1) return "Synced just now";
  if (minutes < 60) return `Synced ${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `Synced ${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `Synced ${days}d ago`;
}

interface DirectoryCardProps {
  directory: DirectoryRead;
}

export function DirectoryCard({ directory }: DirectoryCardProps) {
  return (
    <Link href={`/directories/${directory.id}`}>
      <Card className="group transition-colors hover:bg-accent/50">
        <CardHeader className="flex flex-row items-center gap-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-md bg-muted">
            <Server className="h-5 w-5 text-muted-foreground" />
          </div>
          <div className="flex-1 space-y-1">
            <CardTitle className="text-base">{directory.name}</CardTitle>
            <CardDescription className="text-xs">
              {directory.host}:{directory.port} &middot; {directory.base_dn}
            </CardDescription>
          </div>
          <Badge variant="secondary" className="text-xs font-normal">
            {formatRelativeTime(directory.last_full_sync_at)}
          </Badge>
          <ChevronRight className="h-4 w-4 text-muted-foreground transition-transform group-hover:translate-x-0.5" />
        </CardHeader>
      </Card>
    </Link>
  );
}
