"use client";

import { useEffect, useMemo, useState } from "react";
import {
  analyzeStyle,
  createDraft,
  createProfile,
  getStyle,
  importPosts,
  listDrafts,
  listImportedPosts,
  listProfiles,
  updateDraftFeedback,
} from "@/lib/api";
import type { CreatorProfile, Draft, DraftFormat, ImportedPost, Platform, StyleProfile } from "@/types/api";

const samplePosts = `Building a content system is less about posting more and more about making your point impossible to miss.

The best creators do not chase consistency.
They design it.

Your caption should do three jobs:
1. Stop the scroll
2. Make the idea useful
3. Give the reader a next step`;

type StepStatus = "done" | "active" | "locked";

export default function Home() {
  const [profiles, setProfiles] = useState<CreatorProfile[]>([]);
  const [activeId, setActiveId] = useState<number | null>(null);
  const [style, setStyle] = useState<StyleProfile | null>(null);
  const [draft, setDraft] = useState<Draft | null>(null);
  const [drafts, setDrafts] = useState<Draft[]>([]);
  const [importedPosts, setImportedPosts] = useState<ImportedPost[]>([]);
  const [selectedVariant, setSelectedVariant] = useState<Record<number, string>>({});
  const [feedbackNotes, setFeedbackNotes] = useState<Record<number, string>>({});
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
  const hasProfile = Boolean(activeId);
  const hasEnoughPosts = importedPosts.length >= 3;
  const hasStyle = Boolean(style);
  const hasDrafts = drafts.length > 0;
  const canImportPosts = hasProfile && importForm.raw_posts.trim().length > 0;
  const canAnalyzeStyle = hasProfile && hasEnoughPosts;
  const canGenerateDraft = hasProfile && hasStyle && draftForm.topic.trim().length > 0;
  const nextAction = getNextAction(hasProfile, hasEnoughPosts, hasStyle, hasDrafts);

  useEffect(() => {
    refreshProfiles();
  }, []);

  async function refreshProfiles() {
    try {
      const data = await listProfiles();
      setProfiles(data);
      if (!activeId && data.length) {
        setActiveId(data[0].id);
        refreshWorkspace(data[0].id);
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

  async function refreshWorkspace(creatorId: number) {
    refreshStyle(creatorId);
    refreshImportedPosts(creatorId);
    refreshDrafts(creatorId);
  }

  async function refreshImportedPosts(creatorId: number) {
    try {
      const data = await listImportedPosts(creatorId);
      setImportedPosts(data);
    } catch {
      setImportedPosts([]);
    }
  }

  async function refreshDrafts(creatorId: number) {
    try {
      const data = await listDrafts(creatorId);
      setDrafts(data);
    } catch {
      setDrafts([]);
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
      setDrafts([]);
      setImportedPosts([]);
      setStatus("Creator profile created. Add writing samples next.");
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
      await refreshImportedPosts(activeId);
      setStatus(`Imported ${result.imported} samples. Skipped ${result.skipped} duplicates or empty items.`);
    });
  }

  async function handleAnalyzeStyle() {
    if (!activeId) return setError("Create or select a profile first.");
    runAction(async () => {
      const data = await analyzeStyle(activeId);
      setStyle(data);
      setStatus("Voice profile learned. Draft generation is ready.");
    });
  }

  async function handleCreateDraft() {
    if (!activeId) return setError("Create or select a profile first.");
    runAction(async () => {
      const data = await createDraft(activeId, draftForm);
      setDraft(data);
      await refreshDrafts(activeId);
      setStatus("Generated 3 draft variants.");
    });
  }

  async function handleCopy(text: string) {
    try {
      await navigator.clipboard.writeText(text);
      setStatus("Copied draft to clipboard.");
    } catch {
      setError("Copy failed. Select the text manually this time.");
    }
  }

  async function handleFeedback(draftItem: Draft, rating: number) {
    if (!activeId) return setError("Create or select a profile first.");
    const selectedText = selectedVariant[draftItem.id] || draftItem.variants[0]?.text || "";
    runAction(async () => {
      const updated = await updateDraftFeedback(activeId, draftItem.id, {
        selected_text: selectedText,
        rating,
        feedback: feedbackNotes[draftItem.id] || "",
      });
      setDrafts((current) => current.map((item) => (item.id === updated.id ? updated : item)));
      if (draft?.id === updated.id) {
        setDraft(updated);
      }
      setStatus(`Saved ${rating}/5 feedback for this draft.`);
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
    refreshWorkspace(profileId);
  }

  return (
    <main className="shell">
      <section className="hero">
        <div className="hero-copy">
          <div className="eyebrow">Creator studio for voice-led drafting</div>
          <h1>Turn writing samples into publish-ready drafts.</h1>
          <p>
            A guided local workspace for importing creator samples, learning the writing voice, and
            drafting X posts, Instagram captions, and short scripts without pretending it can post for you.
          </p>
          <div className="hero-actions">
            <a className="button" href="#draft">
              Start drafting
            </a>
            <a className="button secondary" href="#samples">
              Add writing samples
            </a>
          </div>
        </div>
        <aside className="studio-card next-card">
          <span className="tag warm">Next best action</span>
          <h2>{nextAction.title}</h2>
          <p>{nextAction.description}</p>
          <div className="metric-grid">
            <Metric label="Samples" value={importedPosts.length.toString()} />
            <Metric label="Drafts" value={drafts.length.toString()} />
            <Metric label="Voice" value={style ? "Ready" : "Pending"} />
          </div>
        </aside>
      </section>

      <section className="wizard-rail" aria-label="Creator Voice Studio progress">
        <WizardStep index="01" label="Profile" status={hasProfile ? "done" : "active"} />
        <WizardStep index="02" label="Samples" status={!hasProfile ? "locked" : hasEnoughPosts ? "done" : "active"} />
        <WizardStep index="03" label="Analyze" status={!hasEnoughPosts ? "locked" : hasStyle ? "done" : "active"} />
        <WizardStep index="04" label="Draft" status={!hasStyle ? "locked" : hasDrafts ? "done" : "active"} />
        <WizardStep index="05" label="Review" status={!hasDrafts ? "locked" : "active"} />
      </section>

      {(status || error) && (
        <section className={`notice ${error ? "error" : ""}`}>{error || status}</section>
      )}

      <section className="workspace">
        <aside className="side-stack">
          <section className="studio-card stack">
            <div>
              <span className="section-kicker">Step 01</span>
              <h2>Creator profile</h2>
              <p>Set the basic creative context for this local workspace.</p>
            </div>
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

          <section className="studio-card stack">
            <div className="row between">
              <h3>Profiles</h3>
              <span className="tag">{profiles.length}</span>
            </div>
            <div className="profile-list">
              {profiles.length === 0 && <p>No profiles yet. Create one to begin.</p>}
              {profiles.map((profile) => (
                <button
                  className={`profile-pill ${profile.id === activeId ? "active" : ""}`}
                  key={profile.id}
                  onClick={() => selectProfile(profile.id)}
                >
                  <strong>{profile.name}</strong>
                  <span>{profile.niche || "No niche yet"}</span>
                </button>
              ))}
            </div>
          </section>
        </aside>

        <section className="main-stack">
          <section className="studio-card draft-lab stack" id="draft">
            <div className="section-heading">
              <div>
                <span className="section-kicker">Step 04 · Priority workspace</span>
                <h2>Draft generation lab</h2>
                <p>
                  Once the profile and writing samples are ready, generate three draft directions and
                  copy the strongest one into your real publishing workflow.
                </p>
              </div>
              <span className={`status-pill ${canGenerateDraft ? "ready" : ""}`}>
                {canGenerateDraft ? "Ready" : "Needs voice"}
              </span>
            </div>

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
              <label>Draft brief</label>
              <textarea
                className="brief-textarea"
                value={draftForm.topic}
                onChange={(event) => setDraftForm({ ...draftForm, topic: event.target.value })}
              />
            </div>

            <div className="two-col">
              <div className="field">
                <label>Call to action</label>
                <input
                  value={draftForm.cta}
                  onChange={(event) => setDraftForm({ ...draftForm, cta: event.target.value })}
                />
              </div>
              <div className="field">
                <label>Creativity: {Math.round(draftForm.creativity * 100)}%</label>
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

            <div className="row">
              <button className="button jumbo" disabled={!canGenerateDraft} onClick={handleCreateDraft}>
                Generate draft variants
              </button>
              {!hasProfile && <span className="hint">Create a profile first.</span>}
              {hasProfile && !hasStyle && <span className="hint">Analyze the voice before drafting.</span>}
            </div>

            {draft && (
              <div className="variant-grid">
                {draft.variants.map((variant) => (
                  <article className="draft-card featured" key={variant.label}>
                    <div className="row between">
                      <strong>{variant.label}</strong>
                      <button className="button compact secondary" onClick={() => handleCopy(variant.text)}>
                        Copy
                      </button>
                    </div>
                    <pre>{variant.text}</pre>
                    <p>{variant.rationale}</p>
                  </article>
                ))}
              </div>
            )}
          </section>

          <section className="studio-card stack" id="samples">
            <div className="section-heading">
              <div>
                <span className="section-kicker">Step 02 + 03</span>
                <h2>Import writing samples</h2>
                <p>
                  Manual import only for now. Paste X or Instagram examples separated by blank lines,
                  or use CSV/JSON fields like text, caption, content, or post.
                </p>
              </div>
              <span className="status-pill">{importedPosts.length} samples</span>
            </div>

            <div className="two-col">
              <div className="field">
                <label>Sample source</label>
                <select
                  value={importForm.platform}
                  onChange={(event) =>
                    setImportForm({ ...importForm, platform: event.target.value as Platform })
                  }
                >
                  <option value="x">X writing samples</option>
                  <option value="instagram">Instagram captions</option>
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
              <button className="button secondary" disabled={!canImportPosts} onClick={handleImportPosts}>
                Import samples
              </button>
              <button className="button secondary" disabled={!canAnalyzeStyle} onClick={handleAnalyzeStyle}>
                Analyze voice
              </button>
              {!hasEnoughPosts && <span className="hint">Need at least 3 samples to analyze.</span>}
            </div>

            <div className="mini-list">
              <div className="row between">
                <strong>Recent samples</strong>
                <span className="muted">{importedPosts.length} total</span>
              </div>
              {importedPosts.length === 0 && (
                <p>Imported writing samples will appear here after you add them.</p>
              )}
              {importedPosts.slice(0, 3).map((post) => (
                <article className="mini-card" key={post.id}>
                  <span className="tag">{post.platform}</span>
                  <p>{post.text}</p>
                </article>
              ))}
            </div>
          </section>

          <section className="studio-card stack">
            <div className="section-heading">
              <div>
                <span className="section-kicker">Step 05</span>
                <h2>Feedback and draft history</h2>
                <p>Review generated drafts, copy the strongest variant, and save a quick rating.</p>
              </div>
              <span className="status-pill">{drafts.length} drafts</span>
            </div>

            {drafts.length === 0 && (
              <div className="empty-state">
                <strong>No drafts yet</strong>
                <p>Generate variants above and they will be saved here for review.</p>
              </div>
            )}

            <div className="drafts">
              {drafts.map((draftItem) => (
                <article className="draft-card" key={draftItem.id}>
                  <div className="row between">
                    <div>
                      <strong>{draftItem.topic}</strong>
                      <div className="muted">
                        {draftItem.platform} · {draftItem.draft_format} ·{" "}
                        {new Date(draftItem.created_at).toLocaleString()}
                      </div>
                    </div>
                    {draftItem.rating && <span className="tag warm">{draftItem.rating}/5</span>}
                  </div>
                  <div className="field">
                    <label>Best variant</label>
                    <select
                      value={selectedVariant[draftItem.id] || draftItem.variants[0]?.text || ""}
                      onChange={(event) =>
                        setSelectedVariant({
                          ...selectedVariant,
                          [draftItem.id]: event.target.value,
                        })
                      }
                    >
                      {draftItem.variants.map((variant) => (
                        <option key={variant.label} value={variant.text}>
                          {variant.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <pre>{selectedVariant[draftItem.id] || draftItem.variants[0]?.text || ""}</pre>
                  <div className="row">
                    <button
                      className="button compact secondary"
                      onClick={() => handleCopy(selectedVariant[draftItem.id] || draftItem.variants[0]?.text || "")}
                    >
                      Copy selected
                    </button>
                    {[1, 2, 3, 4, 5].map((rating) => (
                      <button
                        className={`rating ${draftItem.rating === rating ? "active" : ""}`}
                        key={rating}
                        onClick={() => handleFeedback(draftItem, rating)}
                      >
                        {rating}
                      </button>
                    ))}
                  </div>
                  <div className="field">
                    <label>Feedback notes</label>
                    <textarea
                      className="small-textarea"
                      placeholder="What worked? What felt off?"
                      value={feedbackNotes[draftItem.id] ?? draftItem.feedback ?? ""}
                      onChange={(event) =>
                        setFeedbackNotes({
                          ...feedbackNotes,
                          [draftItem.id]: event.target.value,
                        })
                      }
                    />
                  </div>
                </article>
              ))}
            </div>
          </section>

          <section className="studio-card compact-section" id="voice">
            <div>
              <span className="section-kicker">Voice profile</span>
              <h2>Learned voice signals</h2>
              {!style && <p>Voice insights appear after analysis. This stays secondary to drafting for now.</p>}
            </div>
            {style && (
              <div className="voice-grid">
                <VoiceTile title="Tone" value={style.tone} />
                <VoiceTile title="Hooks" value={style.hooks} />
                <VoiceTile title="Rhythm" value={style.rhythm} />
                <VoiceTile title="Vocabulary" value={style.vocabulary} />
                <VoiceTile title="Emoji / Hashtags" value={style.emoji_hashtag_habits} />
                <VoiceTile title="Avoid" value={style.avoid_rules} />
              </div>
            )}
          </section>
        </section>
      </section>
    </main>
  );
}

function WizardStep({
  index,
  label,
  status,
}: {
  index: string;
  label: string;
  status: StepStatus;
}) {
  return (
    <div className={`wizard-step ${status}`}>
      <span>{index}</span>
      <strong>{label}</strong>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric">
      <strong>{value}</strong>
      <span>{label}</span>
    </div>
  );
}

function VoiceTile({ title, value }: { title: string; value: string }) {
  return (
    <div className="voice-tile">
      <strong>{title}</strong>
      <span>{value}</span>
    </div>
  );
}

function getNextAction(hasProfile: boolean, hasEnoughPosts: boolean, hasStyle: boolean, hasDrafts: boolean) {
  if (!hasProfile) {
    return {
      title: "Create a creator profile",
      description: "Start by defining the creator, niche, audience, and content goal.",
    };
  }
  if (!hasEnoughPosts) {
    return {
      title: "Import writing samples",
      description: "Add at least three X posts or Instagram captions before analysis.",
    };
  }
  if (!hasStyle) {
    return {
      title: "Analyze the voice",
      description: "Convert samples into a reusable voice profile before drafting.",
    };
  }
  if (!hasDrafts) {
    return {
      title: "Generate the first draft",
      description: "Use the draft lab to produce three on-voice directions.",
    };
  }
  return {
    title: "Review and refine",
    description: "Rate the strongest draft so the workflow captures your preferences.",
  };
}

function messageFromError(error: unknown) {
  return error instanceof Error ? error.message : "Something went sideways.";
}
