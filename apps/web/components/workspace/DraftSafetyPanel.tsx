import type { Draft } from "@/types/api";

export function DraftSafetyPanel({ draft, compact = false }: { draft: Draft; compact?: boolean }) {
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
