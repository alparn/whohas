"use client";

import { Moon, RefreshCw, Sun } from "lucide-react";
import { useTheme } from "next-themes";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { useDirectory, useTriggerSync } from "@/hooks/use-directories";
import { cn } from "@/lib/utils";
import { toast } from "sonner";

function formatRelativeTime(iso: string | null): string {
  if (!iso) return "Never";
  const diff = Date.now() - new Date(iso).getTime();
  const minutes = Math.floor(diff / 60_000);
  if (minutes < 1) return "Just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

interface HeaderProps {
  directoryId: string;
}

export function Header({ directoryId }: HeaderProps) {
  const { data: directory, isLoading } = useDirectory(directoryId);
  const { setTheme, resolvedTheme } = useTheme();
  const triggerSync = useTriggerSync(directoryId);

  const handleSync = () => {
    triggerSync.mutate(undefined, {
      onSuccess: () => toast.success("Sync started"),
      onError: () => toast.error("Failed to trigger sync"),
    });
  };

  return (
    <header className="flex h-14 items-center justify-between border-b px-6">
      <div className="flex items-center gap-3">
        {isLoading ? (
          <Skeleton className="h-6 w-40" />
        ) : (
          <h1 className="text-lg font-semibold tracking-tight">
            {directory?.name}
          </h1>
        )}
      </div>

      <div className="flex items-center gap-2">
        {directory && (
          <Tooltip>
            <TooltipTrigger>
              <Badge variant="secondary" className="text-xs font-normal">
                Synced {formatRelativeTime(directory.last_full_sync_at)}
              </Badge>
            </TooltipTrigger>
            <TooltipContent>
              {directory.last_full_sync_at
                ? new Date(directory.last_full_sync_at).toLocaleString()
                : "No sync has been performed yet"}
            </TooltipContent>
          </Tooltip>
        )}

        <Tooltip>
          <TooltipTrigger>
            <Button
              variant="ghost"
              size="icon"
              onClick={handleSync}
              disabled={triggerSync.isPending}
            >
              <RefreshCw
                className={cn("h-4 w-4", triggerSync.isPending && "animate-spin")}
              />
            </Button>
          </TooltipTrigger>
          <TooltipContent>Sync now</TooltipContent>
        </Tooltip>

        <Tooltip>
          <TooltipTrigger>
            <Button
              variant="ghost"
              size="icon"
              onClick={() =>
                setTheme(resolvedTheme === "dark" ? "light" : "dark")
              }
            >
              <Sun className="h-4 w-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
              <Moon className="absolute h-4 w-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
            </Button>
          </TooltipTrigger>
          <TooltipContent>Toggle theme</TooltipContent>
        </Tooltip>
      </div>
    </header>
  );
}
