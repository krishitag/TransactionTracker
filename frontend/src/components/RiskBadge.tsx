import type { RiskLevel } from "@/lib/api";

const STYLES: Record<RiskLevel, string> = {
  high: "bg-risk-high-wash text-risk-high",
  medium: "bg-risk-medium-wash text-risk-medium",
  low: "bg-risk-low-wash text-risk-low",
};

const LABELS: Record<RiskLevel, string> = { high: "High", medium: "Medium", low: "Low" };

// Risk is never shown by colour alone: the badge always carries its word.
export default function RiskBadge({ level }: { level: RiskLevel }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-table font-medium ${STYLES[level]}`}
    >
      {LABELS[level]}
    </span>
  );
}
