import type { StepStatus } from "./types";

export function WizardStep({
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
