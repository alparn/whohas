"use client";

import { CheckCircle2, Loader2, XCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useTestConnection } from "@/hooks/use-directories";
import type { DirectoryCreate } from "@/lib/api-types";

interface ConnectionTestButtonProps {
  getValues: () => DirectoryCreate;
}

export function ConnectionTestButton({ getValues }: ConnectionTestButtonProps) {
  const testConnection = useTestConnection();

  const handleTest = () => {
    testConnection.mutate(getValues());
  };

  return (
    <div className="space-y-2">
      <Button
        type="button"
        variant="outline"
        onClick={handleTest}
        disabled={testConnection.isPending}
      >
        {testConnection.isPending && (
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
        )}
        Test connection
      </Button>

      {testConnection.isSuccess && (
        <div className="flex items-start gap-2 rounded-md border border-green-200 bg-green-50 p-3 text-sm text-green-800 dark:border-green-900 dark:bg-green-950/30 dark:text-green-300">
          <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" />
          <span>{testConnection.data.message}</span>
        </div>
      )}

      {testConnection.isError && (
        <div className="flex items-start gap-2 rounded-md border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive">
          <XCircle className="mt-0.5 h-4 w-4 shrink-0" />
          <span>
            Connection failed. Check your settings and try again.
          </span>
        </div>
      )}
    </div>
  );
}
