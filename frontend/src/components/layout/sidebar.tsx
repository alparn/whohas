"use client";

import Link from "next/link";
import { useParams, usePathname } from "next/navigation";
import { FolderKey, Plus } from "lucide-react";
import { buttonVariants } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { useDirectories } from "@/hooks/use-directories";

export function Sidebar() {
  const { data: directories, isLoading } = useDirectories();
  const params = useParams();
  const activeId = params.id as string | undefined;

  return (
    <aside className="flex h-full w-60 flex-col border-r bg-muted/30">
      <div className="flex items-center gap-2 border-b px-4 py-3">
        <FolderKey className="h-5 w-5 text-primary" />
        <span className="text-sm font-semibold tracking-tight">whohas</span>
      </div>

      <ScrollArea className="flex-1 px-2 py-2">
        {isLoading ? (
          <div className="space-y-2 px-2">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-8 w-full rounded-md" />
            ))}
          </div>
        ) : directories && directories.length > 0 ? (
          <nav className="space-y-0.5">
            {directories.map((dir) => (
              <Link
                key={dir.id}
                href={`/directories/${dir.id}`}
                className={cn(
                  "flex items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors",
                  "hover:bg-accent hover:text-accent-foreground",
                  activeId === dir.id &&
                    "bg-accent text-accent-foreground font-medium",
                )}
              >
                <span className="truncate">{dir.name}</span>
              </Link>
            ))}
          </nav>
        ) : (
          <div className="px-3 py-8 text-center">
            <p className="text-sm text-muted-foreground">
              No directories yet.
            </p>
            <p className="mt-1 text-xs text-muted-foreground">
              Add your first directory to get started.
            </p>
          </div>
        )}
      </ScrollArea>

      <div className="border-t p-2">
        <Link href="/directories/new" className={buttonVariants({ variant: "ghost", size: "sm", className: "w-full justify-start gap-2" })}>
            <Plus className="h-4 w-4" />
            Add directory
        </Link>
      </div>
    </aside>
  );
}
