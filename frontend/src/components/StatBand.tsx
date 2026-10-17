"use client";

import type { RiskLevel, Stats } from "@/lib/api";
import { formatCount } from "@/lib/format";

type Filter = RiskLevel | null;

const ITEMS: { filter: Filter; label: string; key: keyof Stats; figureClass: string }[] = [
  { filter: null, label: "All transactions", key: "total", figureClass: "text-ink" },
  { filter: "high", label: "High risk", key: "high", figureClass: "text-risk-high" },
  { filter: "medium", label: "Medium risk", key: "medium", figureClass: "text-ink" },
  { filter: "low", label: "Low risk", key: "low", figureClass: "text-ink" },
];

// The stat band doubles as the table filter: each figure is the button that shows those rows.
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
    <section aria-label="Risk summary" className="bg-canvas-blue">
      {/* Container padding + button padding = the page's single left edge (16px phone, 32px wider). */}
      <div className="mx-auto grid max-w-7xl grid-cols-2 sm:px-4 lg:grid-cols-4">
        {ITEMS.map((item) => {
          const selected = active === item.filter;
          const value = stats ? (stats[item.key] as number) : null;
          return (
            <button
              key={item.label}
              type="button"
              aria-pressed={selected}
              onClick={() => onSelect(item.filter)}
              className={`flex flex-col items-start gap-1 px-4 py-6 text-left transition-colors ${
                selected ? "bg-canvas" : "hover:bg-canvas-soft"
              }`}
            >
              <span className={`text-display font-light tabular-nums ${item.figureClass}`}>
                {value === null ? "—" : formatCount(value)}
              </span>
              <span className={`text-caption ${selected ? "text-accent font-medium" : "text-ink-mute"}`}>
                {item.label}
                {selected ? " · showing" : ""}
              </span>
            </button>
          );
        })}
      </div>
    </section>
  );
}
