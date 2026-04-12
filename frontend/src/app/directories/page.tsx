"use client";

import Link from "next/link";
import { FolderKey, Plus } from "lucide-react";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useDirectories } from "@/hooks/use-directories";
import { DirectoryCard } from "@/components/directories/directory-card";

export default function DirectoriesPage() {
  const { data: directories, isLoading, error } = useDirectories();

  return (
    <div className="mx-auto max-w-3xl px-6 py-12">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Directories</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Manage your AD/LDAP directory connections.
          </p>
        </div>
        <Link href="/directories/new" className={buttonVariants()}>
            <Plus className="mr-2 h-4 w-4" />
            Add directory
        </Link>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-24 w-full rounded-lg" />
          ))}
        </div>
      ) : error ? (
        <Card>
          <CardHeader>
            <CardTitle className="text-destructive">
              Failed to load directories
            </CardTitle>
            <CardDescription>
              Make sure the backend is running at{" "}
              {process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}.
            </CardDescription>
          </CardHeader>
        </Card>
      ) : directories && directories.length > 0 ? (
        <div className="space-y-3">
          {directories.map((dir) => (
            <DirectoryCard key={dir.id} directory={dir} />
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed py-16">
          <FolderKey className="mb-4 h-10 w-10 text-muted-foreground" />
          <h2 className="text-lg font-medium">No directories configured</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Add your first LDAP directory to get started.
          </p>
          <Link href="/directories/new" className={buttonVariants({ className: "mt-6" })}>
              <Plus className="mr-2 h-4 w-4" />
              Add your first directory
          </Link>
        </div>
      )}
    </div>
  );
}
