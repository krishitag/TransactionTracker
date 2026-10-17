"use client";

import { Fragment, useState } from "react";
import type { Transaction, TransactionPage } from "@/lib/api";
import { formatCount, formatDateTime, formatMoney } from "@/lib/format";
import RiskBadge from "./RiskBadge";

const FRAUD_LABEL = { true: "Confirmed fraud", false: "Not fraud", null: "Unknown" } as const;

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
  onPageChange,
}: {
  page: TransactionPage | null;
  loading: boolean;
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
          <tr className="text-left text-caption text-ink-mute">
            {/* On phones the Time column folds into the Merchant cell so Risk stays on screen. */}
            <th scope="col" className="hidden py-3 pl-3 pr-4 font-normal sm:table-cell">Time (UTC)</th>
            <th scope="col" className="py-3 pl-3 pr-3 font-normal sm:pl-0 sm:pr-4">Merchant</th>
            <th scope="col" className="py-3 pr-3 text-right font-normal sm:pr-4">Amount</th>
            <th scope="col" className="py-3 pr-3 font-normal sm:pr-4">Risk</th>
            <th scope="col" className="hidden py-3 pr-3 font-normal sm:table-cell">
              <span className="sr-only">Details</span>
            </th>
          </tr>
        </thead>
        <tbody className={loading ? "opacity-60 transition-opacity" : "transition-opacity"}>
          {page.items.map((txn, index) => {
            const open = openId === txn.id;
            // Rows are separated by alternating tone, not lines (DESIGN.md: tone steps, no rules).
            const tone = index % 2 === 0 ? "bg-canvas" : "bg-canvas-soft";
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
                <tr className={`${tone} align-top hover:bg-canvas-blue`}>
                  <td className="hidden py-3 pl-3 pr-4 text-body tabular-nums text-ink-secondary whitespace-nowrap sm:table-cell">
                    {formatDateTime(txn.trans_time)}
                  </td>
                  <td className="py-3 pl-3 pr-3 sm:pl-0 sm:pr-4">
                    <span translate="no" className="block text-body text-ink">{txn.merchant}</span>
                    <span className="block text-table text-ink-mute">{txn.category_name}</span>
                    <span className="block text-table tabular-nums text-ink-mute whitespace-nowrap sm:hidden">
                      {formatDateTime(txn.trans_time)}
                    </span>
                  </td>
                  <td className="py-3 pr-3 text-right text-body tabular-nums text-ink whitespace-nowrap sm:pr-4">
                    {formatMoney(txn.amount)}
                  </td>
                  <td className="py-3 pr-3 whitespace-nowrap sm:pr-4">
                    <RiskBadge level={txn.risk_level} />
                    <span className="ml-2 hidden tabular-nums text-ink-mute sm:inline">
                      {txn.risk_score.toFixed(2)}
                    </span>
                    {whyButton("-ml-3 mt-1 block sm:hidden")}
                  </td>
                  <td className="hidden py-2 pr-3 text-right sm:table-cell">{whyButton("")}</td>
                </tr>
                {open && (
                  <tr id={`reasons-${txn.id}`} className="bg-accent-wash">
                    <td colSpan={5} className="px-3 py-4">
                      <Reasons txn={txn} />
                    </td>
                  </tr>
                )}
              </Fragment>
            );
          })}
        </tbody>
      </table>

      {page.total === 0 && <p className="py-10 text-body text-ink-mute">No transactions match this filter.</p>}

      <nav aria-label="Pagination" className="flex items-center justify-between gap-4 py-4">
        <p className="text-caption text-ink-mute tabular-nums">
          {formatCount(first)}–{formatCount(last)} of {formatCount(page.total)}
        </p>
        <div className="flex gap-2">
          <button
            type="button"
            disabled={page.offset === 0 || loading}
            onClick={() => onPageChange(Math.max(0, page.offset - page.limit))}
            className="min-h-10 rounded-full bg-canvas-blue px-4 text-caption font-medium text-ink hover:bg-accent-wash disabled:opacity-40"
          >
            Previous
          </button>
          <button
            type="button"
            disabled={last >= page.total || loading}
            onClick={() => onPageChange(page.offset + page.limit)}
            className="min-h-10 rounded-full bg-canvas-blue px-4 text-caption font-medium text-ink hover:bg-accent-wash disabled:opacity-40"
          >
            Next
          </button>
        </div>
      </nav>
    </div>
  );
}
