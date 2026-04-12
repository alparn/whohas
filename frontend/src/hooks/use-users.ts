"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { queryKeys } from "@/lib/query-keys";
import type { UserRead } from "@/lib/api-types";

export function useUsers(directoryId: string, q: string) {
  return useQuery({
    queryKey: queryKeys.users.search(directoryId, q),
    queryFn: async () => {
      const { data, error } = await api.GET(
        "/api/directories/{directory_id}/users",
        {
          params: {
            path: { directory_id: directoryId },
            query: { q, limit: 50 },
          },
        },
      );
      if (error) throw new Error("Failed to search users");
      return data as UserRead[];
    },
    enabled: !!directoryId,
  });
}

export function useUser(directoryId: string, userId: string) {
  return useQuery({
    queryKey: queryKeys.users.detail(directoryId, userId),
    queryFn: async () => {
      const { data, error } = await api.GET(
        "/api/directories/{directory_id}/users/{user_id}",
        {
          params: {
            path: { directory_id: directoryId, user_id: userId },
          },
        },
      );
      if (error) throw new Error("User not found");
      return data as UserRead;
    },
    enabled: !!directoryId && !!userId,
  });
}
