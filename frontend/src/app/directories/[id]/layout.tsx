"use client";

import { use, type ReactNode } from "react";
import { AppShell } from "@/components/layout/app-shell";

export default function DirectoryLayout({
  children,
  params,
}: {
  children: ReactNode;
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);

  return <AppShell directoryId={id}>{children}</AppShell>;
}
