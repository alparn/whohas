"use client";

import { use } from "react";
import Link from "next/link";
import { ArrowLeft, Users, Network } from "lucide-react";
import { buttonVariants } from "@/components/ui/button";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useGroup, useGroupMembers } from "@/hooks/use-groups";

function InfoRow({ label, value }: { label: string; value: string | null | undefined }) {
  return (
    <div>
      <p className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
        {label}
      </p>
      <p className="mt-0.5 text-sm break-all">{value || "—"}</p>
    </div>
  );
}

export default function GroupDetailPage({
  params,
}: {
  params: Promise<{ id: string; groupId: string }>;
}) {
  const { id, groupId } = use(params);
  const { data: group, isLoading, isError, refetch } = useGroup(id, groupId);
  const {
    data: members,
    isLoading: membersLoading,
    isError: membersError,
    refetch: refetchMembers,
  } = useGroupMembers(id, groupId);

  if (isLoading) {
    return (
      <div className="p-6 space-y-6">
        <Skeleton className="h-6 w-32" />
        <Skeleton className="h-8 w-64" />
        <div className="grid gap-6 lg:grid-cols-[300px_1fr]">
          <Skeleton className="h-48 w-full" />
          <Skeleton className="h-64 w-full" />
        </div>
      </div>
    );
  }

  if (isError || !group) {
    return (
      <div className="p-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-base text-destructive">
              Group not found
            </CardTitle>
            <CardDescription>
              The group may have been removed from the directory.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex gap-2">
            <Button variant="outline" size="sm" onClick={() => refetch()}>
              Retry
            </Button>
            <Link
              href={`/directories/${id}`}
              className={buttonVariants({ variant: "ghost", size: "sm" })}
            >
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back
            </Link>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <Link
        href={`/directories/${id}`}
        className={buttonVariants({ variant: "ghost", size: "sm" })}
      >
        <ArrowLeft className="mr-2 h-4 w-4" />
        Back to dashboard
      </Link>

      <div className="grid gap-8 lg:grid-cols-[300px_1fr]">
        {/* Sidebar */}
        <div className="space-y-4">
          <Card>
            <CardContent className="pt-6 space-y-4">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400">
                  <Users className="h-5 w-5" />
                </div>
                <div className="min-w-0">
                  <p className="truncate text-base font-semibold">{group.name}</p>
                  {group.description && (
                    <p className="truncate text-xs text-muted-foreground">
                      {group.description}
                    </p>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3 rounded-lg border p-3">
                <div className="text-center">
                  <p className="text-2xl font-medium">{group.effective_member_count}</p>
                  <p className="text-[11px] text-muted-foreground">Effective</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-medium">{group.direct_member_count}</p>
                  <p className="text-[11px] text-muted-foreground">Direct</p>
                </div>
              </div>

              <div className="space-y-3">
                <InfoRow label="DN" value={group.dn} />
                <InfoRow label="Group type" value={group.group_type} />
                <InfoRow
                  label="First seen"
                  value={new Date(group.first_seen_at).toLocaleDateString()}
                />
                <InfoRow
                  label="Last seen"
                  value={new Date(group.last_seen_at).toLocaleDateString()}
                />
              </div>

              <Link
                href={`/directories/${id}/graph?root_dn=${encodeURIComponent(group.dn)}`}
                className={buttonVariants({ variant: "outline", size: "sm", className: "w-full" })}
              >
                <Network className="mr-2 h-4 w-4" />
                View in graph
              </Link>
            </CardContent>
          </Card>
        </div>

        {/* Members List */}
        <Card>
          <CardHeader className="flex-row items-center justify-between">
            <div>
              <CardTitle className="text-base">Members</CardTitle>
              <CardDescription>
                Users in this group (direct and inherited)
              </CardDescription>
            </div>
            {members && (
              <Badge variant="secondary">{members.length}</Badge>
            )}
          </CardHeader>
          <CardContent>
            {membersError ? (
              <div className="py-4 text-center">
                <p className="text-sm text-muted-foreground">
                  Could not load members.
                </p>
                <button
                  onClick={() => refetchMembers()}
                  className="mt-2 text-sm font-medium underline underline-offset-4 hover:no-underline"
                >
                  Retry
                </button>
              </div>
            ) : membersLoading ? (
              <div className="space-y-2">
                {Array.from({ length: 5 }, (_, i) => (
                  <div key={i} className="flex items-center justify-between px-3 py-2">
                    <div className="space-y-1.5">
                      <Skeleton className="h-4 w-36" />
                      <Skeleton className="h-3 w-24" />
                    </div>
                    <Skeleton className="h-5 w-14" />
                  </div>
                ))}
              </div>
            ) : members && members.length > 0 ? (
              <div className="space-y-0.5">
                {members.map((member) => (
                  <div
                    key={member.user_dn}
                    className="flex items-center justify-between gap-4 rounded-md px-3 py-2 transition-colors hover:bg-muted/50"
                  >
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium">
                        {member.display_name}
                      </p>
                      <p className="truncate text-xs text-muted-foreground">
                        {member.sam_account_name}
                        {member.mail && ` · ${member.mail}`}
                      </p>
                    </div>
                    <Badge
                      variant={member.depth === 1 ? "default" : "secondary"}
                      className="shrink-0"
                    >
                      {member.depth === 1 ? "direct" : `depth ${member.depth}`}
                    </Badge>
                  </div>
                ))}
              </div>
            ) : (
              <p className="py-6 text-center text-sm text-muted-foreground">
                No members in this group
              </p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
