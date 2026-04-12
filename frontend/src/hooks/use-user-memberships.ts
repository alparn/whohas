"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { queryKeys } from "@/lib/query-keys";
import type { MembershipResponse } from "@/lib/api-types";

export function useUserMemberships(directoryId: string, userId: string) {
  return useQuery({
    queryKey: queryKeys.memberships.byUser(directoryId, userId),
    queryFn: async () => {
      const { data, error } = await api.GET(
        "/api/directories/{directory_id}/users/{user_id}/memberships",
        {
          params: {
            path: { directory_id: directoryId, user_id: userId },
          },
        },
      );
      if (error) throw new Error("Failed to load memberships");
      return data as MembershipResponse;
    },
    enabled: !!directoryId && !!userId,
  });
}
