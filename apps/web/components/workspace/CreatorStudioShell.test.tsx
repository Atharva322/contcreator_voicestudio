import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import CreatorStudioShell from "./CreatorStudioShell";
import type { CreatorProfile, ImportedPost } from "@/types/api";

const api = vi.hoisted(() => ({
  analyzeStyle: vi.fn(),
  clearProfileWorkspace: vi.fn(),
  createDraft: vi.fn(),
  createProfile: vi.fn(),
  deleteProfile: vi.fn(),
  getStyle: vi.fn(),
  importPosts: vi.fn(),
  decideVoiceSuggestion: vi.fn(),
  listStyleRevisions: vi.fn(),
  listDrafts: vi.fn(),
  listImportedPosts: vi.fn(),
  listProfiles: vi.fn(),
  listVoiceSuggestions: vi.fn(),
  reviewFeedbackForSuggestions: vi.fn(),
  updateDraftFeedback: vi.fn(),
  updateImportedPostInclusion: vi.fn(),
  updateProfile: vi.fn(),
  updateStyle: vi.fn(),
}));

vi.mock("@/lib/api", () => api);

const profile: CreatorProfile = {
  id: 1,
  name: "Test Creator",
  niche: "Creator systems",
  audience: "builders",
  goals: "Draft well",
  platforms: ["x", "instagram"],
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
};

const importedPost: ImportedPost = {
  id: 10,
  creator_id: 1,
  platform: "x",
  text: "Creator voice systems make drafting easier.",
  source: "test",
  quality_score: 90,
  quality_labels: ["x_compact"],
  quality_warnings: [],
  include_in_analysis: true,
  created_at: new Date().toISOString(),
};

describe("CreatorStudioShell", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    api.listProfiles.mockResolvedValue([profile]);
    api.getStyle.mockRejectedValue(new Error("No style"));
    api.listImportedPosts.mockResolvedValue([importedPost]);
    api.listDrafts.mockResolvedValue([]);
    api.listVoiceSuggestions.mockResolvedValue([]);
    api.listStyleRevisions.mockResolvedValue([]);
    api.updateImportedPostInclusion.mockResolvedValue({
      ...importedPost,
      include_in_analysis: false,
    });
  });

  it("loads the initial profile workspace", async () => {
    render(<CreatorStudioShell />);

    expect(await screen.findByText("Test Creator")).toBeInTheDocument();
    expect(await screen.findByText("1 eligible / 1 total")).toBeInTheDocument();
  });

  it("shows API load failures as actionable notices", async () => {
    api.listProfiles.mockRejectedValueOnce(new Error("API unreachable"));

    render(<CreatorStudioShell />);

    expect(await screen.findByText("API unreachable")).toBeInTheDocument();
  });

  it("updates sample inclusion through the backend", async () => {
    render(<CreatorStudioShell />);

    fireEvent.click(await screen.findByRole("button", { name: "Exclude" }));

    await waitFor(() => {
      expect(api.updateImportedPostInclusion).toHaveBeenCalledWith(1, 10, false);
    });
    expect(await screen.findByText("Sample excluded from future analysis.")).toBeInTheDocument();
  });
});
