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

export type DraftVariant = {
  label: string;
  text: string;
  rationale: string;
};

export type Draft = {
  id: number;
  creator_id: number;
  platform: Platform;
  draft_format: DraftFormat;
  topic: string;
  variants: DraftVariant[];
  rating?: number | null;
  feedback?: string | null;
  created_at: string;
};
