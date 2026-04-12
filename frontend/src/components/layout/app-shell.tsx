"use client";

import type { ReactNode } from "react";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Sidebar } from "./sidebar";
import { Header } from "./header";

interface AppShellProps {
  directoryId: string;
  children: ReactNode;
}

export function AppShell({ directoryId, children }: AppShellProps) {
  return (
    <TooltipProvider delay={200}>
      <div className="flex h-svh">
        <Sidebar />
        <div className="flex flex-1 flex-col overflow-hidden">
          <Header directoryId={directoryId} />
          <main className="flex-1 overflow-y-auto">{children}</main>
        </div>
      </div>
    </TooltipProvider>
  );
}
