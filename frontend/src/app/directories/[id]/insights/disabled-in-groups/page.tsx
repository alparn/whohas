"use client";

import { use, useMemo, useState } from "react";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { buttonVariants } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { UserSearchInput } from "@/components/users/user-search-input";
import { useDisabledInGroups, useSummary } from "@/hooks/use-insights";

export default function DisabledInGroupsPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const { data: users, isLoading, isError, refetch } = useDisabledInGroups(id, 100);
  const { data: summary } = useSummary(id);
  const [query, setQuery] = useState("");

  const filtered = useMemo(() => {
    if (!users) return [];
    if (!query.trim()) return users;
    const q = query.toLowerCase();
    return users.filter(
      (u) =>
        u.display_name?.toLowerCase().includes(q) ||
        u.sam_account_name?.toLowerCase().includes(q) ||
        u.mail?.toLowerCase().includes(q),
    );
  }, [users, query]);

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
          <h1 className="text-xl font-semibold tracking-tight">Disabled users in groups</h1>
          {summary && (
            <Badge variant="secondary">{summary.disabled_in_groups_count}</Badge>
          )}
        </div>
      </div>

      <p className="text-sm text-muted-foreground max-w-xl">
        Accounts marked as disabled that still have group memberships.
        These should be removed from groups to maintain a clean permission model.
      </p>

      <UserSearchInput value={query} onChange={setQuery} />

      {isError ? (
        <Card>
          <CardContent className="flex items-center justify-between py-4">
            <p className="text-sm text-destructive">Could not load disabled users.</p>
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
          {filtered.map((user) => (
            <Link
              key={user.id}
              href={`/directories/${id}/users/${user.id}`}
              className="flex items-center justify-between gap-4 rounded-lg border px-4 py-3 transition-colors hover:bg-muted/50"
            >
              <div className="min-w-0">
                <p className="truncate text-sm font-medium">{user.display_name}</p>
                <p className="truncate text-xs text-muted-foreground">
                  {user.sam_account_name}
                  {user.mail && ` · ${user.mail}`}
                </p>
              </div>
              <Badge variant="outline" className="shrink-0 text-red-600 border-red-300 dark:text-red-400 dark:border-red-700">
                Disabled
              </Badge>
            </Link>
          ))}
        </div>
      ) : query.trim() ? (
        <p className="py-8 text-center text-sm text-muted-foreground">
          No disabled users match &ldquo;{query}&rdquo;
        </p>
      ) : (
        <p className="py-8 text-center text-sm text-muted-foreground">
          No disabled users in groups — permission model is clean.
        </p>
      )}
    </div>
  );
}
