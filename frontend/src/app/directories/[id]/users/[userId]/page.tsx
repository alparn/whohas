"use client";

import { use } from "react";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { Button, buttonVariants } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { UserDetailCard } from "@/components/users/user-detail-card";
import { EffectiveMembershipsList } from "@/components/users/effective-memberships-list";
import { useUser } from "@/hooks/use-users";

export default function UserDetailPage({
  params,
}: {
  params: Promise<{ id: string; userId: string }>;
}) {
  const { id, userId } = use(params);
  const { data: user, isLoading, isError, refetch } = useUser(id, userId);

  if (isLoading) {
    return (
      <div className="p-6 space-y-6">
        <Skeleton className="h-8 w-48" />
        <div className="grid gap-6 lg:grid-cols-[1fr_2fr]">
          <Skeleton className="h-64 w-full" />
          <Skeleton className="h-64 w-full" />
        </div>
      </div>
    );
  }

  if (isError || !user) {
    return (
      <div className="p-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-base text-destructive">
              User not found
            </CardTitle>
            <CardDescription>
              The user may have been removed from the directory.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex gap-2">
            <Button variant="outline" size="sm" onClick={() => refetch()}>
              Retry
            </Button>
            <Link href={`/directories/${id}/users`} className={buttonVariants({ variant: "ghost", size: "sm" })}>
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back to users
            </Link>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <Link href={`/directories/${id}/users`} className={buttonVariants({ variant: "ghost", size: "sm" })}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to users
      </Link>

      <div className="grid gap-8 lg:grid-cols-[300px_1fr]">
        <div className="rounded-lg border p-6">
          <UserDetailCard user={user} />
        </div>

        <div>
          <EffectiveMembershipsList
            directoryId={id}
            userId={userId}
            userDn={user.dn}
          />
        </div>
      </div>
    </div>
  );
}
