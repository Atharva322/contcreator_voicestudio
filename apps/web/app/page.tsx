"use client";

import { useEffect, useMemo, useState } from "react";
import {
  analyzeStyle,
  clearProfileWorkspace,
  createDraft,
  createProfile,
  deleteProfile,
  getStyle,
  importPosts,
  decideVoiceSuggestion,
  listStyleRevisions,
  listDrafts,
  listImportedPosts,
  listProfiles,
  listVoiceSuggestions,
  reviewFeedbackForSuggestions,
  updateDraftFeedback,
  updateProfile,
  updateStyle,
} from "@/lib/api";
import type {
  CreatorProfile,
  Draft,
  DraftFormat,
  ImportedPost,
  Platform,
  StyleGuideRevision,
  StyleProfile,
  VoiceSuggestion,
} from "@/types/api";

const samplePosts = `Building a content system is less about posting more and more about making your point impossible to miss.

The best creators do not chase consistency.
They design it.

Your caption should do three jobs:
1. Stop the scroll
2. Make the idea useful
3. Give the reader a next step`;

type StepStatus = "done" | "active" | "locked";
type EditableStyleProfile = Omit<StyleProfile, "creator_id" | "updated_at">;

const emptyStyleForm: EditableStyleProfile = {
  summary: "",
  tone: "",
  hooks: "",
  rhythm: "",
  vocabulary: "",
  emoji_hashtag_habits: "",
  cta_habits: "",
  formatting: "",
  avoid_rules: "",
};

