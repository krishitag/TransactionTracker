"use client";

import { Fragment, useState } from "react";
import type { RiskLevel, Transaction, TransactionPage } from "@/lib/api";
import { formatCount, formatDateTime, formatMoney } from "@/lib/format";
import RiskBadge from "./RiskBadge";

const FRAUD_LABEL = { true: "Confirmed fraud", false: "Not fraud", null: "Unknown" } as const;

// The header row takes the colour of the selected stat card (all = blue). Full class names so
// Tailwind generates them.
const HEADER_TONE = {
  all: "border-blue-200 bg-blue-100",
  high: "border-risk-high/30 bg-risk-high-wash",
  medium: "border-risk-medium/30 bg-risk-medium-wash",
  low: "border-low-green/30 bg-low-green-wash",
} as const;

export function Reasons({ txn }: { txn: Transaction }) {
  return (
    <div className="flex flex-col gap-2">
      <ul className="list-disc space-y-1 pl-5 text-body text-ink">
        {txn.reasons.map((reason) => (
          <li key={reason}>{reason}</li>
        ))}
      </ul>
      <p className="text-caption text-ink-mute">
        Risk score {txn.risk_score.toFixed(2)} (relative, not a probability) · Label in dataset:{" "}
        {FRAUD_LABEL[String(txn.is_fraud) as keyof typeof FRAUD_LABEL]} · Card ending {txn.card_last4} ·
        Model <span translate="no">{txn.model_version}</span>
      </p>
    </div>
  );
}

export default function TransactionTable({
  page,
  loading,
  filter,
  onPageChange,
}: {
  page: TransactionPage | null;
  loading: boolean;
  filter: RiskLevel | null;
  onPageChange: (offset: number) => void;
}) {
  const [openId, setOpenId] = useState<number | null>(null);

  if (!page) {
    return <p className="px-2 py-10 text-body text-ink-mute">{loading ? "Loading transactions…" : ""}</p>;
  }

  const first = page.total === 0 ? 0 : page.offset + 1;
  const last = Math.min(page.offset + page.limit, page.total);

  return (
    <div aria-busy={loading}>
      <table className="w-full border-collapse text-table">
        <caption className="sr-only">Scored transactions, newest first</caption>
        <thead>
          <tr className={`border-b ${HEADER_TONE[filter ?? "all"]} text-left text-caption font-medium text-ink-secondary`} /* taste-skill-ignore: lines inside a real table */>
            {/* On phones the Time column folds into the Merchant cell so Risk stays on screen. */}
            <th scope="col" className="hidden py-3 pl-4 pr-4 font-medium sm:table-cell">Time (UTC)</th>
            <th scope="col" className="py-3 pl-4 pr-3 font-medium sm:pl-0 sm:pr-4">Merchant</th>
            <th scope="col" className="py-3 pr-3 text-right font-medium sm:pr-4">Amount</th>
            <th scope="col" className="py-3 pr-3 font-medium sm:pr-4">Risk</th>
            <th scope="col" className="hidden py-3 pr-4 font-medium sm:table-cell">
              <span className="sr-only">Details</span>
            </th>
          </tr>
        </thead>
        <tbody className={loading ? "opacity-60 transition-opacity" : "transition-opacity"}>
          {page.items.map((txn, index) => {
            const open = openId === txn.id;
            // Alternating white / light blue plus a thin blue line, so rows read apart (DESIGN.md D9d).
            const tone = index % 2 === 0 ? "bg-canvas" : "bg-blue-50";
            // Rendered in its own column from sm up, and under the badge on phones (one is
            // display:none at any width, so screen readers only ever meet one).
            const whyButton = (className: string) => (
              <button
                type="button"
                aria-expanded={open}
                aria-controls={`reasons-${txn.id}`}
                onClick={() => setOpenId(open ? null : txn.id)}
                className={`min-h-10 rounded-full px-3 text-table font-medium text-accent hover:bg-accent-wash ${className}`}
              >
                {open ? "Hide" : "Why?"}
                <span className="sr-only"> risk reasons for transaction {txn.id}</span>
              </button>
            );
            return (
              <Fragment key={txn.id}>
                <tr className={`${tone} border-b border-blue-100 align-top hover:bg-blue-100`} /* taste-skill-ignore: real table */>
                  <td className="hidden py-3 pl-4 pr-4 text-body tabular-nums text-ink-secondary whitespace-nowrap sm:table-cell">
                    {formatDateTime(txn.trans_time)}
                  </td>
                  <td className="py-3 pl-4 pr-3 sm:pl-0 sm:pr-4">
                    <span translate="no" className="block text-body text-ink">{txn.merchant}</span>
                    <span className="block text-table text-ink-mute">{txn.category_name}</span>
                    <span className="block text-table tabular-nums text-ink-mute whitespace-nowrap sm:hidden">
                      {formatDateTime(txn.trans_time)}
                    </span>
                  </td>
                  <td className="py-3 pr-3 text-right text-body font-medium tabular-nums text-ink whitespace-nowrap sm:pr-4">
                    {formatMoney(txn.amount)}
                  </td>
                  <td className="py-3 pr-3 whitespace-nowrap sm:pr-4">
                    <RiskBadge level={txn.risk_level} />
                    <span className="ml-2 hidden tabular-nums text-ink-mute sm:inline">
                      {txn.risk_score.toFixed(2)}
                    </span>
                    {whyButton("-ml-3 mt-1 block sm:hidden")}
                  </td>
                  <td className="hidden py-2 pr-4 text-right sm:table-cell">{whyButton("")}</td>
                </tr>
                {open && (
                  <tr id={`reasons-${txn.id}`} className="border-b border-blue-200 bg-accent-wash" /* taste-skill-ignore: real table */>
                    <td colSpan={5} className="px-4 py-4">
                      <Reasons txn={txn} />
                    </td>
                  </tr>
                )}
              </Fragment>
            );
          })}
        </tbody>
      </table>

      {page.total === 0 && <p className="px-4 py-10 text-body text-ink-mute">No transactions match this filter.</p>}

      <nav aria-label="Pagination" className="flex items-center justify-between gap-4 px-4 py-3">
        <p className="text-caption text-ink-mute tabular-nums">
          {formatCount(first)}–{formatCount(last)} of {formatCount(page.total)}
        </p>
        <div className="flex gap-2">
          <button
            type="button"
            disabled={page.offset === 0 || loading}
            onClick={() => onPageChange(Math.max(0, page.offset - page.limit))}
            className="min-h-10 rounded-full bg-blue-100 px-4 text-caption font-medium text-ink hover:bg-blue-200 active:bg-blue-300 disabled:opacity-40"
          >
            Previous
          </button>
          <button
            type="button"
            disabled={last >= page.total || loading}
            onClick={() => onPageChange(page.offset + page.limit)}
            className="min-h-10 rounded-full bg-blue-100 px-4 text-caption font-medium text-ink hover:bg-blue-200 active:bg-blue-300 disabled:opacity-40"
          >
            Next
          </button>
        </div>
      </nav>
    </div>
  );
}
