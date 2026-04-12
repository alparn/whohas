export const queryKeys = {
  directories: {
    all: ["directories"] as const,
    detail: (id: string) => ["directories", id] as const,
  },
  users: {
    search: (directoryId: string, q: string) =>
      ["directories", directoryId, "users", { q }] as const,
    detail: (directoryId: string, userId: string) =>
      ["directories", directoryId, "users", userId] as const,
  },
  groups: {
    list: (directoryId: string, q: string) =>
      ["directories", directoryId, "groups", { q }] as const,
    detail: (directoryId: string, groupId: string) =>
      ["directories", directoryId, "groups", groupId] as const,
    members: (directoryId: string, groupId: string) =>
      ["directories", directoryId, "groups", groupId, "members"] as const,
  },
  memberships: {
    byUser: (directoryId: string, userId: string) =>
      ["directories", directoryId, "users", userId, "memberships"] as const,
  },
  graph: {
    view: (directoryId: string, rootDn: string | null, depth: number) =>
      ["directories", directoryId, "graph", { rootDn, depth }] as const,
  },
  insights: {
    summary: (directoryId: string) =>
      ["directories", directoryId, "insights", "summary"] as const,
    staleUsers: (directoryId: string, limit: number) =>
      ["directories", directoryId, "insights", "stale-users", { limit }] as const,
    largestGroups: (directoryId: string, limit: number) =>
      ["directories", directoryId, "insights", "largest-groups", { limit }] as const,
    emptyGroups: (directoryId: string, limit: number) =>
      ["directories", directoryId, "insights", "empty-groups", { limit }] as const,
    disabledInGroups: (directoryId: string, limit: number) =>
      ["directories", directoryId, "insights", "disabled-in-groups", { limit }] as const,
  },
};
