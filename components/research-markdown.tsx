import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { memo } from "react";

/**
 * Some model answers put an entire digest on one line as "(1) ... (2) ...".
 * Promote only consecutive, explicitly numbered sequences to Markdown lists;
 * leave ordinary prose, dates, figures, citations and existing Markdown alone.
 */
function formatInlineNumberedLists(content: string) {
  let fence: { character: string; length: number } | null = null;
  return content.split("\n").map((line) => {
    const fenceLine = /^\s*(`{3,}|~{3,})/.exec(line);
    if (fenceLine) {
      const marker = fenceLine[1];
      if (!fence) fence = { character: marker[0], length: marker.length };
      else if (marker[0] === fence.character && marker.length >= fence.length) fence = null;
      return line;
    }
    if (fence) return line;
    if (!line.trim() || /^\s*(?:#{1,6}\s|>|```|~~~|[-*+]\s|\|)/.test(line)) return line;

    const marker = /\((\d{1,2})\)\s+|(\d{1,2})\)\s+/g;
    const matches = [...line.matchAll(marker)];
    if (matches.length < 2) return line;

    const numbers = matches.map((match) => Number(match[1] ?? match[2]));
    if (numbers.some((number, index) => number !== index + 1)) return line;

    const intro = line.slice(0, matches[0].index).trim();
    const items = matches.map((match, index) => {
      const start = match.index! + match[0].length;
      const end = matches[index + 1]?.index ?? line.length;
      return line.slice(start, end).trim();
    });

    // Separate a short concluding note that often follows a source-backed digest.
    const finalItem = items.at(-1) ?? "";
    const note = /([.!?。！？])\s+(?=(?:Net|Overall|Bottom line|Takeaway|Caveat|Note):\s)/i.exec(finalItem);
    let trailingNote = "";
    if (note && note.index !== undefined) {
      trailingNote = finalItem.slice(note.index + note[1].length).trim();
      items[items.length - 1] = finalItem.slice(0, note.index + note[1].length).trim();
    }

    const list = items.map((item, index) => `${index + 1}. ${item}`).join("\n");
    return [intro, list, trailingNote].filter(Boolean).join("\n\n");
  }).join("\n");
}

/** Render source-backed prose while preserving facts, citations and punctuation. */
export const ResearchMarkdown = memo(function ResearchMarkdown({ content }: { content: string }) {
  return <div className="markdown-body"><ReactMarkdown skipHtml remarkPlugins={[remarkGfm]} components={{
    a: ({ children, href }) => <a href={href} target="_blank" rel="noopener noreferrer">{children}</a>,
    table: ({ children }) => <div className="research-summary-table"><table>{children}</table></div>,
  }}>{formatInlineNumberedLists(content)}</ReactMarkdown></div>;
});
