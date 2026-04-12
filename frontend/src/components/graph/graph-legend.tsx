"use client";

import { Card, CardContent } from "@/components/ui/card";

export function GraphLegend() {
  return (
    <Card size="sm" className="w-[180px] bg-background/90 backdrop-blur-sm">
      <CardContent className="space-y-2.5">
        <div className="flex items-center gap-2">
          <span className="h-3 w-3 rounded-full bg-blue-500 dark:bg-blue-400" />
          <span className="text-xs text-foreground">User</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="h-3 w-3 rounded-sm bg-purple-500 dark:bg-purple-400" />
          <span className="text-xs text-foreground">Group</span>
        </div>
        <p className="text-[11px] text-muted-foreground">
          Click a node to focus. Drag to pan.
        </p>
      </CardContent>
    </Card>
  );
}
