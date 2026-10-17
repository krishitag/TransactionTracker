import { Fragment, type ReactNode } from "react";

// Renders the LLM's answer, which is untrusted text. Only a tiny subset of markdown is
// understood (headings, bullets, **bold**) plus [#123] citations, and everything is built
// as React elements, never injected as HTML, so text from the data can't become markup.

const INLINE = /(\*\*[^*]+\*\*|\[#\d+\])/g;

function renderInline(text: string, onCite: (id: number) => void, validIds: Set<number>): ReactNode[] {
  return text.split(INLINE).map((part, i) => {
    const bold = part.match(/^\*\*([^*]+)\*\*$/);
    if (bold) return <strong key={i} className="font-semibold">{bold[1]}</strong>;
    const cite = part.match(/^\[#(\d+)\]$/);
    if (cite) {
      const id = Number(cite[1]);
      if (!validIds.has(id)) return <Fragment key={i}>{part}</Fragment>;
      return (
        <button
          key={i}
          type="button"
          onClick={() => onCite(id)}
          aria-label={`Open transaction ${id}`}
          className="-mx-1 rounded-full px-1 font-medium text-accent tabular-nums hover:bg-canvas hover:text-accent-press"
        >
          #{id}
        </button>
      );
    }
    return <Fragment key={i}>{part.replace(/(^|\s)\*(?=\S)|(?<=\S)\*(\s|$)/g, "$1$2")}</Fragment>;
  });
}

export default function AnswerText({
  text,
  onCite,
  validIds,
}: {
  text: string;
  onCite: (id: number) => void;
  validIds: Set<number>;
}) {
  const blocks: ReactNode[] = [];
  let bullets: string[] = [];

  const flushBullets = () => {
    if (!bullets.length) return;
    blocks.push(
      <ul key={`ul-${blocks.length}`} className="list-disc space-y-1 pl-5">
        {bullets.map((b, i) => (
          <li key={i}>{renderInline(b, onCite, validIds)}</li>
        ))}
      </ul>,
    );
    bullets = [];
  };

  for (const raw of text.split("\n")) {
    const line = raw.trim();
    const bullet = line.match(/^(?:[*-]|\d+\.)\s+(.*)$/);
    if (bullet) {
      bullets.push(bullet[1]);
      continue;
    }
    flushBullets();
    if (!line) continue;
    const heading = line.match(/^#{1,6}\s+(.*)$/);
    if (heading) {
      blocks.push(
        <p key={blocks.length} className="pt-1 font-semibold text-ink">
          {renderInline(heading[1], onCite, validIds)}
        </p>,
      );
    } else {
      blocks.push(<p key={blocks.length}>{renderInline(line, onCite, validIds)}</p>);
    }
  }
  flushBullets();

  return <div className="flex flex-col gap-3 text-body text-ink">{blocks}</div>;
}
