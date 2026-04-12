"use client";

import { use, useEffect, useState } from "react";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { UserSearchInput } from "@/components/users/user-search-input";
import { UserTable } from "@/components/users/user-table";
import { useUsers } from "@/hooks/use-users";

export default function UsersPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const [inputValue, setInputValue] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(inputValue), 250);
    return () => clearTimeout(timer);
  }, [inputValue]);

  const { data: users = [], isLoading, isError, refetch } = useUsers(id, debouncedQuery);

  return (
    <div className="p-6 space-y-4">
      <div>
        <h2 className="text-xl font-semibold tracking-tight">Users</h2>
        <p className="text-sm text-muted-foreground mt-1">
          Search and explore cached directory users.
        </p>
      </div>

      <UserSearchInput value={inputValue} onChange={setInputValue} />

      {isError ? (
        <Card>
          <CardHeader>
            <CardTitle className="text-base text-destructive">
              Failed to load users
            </CardTitle>
            <CardDescription>
              Something went wrong while searching.
            </CardDescription>
          </CardHeader>
          <div className="px-6 pb-6">
            <Button variant="outline" size="sm" onClick={() => refetch()}>
              Retry
            </Button>
          </div>
        </Card>
      ) : (
        <UserTable directoryId={id} data={users} isLoading={isLoading} />
      )}
    </div>
  );
}
