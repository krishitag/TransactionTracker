"use client";

import type { RiskLevel, Stats } from "@/lib/api";
import { formatCount, formatMoneyWhole, formatPercent } from "@/lib/format";

type Filter = RiskLevel | null;

// Each card is tinted by what it counts: hover = a faint fill and soft border, selected = the
// full tint, a 2px border in the card's colour and "Showing" (so state never relies on colour alone).
// Class names are written out in full because Tailwind only generates classes it can see.
const ITEMS: {
  filter: Filter;
  label: string;
  key: "total" | "high" | "medium" | "low";
  figureClass: string;
  hover: string;
  selected: string;
  selectedText: string;
}[] = [
  {
    filter: null,
    label: "All transactions",
    key: "total",
    figureClass: "text-ink",
    hover: "hover:border-accent/50 hover:bg-blue-50",
    selected: "border-accent bg-accent-wash",
    selectedText: "text-accent",
  },
  {
    filter: "high",
    label: "High risk",
    key: "high",
    figureClass: "text-risk-high",
    hover: "hover:border-risk-high/50 hover:bg-risk-high-wash/60",
    selected: "border-risk-high bg-risk-high-wash",
    selectedText: "text-risk-high",
  },
  {
    filter: "medium",
    label: "Medium risk",
    key: "medium",
    figureClass: "text-risk-medium",
    hover: "hover:border-risk-medium/50 hover:bg-risk-medium-wash/60",
    selected: "border-risk-medium bg-risk-medium-wash",
    selectedText: "text-risk-medium",
  },
  {
    filter: "low",
    label: "Low risk",
    key: "low",
    figureClass: "text-risk-low",
    hover: "hover:border-risk-low/50 hover:bg-risk-low-wash/60",
    selected: "border-risk-low bg-risk-low-wash",
    selectedText: "text-risk-low",
  },
];

// The stat cards double as the table filter: each card is the button that shows those rows.
export default function StatBand({
  stats,
  active,
  onSelect,
}: {
  stats: Stats | null;
  active: Filter;
  onSelect: (filter: Filter) => void;
}) {
  return (
    <section aria-label="Risk summary" className="px-4 pt-6 sm:px-8">
      <div className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
        {ITEMS.map((item) => {
          const selected = active === item.filter;
          const value = stats ? stats[item.key] : null;
          const detail = !stats
            ? "…"
            : item.key === "total"
              ? `${formatMoneyWhole(stats.total_amount)} in total`
              : `${formatPercent(stats[item.key], stats.total)} of all`;
          return (
            <button
              key={item.label}
              type="button"
              aria-pressed={selected}
              onClick={() => onSelect(item.filter)}
              className={`flex flex-col items-start gap-1 rounded-xl border-2 p-4 text-left transition-colors sm:p-5 ${
                selected ? item.selected : `border-blue-100 bg-canvas ${item.hover}`
              }`}
            >
              <span className="flex w-full items-baseline justify-between gap-2 text-caption">
                <span className={selected ? `font-medium ${item.selectedText}` : "text-ink-secondary"}>{item.label}</span>
                {selected && <span className={`font-medium ${item.selectedText}`}>Showing</span>}
              </span>
              <span className={`text-display tabular-nums ${item.figureClass}`}>
                {value === null ? "—" : formatCount(value)}
              </span>
              <span className="text-caption tabular-nums text-ink-mute">{detail}</span>
            </button>
          );
        })}
      </div>
    </section>
  );
}
