"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { queryKeys } from "@/lib/query-keys";
import type {
  GroupResponse,
  LargestGroupResponse,
  StaleUserResponse,
  SummaryResponse,
} from "@/lib/api-types";

export function useSummary(directoryId: string) {
  return useQuery({
    queryKey: queryKeys.insights.summary(directoryId),
    queryFn: async () => {
      const { data, error } = await api.GET(
        "/api/directories/{directory_id}/insights/summary",
        { params: { path: { directory_id: directoryId } } },
      );
      if (error) throw new Error("Failed to load summary");
      return data as SummaryResponse;
    },
    enabled: !!directoryId,
    staleTime: 60_000,
  });
}

export function useStaleUsers(directoryId: string, limit: number = 10) {
  return useQuery({
    queryKey: queryKeys.insights.staleUsers(directoryId, limit),
    queryFn: async () => {
      const { data, error } = await api.GET(
        "/api/directories/{directory_id}/insights/stale-users",
        {
          params: {
            path: { directory_id: directoryId },
            query: { limit },
          },
        },
      );
      if (error) throw new Error("Failed to load stale users");
      return data as StaleUserResponse[];
    },
    enabled: !!directoryId,
    staleTime: 60_000,
  });
}

export function useLargestGroups(directoryId: string, limit: number = 10) {
  return useQuery({
    queryKey: queryKeys.insights.largestGroups(directoryId, limit),
    queryFn: async () => {
      const { data, error } = await api.GET(
        "/api/directories/{directory_id}/insights/largest-groups",
        {
          params: {
            path: { directory_id: directoryId },
            query: { limit },
          },
        },
      );
      if (error) throw new Error("Failed to load largest groups");
      return data as LargestGroupResponse[];
    },
    enabled: !!directoryId,
    staleTime: 60_000,
  });
}

export function useEmptyGroups(directoryId: string, limit: number = 100) {
  return useQuery({
    queryKey: queryKeys.insights.emptyGroups(directoryId, limit),
    queryFn: async () => {
      const { data, error } = await api.GET(
        "/api/directories/{directory_id}/insights/empty-groups",
        {
          params: {
            path: { directory_id: directoryId },
            query: { limit },
          },
        },
      );
      if (error) throw new Error("Failed to load empty groups");
      return data as GroupResponse[];
    },
    enabled: !!directoryId,
    staleTime: 60_000,
  });
}

export function useDisabledInGroups(directoryId: string, limit: number = 100) {
  return useQuery({
    queryKey: queryKeys.insights.disabledInGroups(directoryId, limit),
    queryFn: async () => {
      const { data, error } = await api.GET(
        "/api/directories/{directory_id}/insights/disabled-in-groups",
        {
          params: {
            path: { directory_id: directoryId },
            query: { limit },
          },
        },
      );
      if (error) throw new Error("Failed to load disabled users");
      return data as StaleUserResponse[];
    },
    enabled: !!directoryId,
    staleTime: 60_000,
  });
}
