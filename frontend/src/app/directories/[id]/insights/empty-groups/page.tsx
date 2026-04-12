"use client";

import { use, useMemo, useState } from "react";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { buttonVariants } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { UserSearchInput } from "@/components/users/user-search-input";
import { useEmptyGroups, useSummary } from "@/hooks/use-insights";

export default function EmptyGroupsPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const { data: groups, isLoading, isError, refetch } = useEmptyGroups(id, 100);
  const { data: summary } = useSummary(id);
  const [query, setQuery] = useState("");

  const filtered = useMemo(() => {
    if (!groups) return [];
    if (!query.trim()) return groups;
    const q = query.toLowerCase();
    return groups.filter(
      (g) =>
        g.name?.toLowerCase().includes(q) ||
        g.description?.toLowerCase().includes(q),
    );
  }, [groups, query]);

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
        <div className="flex items-center gap-3">
          <h1 className="text-xl font-semibold tracking-tight">Empty groups</h1>
          {summary && (
            <Badge variant="secondary">{summary.empty_group_count}</Badge>
          )}
        </div>
      </div>

      <p className="text-sm text-muted-foreground max-w-xl">
        Groups with no effective members. These may be remnants of old projects
        or teams and could be candidates for cleanup.
      </p>

      <UserSearchInput
        value={query}
        onChange={setQuery}
        placeholder="Search by group name or description…"
      />

      {isError ? (
        <Card>
          <CardContent className="flex items-center justify-between py-4">
            <p className="text-sm text-destructive">Could not load empty groups.</p>
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
            <Skeleton key={i} className="h-14 w-full rounded-lg" />
          ))}
        </div>
      ) : filtered.length > 0 ? (
        <div className="space-y-1">
          {filtered.map((group) => (
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
              <Badge variant="outline" className="shrink-0 text-amber-600 border-amber-300 dark:text-amber-400 dark:border-amber-700">
                0 members
              </Badge>
            </Link>
          ))}
        </div>
      ) : query.trim() ? (
        <p className="py-8 text-center text-sm text-muted-foreground">
          No empty groups match &ldquo;{query}&rdquo;
        </p>
      ) : (
        <p className="py-8 text-center text-sm text-muted-foreground">
          No empty groups — all groups have at least one member.
        </p>
      )}
    </div>
  );
}
