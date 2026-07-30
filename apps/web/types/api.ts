export type Platform = "x" | "instagram";

export type DraftFormat = "x_post" | "instagram_caption" | "short_script";

export type CreatorProfile = {
  id: number;
  name: string;
  niche: string;
  audience: string;
  goals: string;
  platforms: string[];
  created_at: string;
  updated_at: string;
};

export type ImportedPost = {
  id: number;
  creator_id: number;
  platform: Platform;
  text: string;
  source: string;
  quality_score: number;
  quality_labels: string[];
  quality_warnings: string[];
  include_in_analysis: boolean;
  created_at: string;
};

export type StyleProfile = {
  creator_id: number;
  summary: string;
  tone: string;
  hooks: string;
  rhythm: string;
  vocabulary: string;
  emoji_hashtag_habits: string;
  cta_habits: string;
  formatting: string;
  avoid_rules: string;
  updated_at: string;
};

export type StyleGuideRevision = {
  id: number;
  creator_id: number;
  summary: string;
  tone: string;
  hooks: string;
  rhythm: string;
  vocabulary: string;
  emoji_hashtag_habits: string;
  cta_habits: string;
  formatting: string;
  avoid_rules: string;
  reason: string;
  created_at: string;
};

export type VoiceSuggestion = {
  id: number;
  creator_id: number;
  source_draft_id?: number | null;
  target_field: string;
  suggestion: string;
  rationale: string;
  status: "pending" | "accepted" | "dismissed";
  created_at: string;
  updated_at: string;
};

export type DraftVariant = {
  label: string;
  text: string;
  rationale: string;
};

export type DraftWarning = {
  variant_label: string;
  type: string;
  score?: number;
  message: string;
};

export type DraftEvidence = {
  title: string;
  text: string;
};

export type Draft = {
  id: number;
  creator_id: number;
  platform: Platform;
  draft_format: DraftFormat;
  topic: string;
  variants: DraftVariant[];
  warnings: DraftWarning[];
  evidence: DraftEvidence[];
  rating?: number | null;
  feedback?: string | null;
  created_at: string;
};
