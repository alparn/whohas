"use client";

import { Check, Copy } from "lucide-react";
import { useState } from "react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import type { UserRead } from "@/lib/api-types";

function getInitials(name: string): string {
  return name
    .split(/\s+/)
    .slice(0, 2)
    .map((w) => w[0])
    .join("")
    .toUpperCase();
}

interface UserDetailCardProps {
  user: UserRead;
}

export function UserDetailCard({ user }: UserDetailCardProps) {
  const [copied, setCopied] = useState(false);

  const copyDn = () => {
    navigator.clipboard.writeText(user.dn);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col items-center text-center sm:items-start sm:text-left">
        <Avatar className="h-16 w-16 text-xl mb-3">
          <AvatarFallback>{getInitials(user.display_name)}</AvatarFallback>
        </Avatar>
        <h1 className="text-2xl font-semibold tracking-tight">
          {user.display_name}
        </h1>
        <p className="mt-1 text-sm text-muted-foreground font-mono">
          {user.sam_account_name}
        </p>
        {user.mail && (
          <p className="text-sm text-muted-foreground">{user.mail}</p>
        )}
        <div className="mt-2">
          {user.account_disabled ? (
            <Badge variant="secondary">Disabled</Badge>
          ) : (
            <Badge className="bg-emerald-100 text-emerald-800 hover:bg-emerald-100 dark:bg-emerald-950 dark:text-emerald-300">
              Active
            </Badge>
          )}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 text-sm">
        <div>
          <span className="text-xs text-muted-foreground">Last logon</span>
          <p className="font-medium">
            {user.last_logon
              ? new Date(user.last_logon).toLocaleDateString()
              : "—"}
          </p>
        </div>
        <div>
          <span className="text-xs text-muted-foreground">First seen</span>
          <p className="font-medium">
            {new Date(user.first_seen_at).toLocaleDateString()}
          </p>
        </div>
        <div>
          <span className="text-xs text-muted-foreground">Last seen</span>
          <p className="font-medium">
            {new Date(user.last_seen_at).toLocaleDateString()}
          </p>
        </div>
      </div>

      <div className="space-y-1">
        <span className="text-xs text-muted-foreground">Distinguished Name</span>
        <div className="flex items-start gap-2">
          <code className="flex-1 break-all rounded-md bg-muted p-2 text-xs font-mono">
            {user.dn}
          </code>
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger>
                <Button variant="ghost" size="icon" className="h-8 w-8 shrink-0" onClick={copyDn}>
                  {copied ? (
                    <Check className="h-3.5 w-3.5 text-emerald-600" />
                  ) : (
                    <Copy className="h-3.5 w-3.5" />
                  )}
                </Button>
              </TooltipTrigger>
              <TooltipContent>{copied ? "Copied!" : "Copy DN"}</TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
      </div>
    </div>
  );
}
