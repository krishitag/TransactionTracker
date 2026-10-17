"use client";

import { useEffect, useRef, useState } from "react";
import { ask, getTransaction, type AskResponse, type Transaction } from "@/lib/api";
import { formatDateTime, formatMoney } from "@/lib/format";
import AnswerText from "./AnswerText";
import RiskBadge from "./RiskBadge";
import { Reasons } from "./TransactionTable";

const ASK_TIMEOUT_MS = 60_000;

const EXAMPLES = [
  "Which spending categories have the most high-risk transactions?",
  "Show me suspicious late-night online shopping purchases",
  "Why were the high-risk transactions flagged?",
];

export default function AskPanel() {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<AskResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [cited, setCited] = useState<Transaction | null>(null);
  const [citedError, setCitedError] = useState<string | null>(null);
  const controller = useRef<AbortController | null>(null);
  const citedRef = useRef<HTMLDivElement>(null);

  useEffect(() => () => controller.current?.abort(), []);

  async function submit(q: string) {
    const text = q.trim();
    if (pending) return;
    if (text.length < 3) {
      setError("Type a question of at least 3 characters, or pick one of the examples above.");
      return;
    }
    controller.current?.abort();
    const current = new AbortController();
    controller.current = current;
    // Safety net: never leave "Thinking…" on screen forever.
    const timer = setTimeout(
      () => current.abort(new DOMException("No answer in time", "TimeoutError")),
      ASK_TIMEOUT_MS,
    );
    setQuestion(text);
    setPending(true);
    setError(null);
    setCited(null);
    try {
      setResult(await ask(text, current.signal));
    } catch (e) {
      if (e instanceof DOMException && e.name === "AbortError") return;
      setResult(null);
      if (e instanceof DOMException && e.name === "TimeoutError") {
        setError(`No answer after ${ASK_TIMEOUT_MS / 1000} seconds. The AI service may be busy; try again.`);
      } else {
        setError(e instanceof Error ? e.message : "Something went wrong.");
      }
    } finally {
      clearTimeout(timer);
      if (controller.current === current) setPending(false);
    }
  }

  async function openCitation(id: number) {
    setCitedError(null);
    try {
      setCited(await getTransaction(id));
      requestAnimationFrame(() => citedRef.current?.focus());
    } catch (e) {
      setCitedError(e instanceof Error ? e.message : "Could not load that transaction.");
    }
  }

  const validIds = new Set(result?.citations.map((c) => c.id) ?? []);

  return (
    <section id="ask" aria-labelledby="ask-heading" className="flex scroll-mt-4 flex-col gap-4 bg-canvas-soft p-6">
      <div>
        <h2 id="ask-heading" className="text-heading text-ink text-balance">Ask about these transactions</h2>
        <p className="mt-1 max-w-[60ch] text-body text-ink-secondary">
          Answers use only the data here and cite transaction numbers you can open.
        </p>
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          submit(question);
        }}
        className="flex flex-col gap-3"
      >
        <label htmlFor="question" className="sr-only">Question</label>
        <textarea
          id="question"
          name="question"
          autoComplete="off"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              submit(question);
            }
          }}
          rows={3}
          maxLength={500}
          placeholder="Ask about merchants, categories, times…"
          className="w-full resize-none rounded-[6px] border border-hairline bg-canvas px-3 py-2 text-body text-ink placeholder:text-ink-mute focus:border-accent"
        />
        <button
          type="submit"
          disabled={pending}
          className="min-h-10 self-start rounded-full bg-accent px-5 text-body font-medium text-white transition-colors hover:bg-accent-press active:bg-accent-press disabled:opacity-50"
        >
          {pending ? "Thinking…" : "Ask"}
        </button>
      </form>

      {/* Kept visible next to an error too: the error text points to these examples. */}
      {!result && !pending && (
        <div className="flex flex-col gap-2">
          <p className="text-caption text-ink-mute">Try one of these:</p>
          {EXAMPLES.map((q) => (
            <button
              key={q}
              type="button"
              onClick={() => submit(q)}
              className="min-h-10 rounded-full bg-canvas px-4 py-2 text-left text-table text-ink-secondary hover:bg-accent-wash hover:text-accent"
            >
              {q}
            </button>
          ))}
        </div>
      )}

      <div aria-live="polite" aria-busy={pending} className="flex flex-col gap-4">
        {pending && <p className="text-body text-ink-mute">Searching the data and writing an answer. This can take 10–20 seconds.</p>}
        {error && <p role="alert" className="text-body text-risk-high">{error}</p>}
        {result && !pending && (
          <div className="flex flex-col gap-3 bg-accent-wash p-4">
            <AnswerText text={result.answer} onCite={openCitation} validIds={validIds} />
            <p className="text-caption text-ink-mute">
              {describeFilters(result)} · {result.examples_retrieved} transactions examined · {result.model}
              {result.removed_invalid_citations.length > 0 &&
                ` · ${result.removed_invalid_citations.length} unsupported citation(s) removed`}
            </p>
          </div>
        )}
      </div>

      {citedError && <p role="alert" className="text-body text-risk-high">{citedError}</p>}
      {cited && (
        <div
          ref={citedRef}
          tabIndex={-1}
          aria-label={`Transaction ${cited.id}`}
          className="flex flex-col gap-3 bg-canvas p-4"
        >
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <p className="text-body font-medium text-ink">
              #{cited.id} · <span translate="no">{cited.merchant}</span>
            </p>
            <RiskBadge level={cited.risk_level} />
          </div>
          <p className="text-table tabular-nums text-ink-secondary">
            {formatMoney(cited.amount)} · {cited.category_name} · {formatDateTime(cited.trans_time)} UTC
          </p>
          <Reasons txn={cited} />
          <button
            type="button"
            onClick={() => setCited(null)}
            className="min-h-10 self-start rounded-full px-3 text-caption font-medium text-accent hover:bg-accent-wash"
          >
            Close
          </button>
        </div>
      )}
    </section>
  );
}

function describeFilters(r: AskResponse) {
  const parts = [
    r.filters.risk_level && `${r.filters.risk_level} risk`,
    r.filters.time_of_day,
    r.filters.categories?.length && r.filters.categories.join(", ").replaceAll("_", " "),
  ].filter(Boolean);
  if (!parts.length) return "No filters";
  return `${r.filters_relaxed ? "No exact matches for" : "Filtered to"} ${parts.join(" · ")}`;
}
