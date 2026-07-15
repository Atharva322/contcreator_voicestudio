"use client";

import { useEffect, useMemo, useState } from "react";
import {
  analyzeStyle,
  createDraft,
  createProfile,
  getStyle,
  importPosts,
  listProfiles,
} from "@/lib/api";
import type { CreatorProfile, Draft, DraftFormat, Platform, StyleProfile } from "@/types/api";

const samplePosts = `Building a content system is less about posting more and more about making your point impossible to miss.

The best creators do not chase consistency.
They design it.

Your caption should do three jobs:
1. Stop the scroll
2. Make the idea useful
3. Give the reader a next step`;

export default function Home() {
  const [profiles, setProfiles] = useState<CreatorProfile[]>([]);
  const [activeId, setActiveId] = useState<number | null>(null);
  const [style, setStyle] = useState<StyleProfile | null>(null);
  const [draft, setDraft] = useState<Draft | null>(null);
  const [status, setStatus] = useState<string>("");
  const [error, setError] = useState<string>("");

  const [profileForm, setProfileForm] = useState({
    name: "Atharva Studio",
    niche: "AI projects and creator tools",
    audience: "builders, students, and early-stage creators",
    goals: "Draft useful social content that still sounds personal.",
  });

  const [importForm, setImportForm] = useState({
    platform: "x" as Platform,
    raw_posts: samplePosts,
  });

  const [draftForm, setDraftForm] = useState({
    platform: "x" as Platform,
    draft_format: "x_post" as DraftFormat,
    topic: "Why creators need a reusable voice system instead of random AI captions",
    audience: "",
    cta: "Save this for your next content planning session.",
    length: "medium",
    creativity: 0.55,
  });

  const activeProfile = useMemo(
    () => profiles.find((profile) => profile.id === activeId) || null,
    [profiles, activeId],
  );

  useEffect(() => {
    refreshProfiles();
  }, []);

  async function refreshProfiles() {
    try {
      const data = await listProfiles();
      setProfiles(data);
      if (!activeId && data.length) {
        setActiveId(data[0].id);
        refreshStyle(data[0].id);
      }
    } catch (err) {
      setError(messageFromError(err));
    }
  }

  async function refreshStyle(creatorId: number) {
    try {
      const data = await getStyle(creatorId);
      setStyle(data);
    } catch {
      setStyle(null);
    }
  }

  async function handleCreateProfile() {
    runAction(async () => {
      const profile = await createProfile({
        ...profileForm,
        platforms: ["x", "instagram"],
      });
      setProfiles((current) => [profile, ...current]);
      setActiveId(profile.id);
      setStyle(null);
      setDraft(null);
      setStatus("Creator profile created. Import at least 3 posts next.");
    });
  }

  async function handleImportPosts() {
    if (!activeId) return setError("Create or select a profile first.");
    runAction(async () => {
      const result = await importPosts(activeId, {
        platform: importForm.platform,
        raw_posts: importForm.raw_posts,
        source: "manual",
      });
      setStatus(`Imported ${result.imported} posts. Skipped ${result.skipped} duplicates/empty posts.`);
    });
  }

  async function handleAnalyzeStyle() {
    if (!activeId) return setError("Create or select a profile first.");
    runAction(async () => {
      const data = await analyzeStyle(activeId);
      setStyle(data);
      setStatus("Voice profile learned. Tiny wizard hat placed on the style engine.");
    });
  }

  async function handleCreateDraft() {
    if (!activeId) return setError("Create or select a profile first.");
    runAction(async () => {
      const data = await createDraft(activeId, draftForm);
      setDraft(data);
      setStatus("Generated 3 draft variants.");
    });
  }

  async function runAction(action: () => Promise<void>) {
    setError("");
    setStatus("Working...");
    try {
      await action();
    } catch (err) {
      setStatus("");
      setError(messageFromError(err));
    }
  }

  function selectProfile(profileId: number) {
    setActiveId(profileId);
    setDraft(null);
    refreshStyle(profileId);
  }

  return (
    <main className="shell">
      <section className="hero">
        <div className="hero-card">
          <div className="eyebrow">Local-first AI content assistant</div>
          <h1>Creator Voice Studio</h1>
          <p>
            Learn a creator&apos;s writing style from X and Instagram posts, inspect the voice
            profile, then draft captions and scripts that sound less like a template goblin.
          </p>
          <div className="hero-actions">
            <a className="button" href="#composer">
              Generate a draft
            </a>
            <a className="button secondary" href="#voice">
              View voice profile
            </a>
          </div>
        </div>
        <aside className="hero-card stat-card">
          <div className="eyebrow">Current build</div>
          <div className="stat">
            <strong>{profiles.length}</strong>
            <span className="muted">creator profiles</span>
          </div>
          <div className="stat">
            <strong>{style ? "Ready" : "Train"}</strong>
            <span className="muted">voice profile status</span>
          </div>
        </aside>
      </section>

      {(status || error) && (
        <section className={`notice ${error ? "error" : ""}`}>{error || status}</section>
      )}

      <section className="grid" style={{ marginTop: 24 }}>
        <div className="stack">
          <section className="panel stack">
            <h2>1. Creator Profile</h2>
            <div className="field">
              <label>Name</label>
              <input
                value={profileForm.name}
                onChange={(event) => setProfileForm({ ...profileForm, name: event.target.value })}
              />
            </div>
            <div className="field">
              <label>Niche</label>
              <input
                value={profileForm.niche}
                onChange={(event) => setProfileForm({ ...profileForm, niche: event.target.value })}
              />
            </div>
            <div className="field">
              <label>Audience</label>
              <input
                value={profileForm.audience}
                onChange={(event) => setProfileForm({ ...profileForm, audience: event.target.value })}
              />
            </div>
            <div className="field">
              <label>Goals</label>
              <textarea
                value={profileForm.goals}
                onChange={(event) => setProfileForm({ ...profileForm, goals: event.target.value })}
              />
            </div>
            <button className="button" onClick={handleCreateProfile}>
              Create profile
            </button>
          </section>

          <section className="panel stack">
            <h3>Profiles</h3>
            <div className="profile-list">
              {profiles.length === 0 && <p>No profiles yet. Create one to begin.</p>}
              {profiles.map((profile) => (
                <button
                  className={`profile-pill ${profile.id === activeId ? "active" : ""}`}
                  key={profile.id}
                  onClick={() => selectProfile(profile.id)}
                >
                  <strong>{profile.name}</strong>
                  <div className="tiny muted">{profile.niche || "No niche yet"}</div>
                </button>
              ))}
            </div>
          </section>
        </div>

        <div className="stack">
          <section className="panel stack">
            <h2>2. Import Posts</h2>
            <p>
              Paste posts separated by blank lines, or paste CSV/JSON with a text, caption, content,
              or post field.
            </p>
            <div className="two-col">
              <div className="field">
                <label>Platform</label>
                <select
                  value={importForm.platform}
                  onChange={(event) =>
                    setImportForm({ ...importForm, platform: event.target.value as Platform })
                  }
                >
                  <option value="x">X</option>
                  <option value="instagram">Instagram</option>
                </select>
              </div>
              <div className="field">
                <label>Selected profile</label>
                <input value={activeProfile?.name || "None"} readOnly />
              </div>
            </div>
            <textarea
              value={importForm.raw_posts}
              onChange={(event) => setImportForm({ ...importForm, raw_posts: event.target.value })}
            />
            <div className="row">
              <button className="button" onClick={handleImportPosts}>
                Import posts
              </button>
              <button className="button secondary" onClick={handleAnalyzeStyle}>
                Analyze voice
              </button>
            </div>
          </section>

          <section className="panel stack" id="voice">
            <h2>3. Learned Voice</h2>
            {!style && <p>Analyze at least 3 imported posts to generate a visible voice profile.</p>}
            {style && (
              <>
                <p>{style.summary}</p>
                <div className="voice-grid">
                  <VoiceTile title="Tone" value={style.tone} />
                  <VoiceTile title="Hooks" value={style.hooks} />
                  <VoiceTile title="Rhythm" value={style.rhythm} />
                  <VoiceTile title="Vocabulary" value={style.vocabulary} />
                  <VoiceTile title="Emoji / Hashtags" value={style.emoji_hashtag_habits} />
                  <VoiceTile title="Avoid" value={style.avoid_rules} />
                </div>
              </>
            )}
          </section>

          <section className="panel stack" id="composer">
            <h2>4. Draft Composer</h2>
            <div className="two-col">
              <div className="field">
                <label>Platform</label>
                <select
                  value={draftForm.platform}
                  onChange={(event) =>
                    setDraftForm({ ...draftForm, platform: event.target.value as Platform })
                  }
                >
                  <option value="x">X</option>
                  <option value="instagram">Instagram</option>
                </select>
              </div>
              <div className="field">
                <label>Format</label>
                <select
                  value={draftForm.draft_format}
                  onChange={(event) =>
                    setDraftForm({ ...draftForm, draft_format: event.target.value as DraftFormat })
                  }
                >
                  <option value="x_post">X post</option>
                  <option value="instagram_caption">Instagram caption</option>
                  <option value="short_script">Short script</option>
                </select>
              </div>
            </div>
            <div className="field">
              <label>Topic</label>
              <textarea
                value={draftForm.topic}
                onChange={(event) => setDraftForm({ ...draftForm, topic: event.target.value })}
              />
            </div>
            <div className="two-col">
              <div className="field">
                <label>CTA</label>
                <input
                  value={draftForm.cta}
                  onChange={(event) => setDraftForm({ ...draftForm, cta: event.target.value })}
                />
              </div>
              <div className="field">
                <label>Creativity</label>
                <input
                  max="1"
                  min="0"
                  step="0.05"
                  type="range"
                  value={draftForm.creativity}
                  onChange={(event) =>
                    setDraftForm({ ...draftForm, creativity: Number(event.target.value) })
                  }
                />
              </div>
            </div>
            <button className="button" onClick={handleCreateDraft}>
              Generate variants
            </button>
            {draft && (
              <div className="drafts">
                {draft.variants.map((variant) => (
                  <article className="draft-card" key={variant.label}>
                    <strong>{variant.label}</strong>
                    <pre>{variant.text}</pre>
                    <p className="tiny">{variant.rationale}</p>
                  </article>
                ))}
              </div>
            )}
          </section>
        </div>
      </section>
    </main>
  );
}

function VoiceTile({ title, value }: { title: string; value: string }) {
  return (
    <div className="voice-tile">
      <strong>{title}</strong>
      <span className="muted">{value}</span>
    </div>
  );
}

function messageFromError(error: unknown) {
  return error instanceof Error ? error.message : "Something went sideways.";
}
