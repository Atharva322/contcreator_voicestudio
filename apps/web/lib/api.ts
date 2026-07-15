import type { CreatorProfile, Draft, DraftFormat, Platform, StyleProfile } from "@/types/api";

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

  return response.json() as Promise<T>;
}

export function listProfiles() {
  return request<CreatorProfile[]>("/api/profiles");
}

export function createProfile(payload: {
  name: string;
  niche: string;
  audience: string;
  goals: string;
  platforms: Platform[];
}) {
  return request<CreatorProfile>("/api/profiles", {
    method: "POST",
    body: JSON.stringify(payload),
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

export function analyzeStyle(creatorId: number) {
  return request<StyleProfile>(`/api/profiles/${creatorId}/style/analyze`, {
    method: "POST",
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
  },
) {
  return request<Draft>(`/api/profiles/${creatorId}/drafts`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
