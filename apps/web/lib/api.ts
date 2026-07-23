import type {
  CreatorProfile,
  Draft,
  DraftFormat,
  ImportedPost,
  Platform,
  StyleProfile,
} from "@/types/api";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || "Request failed");
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export function listProfiles() {
  return request<CreatorProfile[]>("/api/profiles");
}

export type ProfilePayload = {
  name: string;
  niche: string;
  audience: string;
  goals: string;
  platforms: Platform[];
};

export function createProfile(payload: ProfilePayload) {
  return request<CreatorProfile>("/api/profiles", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateProfile(creatorId: number, payload: ProfilePayload) {
  return request<CreatorProfile>(`/api/profiles/${creatorId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function clearProfileWorkspace(creatorId: number) {
  return request<void>(`/api/profiles/${creatorId}/workspace`, {
    method: "DELETE",
  });
}

export function deleteProfile(creatorId: number) {
  return request<void>(`/api/profiles/${creatorId}`, {
    method: "DELETE",
  });
}

export function importPosts(
  creatorId: number,
  payload: { platform: Platform; raw_posts: string; source: string },
) {
  return request<{ imported: number; skipped: number }>(`/api/profiles/${creatorId}/imports`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listImportedPosts(creatorId: number) {
  return request<ImportedPost[]>(`/api/profiles/${creatorId}/imports`);
}

export function analyzeStyle(creatorId: number) {
  return request<StyleProfile>(`/api/profiles/${creatorId}/style/analyze`, {
    method: "POST",
  });
}

export function listDrafts(creatorId: number) {
  return request<Draft[]>(`/api/profiles/${creatorId}/drafts`);
}

export function updateDraftFeedback(
  creatorId: number,
  draftId: number,
  payload: { selected_text?: string; rating?: number; feedback?: string },
) {
  return request<Draft>(`/api/profiles/${creatorId}/drafts/${draftId}/feedback`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function getStyle(creatorId: number) {
  return request<StyleProfile>(`/api/profiles/${creatorId}/style`);
}

export function createDraft(
  creatorId: number,
  payload: {
    platform: Platform;
    draft_format: DraftFormat;
    topic: string;
    audience: string;
    cta: string;
    length: string;
    creativity: number;
    include_hashtags: boolean;
    show_reuse_warnings: boolean;
    show_evidence: boolean;
  },
) {
  return request<Draft>(`/api/profiles/${creatorId}/drafts`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
