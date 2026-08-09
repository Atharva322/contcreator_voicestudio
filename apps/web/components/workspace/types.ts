import type { StyleProfile } from "@/types/api";

export type StepStatus = "done" | "active" | "locked";
export type EditableStyleProfile = Omit<StyleProfile, "creator_id" | "updated_at">;
