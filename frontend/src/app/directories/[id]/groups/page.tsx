"use client";

import { use, useState } from "react";
import Link from "next/link";
import { ArrowLeft, Search } from "lucide-react";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { useGroups } from "@/hooks/use-groups";
import { useSummary } from "@/hooks/use-insights";

export default function GroupsListPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const [search, setSearch] = useState("");
  const { data: groups, isLoading, isError, refetch } = useGroups(id, search);
  const { data: summary } = useSummary(id);

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center gap-4">
        <Link
          href={`/directories/${id}`}
          className={buttonVariants({ variant: "ghost", size: "sm" })}
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Dashboard
        </Link>
        <div>
          <h1 className="text-xl font-semibold tracking-tight">Groups</h1>
          {summary && (
            <p className="text-sm text-muted-foreground">
              {summary.total_groups} groups total
            </p>
          )}
        </div>
      </div>

      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          placeholder="Search groups..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-9"
        />
      </div>

      {isError ? (
        <Card>
          <CardContent className="flex items-center justify-between py-4">
            <p className="text-sm text-destructive">
              Could not load groups.
            </p>
            <button
              onClick={() => refetch()}
              className="text-sm font-medium text-destructive underline underline-offset-4 hover:no-underline"
            >
              Retry
            </button>
          </CardContent>
        </Card>
      ) : isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 10 }, (_, i) => (
            <Skeleton key={i} className="h-16 w-full rounded-lg" />
          ))}
        </div>
      ) : groups && groups.length > 0 ? (
        <div className="space-y-1">
          {groups.map((group) => (
            <Link
              key={group.id}
              href={`/directories/${id}/groups/${group.id}`}
              className="flex items-center justify-between gap-4 rounded-lg border px-4 py-3 transition-colors hover:bg-muted/50"
            >
              <div className="min-w-0">
                <p className="truncate text-sm font-medium">{group.name}</p>
                {group.description && (
                  <p className="truncate text-xs text-muted-foreground">
                    {group.description}
                  </p>
                )}
              </div>
              <p className="shrink-0 text-xs text-muted-foreground">
                {group.group_type || "—"}
              </p>
            </Link>
          ))}
        </div>
      ) : (
        <p className="py-8 text-center text-sm text-muted-foreground">
          {search ? "No groups found" : "No groups synced yet"}
        </p>
      )}
    </div>
  );
}
