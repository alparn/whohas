"use client";

import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button, buttonVariants } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useUserMemberships } from "@/hooks/use-user-memberships";
import type { MembershipEntry } from "@/lib/api-types";
import { cn } from "@/lib/utils";

interface EffectiveMembershipsListProps {
  directoryId: string;
  userId: string;
  userDn: string;
}

export function EffectiveMembershipsList({
  directoryId,
  userId,
  userDn,
}: EffectiveMembershipsListProps) {
  const { data, isLoading, isError, refetch } = useUserMemberships(
    directoryId,
    userId,
  );

  if (isLoading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-10 w-full rounded-md" />
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base text-destructive">
            Failed to load memberships
          </CardTitle>
          <CardDescription>
            The memberships endpoint may not be available yet.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  if (!data || data.memberships.length === 0) {
    return (
      <p className="py-8 text-center text-sm text-muted-foreground">
        No group memberships found.
      </p>
    );
  }

  const sorted = [...data.memberships].sort((a, b) => a.depth - b.depth);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h3 className="text-lg font-semibold tracking-tight">
            Group memberships
          </h3>
          <Badge variant="secondary" className="text-xs font-normal">
            {data.total} groups ({data.direct_count} direct,{" "}
            {data.inherited_count} inherited)
          </Badge>
        </div>
        <Link
          href={`/directories/${directoryId}/graph?root_dn=${encodeURIComponent(userDn)}`}
          className={buttonVariants({ variant: "ghost", size: "sm" })}
        >
          View in graph
          <ArrowRight className="ml-1 h-3.5 w-3.5" />
        </Link>
      </div>

      <div className="divide-y rounded-md border">
        {sorted.map((membership, i) => (
          <MembershipRow key={`${membership.group_dn}-${i}`} membership={membership} />
        ))}
      </div>
    </div>
  );
}

function MembershipRow({ membership }: { membership: MembershipEntry }) {
  const isDirect = membership.depth === 0;

  return (
    <div
      className={cn(
        "flex items-center gap-3 px-4 py-2.5 text-sm",
        isDirect && "border-l-2 border-l-primary font-medium",
      )}
    >
      <span className="flex-1 truncate">{membership.group_name}</span>
      {isDirect ? (
        <Badge variant="outline" className="text-xs">
          Direct
        </Badge>
      ) : (
        <Badge variant="secondary" className="text-xs font-normal">
          via {membership.depth} group{membership.depth > 1 ? "s" : ""}
        </Badge>
      )}
    </div>
  );
}