export default function Home() {
  const [profiles, setProfiles] = useState<CreatorProfile[]>([]);
  const [activeId, setActiveId] = useState<number | null>(null);
  const [style, setStyle] = useState<StyleProfile | null>(null);
  const [styleForm, setStyleForm] = useState<EditableStyleProfile>(emptyStyleForm);
  const [draft, setDraft] = useState<Draft | null>(null);
  const [drafts, setDrafts] = useState<Draft[]>([]);
  const [importedPosts, setImportedPosts] = useState<ImportedPost[]>([]);
  const [voiceSuggestions, setVoiceSuggestions] = useState<VoiceSuggestion[]>([]);
  const [styleRevisions, setStyleRevisions] = useState<StyleGuideRevision[]>([]);
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
    source: "manual",
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
    include_hashtags: false,
    show_reuse_warnings: false,
    show_evidence: false,
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
  const canSaveProfile = hasProfile && profileForm.name.trim().length > 0;
  const pendingSuggestions = voiceSuggestions.filter((suggestion) => suggestion.status === "pending");
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
      setStyleForm(styleToForm(data));
    } catch {
      setStyle(null);
      setStyleForm(emptyStyleForm);
    }
  }

  async function refreshWorkspace(creatorId: number) {
    refreshStyle(creatorId);
    refreshImportedPosts(creatorId);
    refreshDrafts(creatorId);
    refreshVoiceLearning(creatorId);
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

  async function refreshVoiceLearning(creatorId: number) {
    try {
      const [suggestions, revisions] = await Promise.all([
        listVoiceSuggestions(creatorId),
        listStyleRevisions(creatorId),
      ]);
      setVoiceSuggestions(suggestions);
      setStyleRevisions(revisions);
    } catch {
      setVoiceSuggestions([]);
      setStyleRevisions([]);
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
      setStyleForm(emptyStyleForm);
      setDraft(null);
      setDrafts([]);
      setImportedPosts([]);
      setVoiceSuggestions([]);
      setStyleRevisions([]);
      setStatus("Creator profile created. Add writing samples next.");
    });
  }

  async function handleUpdateProfile() {
    if (!activeId) return setError("Select a profile before saving changes.");
    runAction(async () => {
      const updated = await updateProfile(activeId, {
        ...profileForm,
        platforms: ["x", "instagram"],
      });
      setProfiles((current) => current.map((profile) => (profile.id === updated.id ? updated : profile)));
      setStatus("Profile details saved.");
    });
  }

  async function handleLoadProfileIntoForm() {
    if (!activeProfile) return setError("Select a profile to load.");
    setProfileForm({
      name: activeProfile.name,
      niche: activeProfile.niche,
      audience: activeProfile.audience,
      goals: activeProfile.goals,
    });
    setStatus("Loaded selected profile into the editor.");
  }

  async function handleClearWorkspace() {
    if (!activeId) return setError("Select a profile before clearing workspace data.");
    const confirmed = window.confirm("Clear imported samples, learned voice profile, drafts, and feedback for this profile?");
    if (!confirmed) return;
    runAction(async () => {
      await clearProfileWorkspace(activeId);
      setStyle(null);
      setStyleForm(emptyStyleForm);
      setDraft(null);
      setDrafts([]);
      setImportedPosts([]);
      setVoiceSuggestions([]);
      setStyleRevisions([]);
      setSelectedVariant({});
      setFeedbackNotes({});
      setStatus("Workspace data cleared for this profile.");
    });
  }

  async function handleDeleteProfile() {
    if (!activeId || !activeProfile) return setError("Select a profile before deleting.");
    const confirmed = window.confirm(`Delete ${activeProfile.name} and all local workspace data?`);
    if (!confirmed) return;
    runAction(async () => {
      await deleteProfile(activeId);
      const remaining = profiles.filter((profile) => profile.id !== activeId);
      setProfiles(remaining);
      setActiveId(remaining[0]?.id ?? null);
      setStyle(null);
      setStyleForm(emptyStyleForm);
      setDraft(null);
      setDrafts([]);
      setImportedPosts([]);
      setVoiceSuggestions([]);
      setStyleRevisions([]);
      setSelectedVariant({});
      setFeedbackNotes({});
      if (remaining[0]) {
        refreshWorkspace(remaining[0].id);
      }
      setStatus("Profile deleted.");
    });
  }

  async function handleImportPosts() {
    if (!activeId) return setError("Create or select a profile first.");
    runAction(async () => {
      const result = await importPosts(activeId, {
        platform: importForm.platform,
        raw_posts: importForm.raw_posts,
        source: importForm.source,
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
      setStyleForm(styleToForm(data));
      setStatus("Voice profile learned. Draft generation is ready.");
    });
  }

  async function handleSaveStyleGuide() {
    if (!activeId) return setError("Select a profile before saving voice edits.");
    if (!style) return setError("Analyze the voice before editing the guide.");
    runAction(async () => {
      const updated = await updateStyle(activeId, styleForm);
      setStyle(updated);
      setStyleForm(styleToForm(updated));
      await refreshVoiceLearning(activeId);
      setStatus("Voice guide saved. Future drafts will use these edited instructions.");
    });
  }

  function handleResetStyleForm() {
    if (!style) return;
    setStyleForm(styleToForm(style));
    setStatus("Voice guide edits reset to the saved profile.");
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

  async function handleReviewFeedbackSuggestions() {
    if (!activeId) return setError("Select a profile before reviewing feedback.");
    if (!style) return setError("Analyze the voice before reviewing feedback.");
    runAction(async () => {
      const suggestions = await reviewFeedbackForSuggestions(activeId);
      setVoiceSuggestions(suggestions);
      setStatus("Feedback reviewed. New voice-guide suggestions are waiting for approval.");
    });
  }

  async function handleSuggestionDecision(suggestionId: number, decision: "accepted" | "dismissed") {
    if (!activeId) return setError("Select a profile before reviewing suggestions.");
    runAction(async () => {
      await decideVoiceSuggestion(activeId, suggestionId, decision);
      await refreshStyle(activeId);
      await refreshVoiceLearning(activeId);
      setStatus(decision === "accepted" ? "Suggestion accepted and added to the voice guide." : "Suggestion dismissed.");
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
    const profile = profiles.find((item) => item.id === profileId);
    setActiveId(profileId);
    setDraft(null);
    if (profile) {
      setProfileForm({
        name: profile.name,
        niche: profile.niche,
        audience: profile.audience,
        goals: profile.goals,
      });
    }
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
            <div className="admin-actions">
              <button className="button" onClick={handleCreateProfile}>
                Create profile
              </button>
              <button className="button secondary" disabled={!canSaveProfile} onClick={handleUpdateProfile}>
                Save selected
              </button>
              <button className="button ghost" disabled={!activeProfile} onClick={handleLoadProfileIntoForm}>
                Load selected
              </button>
            </div>
            <div className="admin-danger-zone">
              <div>
                <strong>Workspace admin</strong>
                <p>Manage local demo data for the selected profile only.</p>
              </div>
              <div className="admin-actions">
                <button className="button ghost" disabled={!activeProfile} onClick={handleClearWorkspace}>
                  Clear workspace
                </button>
                <button className="button danger" disabled={!activeProfile} onClick={handleDeleteProfile}>
                  Delete profile
                </button>
              </div>
            </div>
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
                <span className="section-kicker">Step 04 - Priority workspace</span>
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

            <div className="toggle-grid">
              <label className="toggle-card">
                <input
                  checked={draftForm.include_hashtags}
                  type="checkbox"
                  onChange={(event) =>
                    setDraftForm({ ...draftForm, include_hashtags: event.target.checked })
                  }
                />
                <span>
                  <strong>Include hashtags</strong>
                  <small>User-controlled; off by default to avoid hashtag spam.</small>
                </span>
              </label>
              <label className="toggle-card">
                <input
                  checked={draftForm.show_reuse_warnings}
                  type="checkbox"
                  onChange={(event) =>
                    setDraftForm({ ...draftForm, show_reuse_warnings: event.target.checked })
                  }
                />
                <span>
                  <strong>Show reuse warnings</strong>
                  <small>Detects captions that may be too close to imported samples.</small>
                </span>
              </label>
              <label className="toggle-card">
                <input
                  checked={draftForm.show_evidence}
                  type="checkbox"
                  onChange={(event) =>
                    setDraftForm({ ...draftForm, show_evidence: event.target.checked })
                  }
                />
                <span>
                  <strong>Show evidence</strong>
                  <small>Optional notes about the voice traits and samples used.</small>
                </span>
              </label>
            </div>

            <div className="row">
              <button className="button jumbo" disabled={!canGenerateDraft} onClick={handleCreateDraft}>
                Generate draft variants
              </button>
              {!hasProfile && <span className="hint">Create a profile first.</span>}
              {hasProfile && !hasStyle && <span className="hint">Analyze the voice before drafting.</span>}
            </div>

            {draft && (
              <>
                <DraftSafetyPanel draft={draft} />
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
              </>
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
                    setImportForm({
                      ...importForm,
                      platform: event.target.value as Platform,
                      source: event.target.value === "instagram" ? importForm.source : "manual",
                    })
                  }
                >
                  <option value="x">X writing samples</option>
                  <option value="instagram">Instagram captions</option>
                </select>
              </div>
              <div className="field">
                <label>Import format</label>
                <select
                  value={importForm.source}
                  onChange={(event) => setImportForm({ ...importForm, source: event.target.value })}
                >
                  <option value="manual">Manual paste / CSV / JSON</option>
                  <option value="instagram_export" disabled={importForm.platform !== "instagram"}>
                    Instagram export JSON / CSV
                  </option>
                </select>
              </div>
            </div>

            <div className="field">
              <label>Selected profile</label>
              <input value={activeProfile?.name || "None"} readOnly />
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
                  <div className="row between">
                    <span className="tag">{post.platform}</span>
                    <span className={`quality-pill ${qualityTone(post.quality_score)}`}>
                      {post.quality_score}/100
                    </span>
                  </div>
                  <p>{post.text}</p>
                  <div className="quality-tags">
                    {post.quality_labels.slice(0, 3).map((label) => (
                      <span key={label}>{label.replaceAll("_", " ")}</span>
                    ))}
                    {post.quality_warnings.slice(0, 2).map((warning) => (
                      <span className="warning" key={warning}>
                        {warning.replaceAll("_", " ")}
                      </span>
                    ))}
                  </div>
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
                        {draftItem.platform} - {draftItem.draft_format} -{" "}
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
                  <DraftSafetyPanel draft={draftItem} compact />
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

          <section className="studio-card stack">
            <div className="section-heading">
              <div>
                <span className="section-kicker">Voice learning loop</span>
                <h2>Feedback suggestions</h2>
                <p>
                  Turn draft ratings and notes into proposed voice-guide edits. Nothing changes until
                  you approve a suggestion.
                </p>
              </div>
              <span className="status-pill">{pendingSuggestions.length} pending</span>
            </div>

            <div className="row">
              <button className="button secondary" disabled={!hasStyle || !hasDrafts} onClick={handleReviewFeedbackSuggestions}>
                Review feedback
              </button>
              {!hasDrafts && <span className="hint">Generate and rate drafts first.</span>}
              {hasDrafts && !hasStyle && <span className="hint">Analyze the voice before learning from feedback.</span>}
            </div>

            {voiceSuggestions.length === 0 && (
              <div className="empty-state">
                <strong>No suggestions yet</strong>
                <p>Save ratings or notes on drafts, then run feedback review.</p>
              </div>
            )}

            <div className="suggestion-grid">
              {voiceSuggestions.slice(0, 6).map((suggestion) => (
                <article className={`suggestion-card ${suggestion.status}`} key={suggestion.id}>
                  <div className="row between">
                    <span className="tag">{fieldLabel(suggestion.target_field)}</span>
                    <span className={`review-status ${suggestion.status}`}>{suggestion.status}</span>
                  </div>
                  <strong>{suggestion.suggestion}</strong>
                  <p>{suggestion.rationale}</p>
                  {suggestion.status === "pending" && (
                    <div className="row">
                      <button
                        className="button compact secondary"
                        onClick={() => handleSuggestionDecision(suggestion.id, "accepted")}
                      >
                        Accept
                      </button>
                      <button
                        className="button compact ghost"
                        onClick={() => handleSuggestionDecision(suggestion.id, "dismissed")}
                      >
                        Dismiss
                      </button>
                    </div>
                  )}
                </article>
              ))}
            </div>

            {styleRevisions.length > 0 && (
              <div className="revision-strip">
                <strong>Recent guide revisions</strong>
                {styleRevisions.slice(0, 4).map((revision) => (
                  <span key={revision.id}>
                    {revision.reason} · {new Date(revision.created_at).toLocaleString()}
                  </span>
                ))}
              </div>
            )}
          </section>

          <section className="studio-card compact-section" id="voice">
            <div>
              <span className="section-kicker">Voice profile</span>
              <h2>Editable voice guide</h2>
              {!style && <p>Analyze writing samples first, then tune the guide that future drafts use.</p>}
            </div>
            {style && (
              <>
                <div className="voice-editor-grid">
                  <VoiceField
                    label="Summary"
                    value={styleForm.summary}
                    onChange={(value) => setStyleForm({ ...styleForm, summary: value })}
                  />
                  <VoiceField
                    label="Tone"
                    value={styleForm.tone}
                    onChange={(value) => setStyleForm({ ...styleForm, tone: value })}
                  />
                  <VoiceField
                    label="Hooks"
                    value={styleForm.hooks}
                    onChange={(value) => setStyleForm({ ...styleForm, hooks: value })}
                  />
                  <VoiceField
                    label="Rhythm"
                    value={styleForm.rhythm}
                    onChange={(value) => setStyleForm({ ...styleForm, rhythm: value })}
                  />
                  <VoiceField
                    label="Vocabulary"
                    value={styleForm.vocabulary}
                    onChange={(value) => setStyleForm({ ...styleForm, vocabulary: value })}
                  />
                  <VoiceField
                    label="Emoji / Hashtags"
                    value={styleForm.emoji_hashtag_habits}
                    onChange={(value) => setStyleForm({ ...styleForm, emoji_hashtag_habits: value })}
                  />
                  <VoiceField
                    label="CTA habits"
                    value={styleForm.cta_habits}
                    onChange={(value) => setStyleForm({ ...styleForm, cta_habits: value })}
                  />
                  <VoiceField
                    label="Formatting"
                    value={styleForm.formatting}
                    onChange={(value) => setStyleForm({ ...styleForm, formatting: value })}
                  />
                  <VoiceField
                    label="Avoid rules"
                    value={styleForm.avoid_rules}
                    onChange={(value) => setStyleForm({ ...styleForm, avoid_rules: value })}
                  />
                </div>
                <div className="row">
                  <button className="button secondary" onClick={handleSaveStyleGuide}>
                    Save voice guide
                  </button>
                  <button className="button ghost" onClick={handleResetStyleForm}>
                    Reset edits
                  </button>
                  <span className="hint">Manual guardrails override the analyzed profile.</span>
                </div>
              </>
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

function styleToForm(style: StyleProfile): EditableStyleProfile {
  return {
    summary: style.summary,
    tone: style.tone,
    hooks: style.hooks,
    rhythm: style.rhythm,
    vocabulary: style.vocabulary,
    emoji_hashtag_habits: style.emoji_hashtag_habits,
    cta_habits: style.cta_habits,
    formatting: style.formatting,
    avoid_rules: style.avoid_rules,
  };
}

function VoiceField({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <div className="field voice-field">
      <label>{label}</label>
      <textarea value={value} onChange={(event) => onChange(event.target.value)} />
    </div>
  );
}

function fieldLabel(field: string) {
  const labels: Record<string, string> = {
    summary: "Summary",
    tone: "Tone",
    hooks: "Hooks",
    rhythm: "Rhythm",
    vocabulary: "Vocabulary",
    emoji_hashtag_habits: "Emoji / hashtags",
    cta_habits: "CTA habits",
    formatting: "Formatting",
    avoid_rules: "Avoid rules",
  };
  return labels[field] || field;
}

function qualityTone(score: number) {
  if (score >= 75) return "good";
  if (score >= 50) return "review";
  return "weak";
}

function DraftSafetyPanel({ draft, compact = false }: { draft: Draft; compact?: boolean }) {
  const hasWarnings = draft.warnings.length > 0;
  const hasEvidence = draft.evidence.length > 0;
  if (!hasWarnings && !hasEvidence) {
    return null;
  }

  return (
    <div className={`safety-panel ${compact ? "compact" : ""}`}>
      {hasWarnings && (
        <div className="safety-block warning">
          <strong>Reuse warnings</strong>
          {draft.warnings.map((warning, index) => (
            <p key={`${warning.variant_label}-${index}`}>
              {warning.variant_label}: {warning.message}
            </p>
          ))}
        </div>
      )}
      {hasEvidence && (
        <div className="safety-block evidence">
          <strong>Voice evidence</strong>
          {draft.evidence.map((item, index) => (
            <p key={`${item.title}-${index}`}>
              <b>{item.title}:</b> {item.text}
            </p>
          ))}
        </div>
      )}
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
