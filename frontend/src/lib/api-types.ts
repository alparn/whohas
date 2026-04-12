// TODO: Auto-generate from backend OpenAPI schema via `npm run generate:api`
// Scaffolded manually until backend is running.

export interface DirectoryRead {
  id: string;
  name: string;
  host: string;
  port: number;
  use_ssl: boolean;
  base_dn: string;
  user_filter: string;
  group_filter: string;
  last_full_sync_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface DirectoryCreate {
  name: string;
  host: string;
  port?: number;
  use_ssl?: boolean;
  bind_dn: string;
  bind_password: string;
  base_dn: string;
  user_filter?: string;
  group_filter?: string;
}

export interface DirectoryUpdate {
  name?: string;
  host?: string;
  port?: number;
  use_ssl?: boolean;
  bind_dn?: string;
  bind_password?: string;
  base_dn?: string;
  user_filter?: string;
  group_filter?: string;
}

export interface UserRead {
  id: string;
  directory_id: string;
  dn: string;
  sam_account_name: string;
  display_name: string;
  mail: string | null;
  last_logon: string | null;
  account_disabled: boolean;
  first_seen_at: string;
  last_seen_at: string;
}

export interface MembershipEntry {
  group_dn: string;
  group_name: string;
  depth: number;
  path: string[];
}

export interface MembershipResponse {
  user: { dn: string; display_name: string };
  memberships: MembershipEntry[];
  total: number;
  direct_count: number;
  inherited_count: number;
}

export interface ConnectionTestResult {
  ok: boolean;
  message: string;
}

export interface SyncTriggerResult {
  status: string;
  directory_id: string;
}

export interface SummaryResponse {
  total_users: number;
  total_groups: number;
  stale_user_count: number;
  empty_group_count: number;
  disabled_in_groups_count: number;
}

export interface StaleUserResponse {
  id: string;
  dn: string;
  display_name: string;
  sam_account_name: string;
  mail: string | null;
  last_logon: string | null;
  account_disabled: boolean;
}

export interface GroupResponse {
  id: string;
  dn: string;
  name: string;
  description: string | null;
}

export interface LargestGroupResponse {
  id: string;
  dn: string;
  name: string;
  description: string | null;
  effective_member_count: number;
}

export interface GroupRead {
  id: string;
  directory_id: string;
  dn: string;
  name: string;
  description: string | null;
  group_type: string | null;
  first_seen_at: string;
  last_seen_at: string;
}

export interface GroupDetailRead extends GroupRead {
  effective_member_count: number;
  direct_member_count: number;
}

export interface GroupMemberRead {
  user_dn: string;
  display_name: string;
  sam_account_name: string;
  mail: string | null;
  depth: number;
}

export interface paths {
  "/api/directories": {
    get: {
      responses: { 200: { content: { "application/json": DirectoryRead[] } } };
    };
    post: {
      requestBody: { content: { "application/json": DirectoryCreate } };
      responses: { 201: { content: { "application/json": DirectoryRead } } };
    };
  };
  "/api/directories/{directory_id}": {
    get: {
      parameters: { path: { directory_id: string } };
      responses: { 200: { content: { "application/json": DirectoryRead } } };
    };
    patch: {
      parameters: { path: { directory_id: string } };
      requestBody: { content: { "application/json": DirectoryUpdate } };
      responses: { 200: { content: { "application/json": DirectoryRead } } };
    };
  };
  "/api/directories/{directory_id}/users": {
    get: {
      parameters: {
        path: { directory_id: string };
        query?: { q?: string; limit?: number };
      };
      responses: { 200: { content: { "application/json": UserRead[] } } };
    };
  };
  "/api/directories/{directory_id}/users/{user_id}": {
    get: {
      parameters: { path: { directory_id: string; user_id: string } };
      responses: { 200: { content: { "application/json": UserRead } } };
    };
  };
  "/api/directories/{directory_id}/users/{user_id}/memberships": {
    get: {
      parameters: { path: { directory_id: string; user_id: string } };
      responses: {
        200: { content: { "application/json": MembershipResponse } };
      };
    };
  };
  "/api/directories/{directory_id}/groups": {
    get: {
      parameters: {
        path: { directory_id: string };
        query?: { q?: string; limit?: number };
      };
      responses: { 200: { content: { "application/json": GroupRead[] } } };
    };
  };
  "/api/directories/{directory_id}/groups/{group_id}": {
    get: {
      parameters: { path: { directory_id: string; group_id: string } };
      responses: {
        200: { content: { "application/json": GroupDetailRead } };
      };
    };
  };
  "/api/directories/{directory_id}/groups/{group_id}/members": {
    get: {
      parameters: {
        path: { directory_id: string; group_id: string };
        query?: { limit?: number };
      };
      responses: {
        200: { content: { "application/json": GroupMemberRead[] } };
      };
    };
  };
  "/api/directories/{directory_id}/insights/summary": {
    get: {
      parameters: { path: { directory_id: string } };
      responses: {
        200: { content: { "application/json": SummaryResponse } };
      };
    };
  };
  "/api/directories/{directory_id}/insights/stale-users": {
    get: {
      parameters: {
        path: { directory_id: string };
        query?: { limit?: number };
      };
      responses: {
        200: { content: { "application/json": StaleUserResponse[] } };
      };
    };
  };
  "/api/directories/{directory_id}/insights/empty-groups": {
    get: {
      parameters: {
        path: { directory_id: string };
        query?: { limit?: number };
      };
      responses: {
        200: { content: { "application/json": GroupResponse[] } };
      };
    };
  };
  "/api/directories/{directory_id}/insights/largest-groups": {
    get: {
      parameters: {
        path: { directory_id: string };
        query?: { limit?: number };
      };
      responses: {
        200: { content: { "application/json": LargestGroupResponse[] } };
      };
    };
  };
  "/api/directories/{directory_id}/insights/disabled-in-groups": {
    get: {
      parameters: {
        path: { directory_id: string };
        query?: { limit?: number };
      };
      responses: {
        200: { content: { "application/json": StaleUserResponse[] } };
      };
    };
  };
  "/api/directories/test": {
    post: {
      requestBody: { content: { "application/json": DirectoryCreate } };
      responses: {
        200: { content: { "application/json": ConnectionTestResult } };
      };
    };
  };
  "/api/directories/{directory_id}/sync": {
    post: {
      parameters: { path: { directory_id: string } };
      responses: {
        202: { content: { "application/json": SyncTriggerResult } };
      };
    };
  };
}
