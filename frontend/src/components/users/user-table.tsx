"use client";

import { useRouter } from "next/navigation";
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
  type SortingState,
} from "@tanstack/react-table";
import { useState } from "react";
import { ArrowUpDown } from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import type { UserRead } from "@/lib/api-types";

function getInitials(name: string): string {
  return name
    .split(/\s+/)
    .slice(0, 2)
    .map((w) => w[0])
    .join("")
    .toUpperCase();
}

function formatRelativeTime(iso: string | null): string {
  if (!iso) return "—";
  const diff = Date.now() - new Date(iso).getTime();
  const minutes = Math.floor(diff / 60_000);
  if (minutes < 1) return "Just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

const columnHelper = createColumnHelper<UserRead>();

const columns = [
  columnHelper.accessor("display_name", {
    header: "Name",
    cell: (info) => (
      <div className="flex items-center gap-3">
        <Avatar className="h-8 w-8 text-xs">
          <AvatarFallback>{getInitials(info.getValue())}</AvatarFallback>
        </Avatar>
        <span className="font-medium">{info.getValue()}</span>
      </div>
    ),
  }),
  columnHelper.accessor("sam_account_name", {
    header: "Username",
    cell: (info) => (
      <code className="text-xs text-muted-foreground font-mono">
        {info.getValue()}
      </code>
    ),
  }),
  columnHelper.accessor("mail", {
    header: "Email",
    cell: (info) => (
      <span className="text-sm text-muted-foreground">
        {info.getValue() ?? "—"}
      </span>
    ),
  }),
  columnHelper.accessor("account_disabled", {
    header: "Status",
    cell: (info) =>
      info.getValue() ? (
        <Badge variant="secondary" className="text-xs">
          Disabled
        </Badge>
      ) : (
        <Badge className="bg-emerald-100 text-emerald-800 hover:bg-emerald-100 dark:bg-emerald-950 dark:text-emerald-300 text-xs">
          Active
        </Badge>
      ),
  }),
  columnHelper.accessor("last_logon", {
    header: "Last logon",
    cell: (info) => {
      const val = info.getValue();
      return (
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger>
              <span className="text-sm text-muted-foreground cursor-default">
                {formatRelativeTime(val)}
              </span>
            </TooltipTrigger>
            <TooltipContent>
              {val ? new Date(val).toLocaleString() : "Never"}
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      );
    },
  }),
];

interface UserTableProps {
  directoryId: string;
  data: UserRead[];
  isLoading: boolean;
}

export function UserTable({ directoryId, data, isLoading }: UserTableProps) {
  const router = useRouter();
  const [sorting, setSorting] = useState<SortingState>([]);

  const table = useReactTable({
    data,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  if (isLoading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 8 }).map((_, i) => (
          <Skeleton key={i} className="h-12 w-full rounded-md" />
        ))}
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <p className="text-sm text-muted-foreground">
          No users match that search.
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          {table.getHeaderGroups().map((headerGroup) => (
            <TableRow key={headerGroup.id}>
              {headerGroup.headers.map((header) => (
                <TableHead
                  key={header.id}
                  className="cursor-pointer select-none"
                  onClick={header.column.getToggleSortingHandler()}
                >
                  <div className="flex items-center gap-1">
                    {flexRender(
                      header.column.columnDef.header,
                      header.getContext(),
                    )}
                    <ArrowUpDown className="h-3 w-3 text-muted-foreground" />
                  </div>
                </TableHead>
              ))}
            </TableRow>
          ))}
        </TableHeader>
        <TableBody>
          {table.getRowModel().rows.map((row) => (
            <TableRow
              key={row.id}
              className="cursor-pointer"
              onClick={() =>
                router.push(
                  `/directories/${directoryId}/users/${row.original.id}`,
                )
              }
            >
              {row.getVisibleCells().map((cell) => (
                <TableCell key={cell.id}>
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
