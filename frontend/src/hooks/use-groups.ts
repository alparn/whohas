"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { queryKeys } from "@/lib/query-keys";
import type {
  GroupRead,
  GroupDetailRead,
  GroupMemberRead,
} from "@/lib/api-types";

export function useGroups(directoryId: string, q: string = "") {
  return useQuery({
    queryKey: queryKeys.groups.list(directoryId, q),
    queryFn: async () => {
      const { data, error } = await api.GET(
        "/api/directories/{directory_id}/groups",
        {
          params: {
            path: { directory_id: directoryId },
            query: q ? { q } : undefined,
          },
        },
      );
      if (error) throw new Error("Failed to load groups");
      return data as GroupRead[];
    },
    enabled: !!directoryId,
  });
}

export function useGroup(directoryId: string, groupId: string) {
  return useQuery({
    queryKey: queryKeys.groups.detail(directoryId, groupId),
    queryFn: async () => {
      const { data, error } = await api.GET(
        "/api/directories/{directory_id}/groups/{group_id}",
        {
          params: {
            path: { directory_id: directoryId, group_id: groupId },
          },
        },
      );
      if (error) throw new Error("Group not found");
      return data as GroupDetailRead;
    },
    enabled: !!directoryId && !!groupId,
  });
}

export function useGroupMembers(directoryId: string, groupId: string) {
  return useQuery({
    queryKey: queryKeys.groups.members(directoryId, groupId),
    queryFn: async () => {
      const { data, error } = await api.GET(
        "/api/directories/{directory_id}/groups/{group_id}/members",
        {
          params: {
            path: { directory_id: directoryId, group_id: groupId },
          },
        },
      );
      if (error) throw new Error("Failed to load members");
      return data as GroupMemberRead[];
    },
    enabled: !!directoryId && !!groupId,
  });
}
