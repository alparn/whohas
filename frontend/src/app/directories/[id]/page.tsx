"use client";

import { use } from "react";
import Link from "next/link";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useDirectory } from "@/hooks/use-directories";
import { useSummary, useStaleUsers, useLargestGroups } from "@/hooks/use-insights";
import { cn } from "@/lib/utils";
import type { SummaryResponse, StaleUserResponse, LargestGroupResponse } from "@/lib/api-types";

function timeAgo(dateStr: string | null | undefined): string {
  if (!dateStr) return "Never";
  const diff = Date.now() - new Date(dateStr).getTime();
  const minutes = Math.floor(diff / 60_000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

function daysAgo(dateStr: string | null): string {
  if (!dateStr) return "Never";
  const diff = Date.now() - new Date(dateStr).getTime();
  const days = Math.floor(diff / 86_400_000);
  if (days === 0) return "Today";
  if (days === 1) return "Yesterday";
  return `${days} days ago`;
}

interface StatCardProps {
  label: string;
  value: number | undefined;
  href: string;
  isLoading: boolean;
  accent?: "amber" | "red" | "none";
}

function StatCard({ label, value, href, isLoading, accent = "none" }: StatCardProps) {
  const hasAccent = accent !== "none" && value !== undefined && value > 0;
  return (
    <Link href={href} className="block">
      <Card
        className={cn(
          "relative transition-colors hover:bg-muted/50",
          hasAccent && accent === "amber" && "border-l-2 border-l-amber-500",
          hasAccent && accent === "red" && "border-l-2 border-l-red-500",
        )}
      >
        <CardContent className="pt-4 pb-4">
          <p className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
            {label}
          </p>
          {isLoading ? (
            <Skeleton className="mt-1 h-8 w-16" />
          ) : (
            <p
              className={cn(
                "mt-1 text-[28px] font-medium leading-none",
                hasAccent && accent === "amber" && "text-amber-700 dark:text-amber-400",
                hasAccent && accent === "red" && "text-red-700 dark:text-red-400",
              )}
            >
              {value ?? "—"}
            </p>
          )}
        </CardContent>
      </Card>
    </Link>
  );
}

function StaleUserRow({
  user,
  directoryId,
}: {
  user: StaleUserResponse;
  directoryId: string;
}) {
  return (
    <Link
      href={`/directories/${directoryId}/users/${user.id}`}
      className="flex items-center justify-between gap-4 rounded-md px-3 py-2 transition-colors hover:bg-muted/50"
    >
      <div className="min-w-0">
        <p className="truncate text-sm font-medium">{user.display_name}</p>
        <p className="truncate text-xs text-muted-foreground">{user.sam_account_name}</p>
      </div>
      <p className="shrink-0 text-xs text-muted-foreground">
        {daysAgo(user.last_logon)}
      </p>
    </Link>
  );
}

function LargestGroupRow({
  group,
  directoryId,
}: {
  group: LargestGroupResponse;
  directoryId: string;
}) {
  return (
    <Link
      href={`/directories/${directoryId}/groups/${group.id}`}
      className="flex items-center justify-between gap-4 rounded-md px-3 py-2 transition-colors hover:bg-muted/50"
    >
      <div className="min-w-0">
        <p className="truncate text-sm font-medium">{group.name}</p>
        {group.description && (
          <p className="truncate text-xs text-muted-foreground">{group.description}</p>
        )}
      </div>
      <Badge variant="secondary" className="shrink-0">
        {group.effective_member_count}
      </Badge>
    </Link>
  );
}

function SkeletonRows({ count = 5 }: { count?: number }) {
  return (
    <div className="space-y-2">
      {Array.from({ length: count }, (_, i) => (
        <div key={i} className="flex items-center justify-between px-3 py-2">
          <div className="space-y-1.5">
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-3 w-20" />
          </div>
          <Skeleton className="h-4 w-16" />
        </div>
      ))}
    </div>
  );
}

function ErrorCard({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <Card className="border-destructive/50 bg-destructive/5">
      <CardContent className="flex items-center justify-between py-3">
        <p className="text-sm text-destructive">{message}</p>
        <button
          onClick={onRetry}
          className="text-sm font-medium text-destructive underline underline-offset-4 hover:no-underline"
        >
          Retry
        </button>
      </CardContent>
    </Card>
  );
}

export default function DirectoryOverview({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const { data: directory, isLoading: dirLoading } = useDirectory(id);
  const {
    data: summary,
    isLoading: summaryLoading,
    isError: summaryError,
    refetch: refetchSummary,
  } = useSummary(id);
  const {
    data: staleUsers,
    isLoading: staleLoading,
    isError: staleError,
    refetch: refetchStale,
  } = useStaleUsers(id, 10);
  const {
    data: largestGroups,
    isLoading: groupsLoading,
    isError: groupsError,
    refetch: refetchGroups,
  } = useLargestGroups(id, 10);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        {dirLoading ? (
          <Skeleton className="h-8 w-64" />
        ) : (
          <h1 className="text-2xl font-semibold tracking-tight">{directory?.name}</h1>
        )}
        <p className="mt-1 text-sm text-muted-foreground">
          Last sync: {timeAgo(directory?.last_full_sync_at)}
        </p>
      </div>

      {/* Summary Error */}
      {summaryError && (
        <ErrorCard
          message="Failed to load dashboard summary."
          onRetry={() => refetchSummary()}
        />
      )}

      {/* Stat Cards */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
        <StatCard
          label="Users"
          value={summary?.total_users}
          href={`/directories/${id}/users`}
          isLoading={summaryLoading}
        />
        <StatCard
          label="Groups"
          value={summary?.total_groups}
          href={`/directories/${id}/groups`}
          isLoading={summaryLoading}
        />
        <StatCard
          label="Stale accounts"
          value={summary?.stale_user_count}
          href={`/directories/${id}/insights/stale-users`}
          isLoading={summaryLoading}
          accent="amber"
        />
        <StatCard
          label="Empty groups"
          value={summary?.empty_group_count}
          href={`/directories/${id}/insights/empty-groups`}
          isLoading={summaryLoading}
          accent="amber"
        />
        <StatCard
          label="Disabled in groups"
          value={summary?.disabled_in_groups_count}
          href={`/directories/${id}/insights/disabled-in-groups`}
          isLoading={summaryLoading}
          accent="red"
        />
      </div>

      {/* Two Column Lists */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Stale Accounts */}
        <Card>
          <CardHeader className="flex-row items-center justify-between">
            <CardTitle className="text-base">Stale accounts</CardTitle>
            {summary && (
              <Badge variant="secondary">{summary.stale_user_count}</Badge>
            )}
          </CardHeader>
          <CardContent>
            {staleError ? (
              <div className="py-4 text-center">
                <p className="text-sm text-muted-foreground">Could not load this list.</p>
                <button
                  onClick={() => refetchStale()}
                  className="mt-2 text-sm font-medium underline underline-offset-4 hover:no-underline"
                >
                  Retry
                </button>
              </div>
            ) : staleLoading ? (
              <SkeletonRows />
            ) : staleUsers && staleUsers.length > 0 ? (
              <div className="space-y-0.5">
                {staleUsers.map((user) => (
                  <StaleUserRow key={user.id} user={user} directoryId={id} />
                ))}
              </div>
            ) : (
              <p className="py-6 text-center text-sm text-muted-foreground">
                No stale accounts found
              </p>
            )}
          </CardContent>
          <CardFooter>
            <Link
              href={`/directories/${id}/insights/stale-users`}
              className="text-sm font-medium text-muted-foreground hover:text-foreground"
            >
              View all stale accounts →
            </Link>
          </CardFooter>
        </Card>

        {/* Largest Groups */}
        <Card>
          <CardHeader className="flex-row items-center justify-between">
            <CardTitle className="text-base">Largest groups</CardTitle>
            {summary && (
              <Badge variant="secondary">{summary.total_groups}</Badge>
            )}
          </CardHeader>
          <CardContent>
            {groupsError ? (
              <div className="py-4 text-center">
                <p className="text-sm text-muted-foreground">Could not load this list.</p>
                <button
                  onClick={() => refetchGroups()}
                  className="mt-2 text-sm font-medium underline underline-offset-4 hover:no-underline"
                >
                  Retry
                </button>
              </div>
            ) : groupsLoading ? (
              <SkeletonRows />
            ) : largestGroups && largestGroups.length > 0 ? (
              <div className="space-y-0.5">
                {largestGroups.map((group) => (
                  <LargestGroupRow key={group.id} group={group} directoryId={id} />
                ))}
              </div>
            ) : (
              <p className="py-6 text-center text-sm text-muted-foreground">
                No groups found
              </p>
            )}
          </CardContent>
          <CardFooter>
            <Link
              href={`/directories/${id}/groups`}
              className="text-sm font-medium text-muted-foreground hover:text-foreground"
            >
              View all groups →
            </Link>
          </CardFooter>
        </Card>
      </div>
    </div>
  );
}
