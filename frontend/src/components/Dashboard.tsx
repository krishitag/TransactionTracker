"use client";

import { useEffect, useState } from "react";
import { getStats, getTransactions, type RiskLevel, type Stats, type TransactionPage } from "@/lib/api";
import { formatCount, formatMoneyWhole, formatPercent } from "@/lib/format";
import AskPanel from "./AskPanel";
import StatBand from "./StatBand";
import TransactionTable from "./TransactionTable";

const PAGE_SIZE = 20;
const WAKING_NOTICE_AFTER_MS = 4000;

// The line under the table title describes the rows on screen: the high-risk share for "All",
// otherwise the selected group's own count and money.
function summaryLine(stats: Stats, filter: RiskLevel | null) {
  if (!filter) {
    return `${formatMoneyWhole(stats.high_risk_amount)} of ${formatMoneyWhole(stats.total_amount)} (${formatPercent(
      stats.high_risk_amount,
      stats.total_amount,
    )}) sits in high-risk transactions.`;
  }
  const amount = stats[`${filter}_risk_amount`] as number | undefined;
  // An older backend has no per-group amounts: show the count rather than "$NaN".
  if (amount === undefined) return `${formatCount(stats[filter])} ${filter}-risk transactions.`;
  return `${formatCount(stats[filter])} transactions worth ${formatMoneyWhole(amount)}, ${formatPercent(
    amount,
    stats.total_amount,
  )} of all money.`;
}

export default function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [filter, setFilter] = useState<RiskLevel | null>(null);
  const [offset, setOffset] = useState(0);
  // Each result remembers which filter+page it belongs to, so "loading" is simply
  // "the data on screen is for a different request" (no setState inside the effect).
  const [loaded, setLoaded] = useState<{ key: string; page: TransactionPage } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const requestKey = `${filter ?? "all"}:${offset}`;
  const loading = loaded?.key !== requestKey && !error;

  // The free backend host sleeps when idle and takes about a minute to wake. If the first
  // answer is slow, say so, rather than showing an empty page that looks broken.
  const [slowStart, setSlowStart] = useState(false);
  const waking = slowStart && !stats && !error;

  useEffect(() => {
    const controller = new AbortController();
    const timer = setTimeout(() => setSlowStart(true), WAKING_NOTICE_AFTER_MS);
    getStats(controller.signal)
      .then(setStats)
      .catch((e) => e.name !== "AbortError" && setError(e.message))
      .finally(() => clearTimeout(timer));
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, []);

  // Refetch the table whenever the filter or page changes; abort the previous request
  // so a slow old response can never overwrite a newer one.
  useEffect(() => {
    const controller = new AbortController();
    const key = `${filter ?? "all"}:${offset}`;
    getTransactions({ riskLevel: filter, limit: PAGE_SIZE, offset }, controller.signal)
      .then((page) => setLoaded({ key, page }))
      .catch((e) => e.name !== "AbortError" && setError(e.message));
    return () => controller.abort();
  }, [filter, offset]);

  function selectFilter(next: RiskLevel | null) {
    setError(null);
    setFilter(next);
    setOffset(0);
  }

  function changePage(next: number) {
    setError(null);
    setOffset(next);
  }

  return (
    <div className="flex flex-1 flex-col">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-10 focus:rounded-full focus:bg-canvas focus:px-4 focus:py-2 focus:text-accent"
      >
        Skip to transactions
      </a>
      <header className="bg-navy-900 text-white">
        <div className="flex flex-wrap items-baseline justify-between gap-2 px-4 py-5 sm:px-8">
          <h1 className="text-heading font-normal text-balance">Transaction Risk Monitor</h1>
          {/* On narrower screens the ask panel sits below the table; give it a first-screen action. */}
          <a
            href="#ask"
            className="inline-flex min-h-11 items-center rounded-full bg-accent px-5 text-body font-medium text-white hover:bg-accent-press lg:hidden"
          >
            Ask a question
          </a>
          <p className="w-full text-body text-white/90 lg:w-auto">
            Model <span translate="no" className="tabular-nums">{stats?.model_version ?? "…"}</span> · scores are relative risk, not
            probabilities
          </p>
        </div>
      </header>

      {waking && (
        <p role="status" className="mx-4 mt-6 rounded-xl bg-accent-wash px-5 py-4 text-body text-ink sm:mx-8">
          Waking up the server. This demo runs on free hosting that sleeps when idle, so the first load takes
          about a minute. The data appears here on its own.
        </p>
      )}

      <StatBand stats={stats} active={filter} onSelect={selectFilter} />

      {/* Full width: the table takes the space, the ask panel is a fixed column on the right edge. */}
      <main id="main" className="grid w-full flex-1 gap-6 px-4 py-6 sm:px-8 lg:grid-cols-[minmax(0,1fr)_420px]">
        {/* The table is a white card whose title sits inside it, level with the ask panel's title. */}
        <section aria-labelledby="table-heading" className="min-w-0 self-start overflow-hidden rounded-xl border border-blue-200 bg-canvas">
          <div className="px-4 py-4">
            <h2 id="table-heading" className="text-heading text-ink text-balance">
              {filter ? `${filter[0].toUpperCase()}${filter.slice(1)}-risk transactions` : "All transactions"}
            </h2>
            {stats && <p className="mt-1 max-w-[60ch] text-body text-ink-secondary">{summaryLine(stats, filter)}</p>}
            {error && (
              <p role="alert" className="mt-4 bg-risk-high-wash px-4 py-3 text-body text-risk-high">
                {error}
              </p>
            )}
          </div>
          <div className="overflow-x-auto">
            <TransactionTable page={loaded?.page ?? null} loading={loading} filter={filter} onPageChange={changePage} />
          </div>
        </section>

        <aside className="lg:sticky lg:top-6 lg:self-start">
          <AskPanel total={stats?.total} />
        </aside>
      </main>
    </div>
  );
}
