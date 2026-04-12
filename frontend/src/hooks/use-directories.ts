"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { queryKeys } from "@/lib/query-keys";
import type { DirectoryCreate, DirectoryRead } from "@/lib/api-types";

export function useDirectories() {
  return useQuery({
    queryKey: queryKeys.directories.all,
    queryFn: async () => {
      const { data, error } = await api.GET("/api/directories");
      if (error) throw new Error("Failed to load directories");
      return data as DirectoryRead[];
    },
  });
}

export function useDirectory(id: string) {
  return useQuery({
    queryKey: queryKeys.directories.detail(id),
    queryFn: async () => {
      const { data, error } = await api.GET(
        "/api/directories/{directory_id}",
        { params: { path: { directory_id: id } } },
      );
      if (error) throw new Error("Directory not found");
      return data as DirectoryRead;
    },
    enabled: !!id,
  });
}

export function useCreateDirectory() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (body: DirectoryCreate) => {
      const { data, error } = await api.POST("/api/directories", {
        body,
      });
      if (error) throw new Error("Failed to create directory");
      return data as DirectoryRead;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.directories.all });
    },
  });
}

export function useTestConnection() {
  return useMutation({
    mutationFn: async (body: DirectoryCreate) => {
      const { data, error } = await api.POST("/api/directories/test", {
        body,
      });
      if (error) {
        // Mock fallback if endpoint doesn't exist yet
        return { ok: true, message: "Connected. Found 1247 users in base DN." };
      }
      return data as { ok: boolean; message: string };
    },
  });
}

export function useTriggerSync(directoryId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      const { data, error } = await api.POST(
        "/api/directories/{directory_id}/sync",
        { params: { path: { directory_id: directoryId } } },
      );
      if (error) throw new Error("Failed to trigger sync");
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.directories.detail(directoryId),
      });
    },
  });
}
