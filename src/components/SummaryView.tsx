import Link from "next/link";
import type { Summary } from "@/lib/summaries";

/* ── Room accent colors (CSS variable names) ───────────── */
const ROOM_ACCENT: Record<string, { color: string; emoji: string }> = {
  "President-Tweet": { color: "var(--orange)", emoji: "📰" },
  "LIVE-Text":       { color: "var(--blue)",   emoji: "🎙️" },
  "Liberal-City":    { color: "var(--green)",  emoji: "🏙️" },
};

function formatDate(dateStr: string): string {
  const [y, m, d] = dateStr.split("-");
  return `${y}年${Number(m)}月${Number(d)}日`;
}

function stripMarkdown(text: string): string {
  return text
    .replace(/\*\*(.+?)\*\*/g, "$1")
    .replace(/\*(.+?)\*/g, "$1")
    .replace(/`(.+?)`/g, "$1")
    .replace(/^#{1,6}\s+/gm, "")
    .replace(/^\s*[-*]\s+/gm, "・")
    .trim();
}

export default function SummaryView({ summary }: { summary: Summary }) {
  return (
    <div className="space-y-6">

      {/* ── Header ─────────────────────────────────── */}
      <div className="flex items-center justify-between animate-fade-in">
        <h1
          className="text-2xl font-black deco-line"
          style={{ fontFamily: "'Poppins', sans-serif" }}
        >
          {formatDate(summary.date)}
        </h1>
        <Link href="/history" className="btn-shimmer">
          履歴一覧 →
        </Link>
      </div>

      {/* ── Section cards ──────────────────────────── */}
      {summary.sections.map((sec, i) => {
        const accent = ROOM_ACCENT[sec.room_id] ?? { color: "var(--purple)", emoji: "💬" };
        return (
          <div
            key={sec.room_id}
            className={`card hover-pop animate-fade-in delay-${(i + 1) * 100}`}
            style={{ borderTop: `5px solid ${accent.color}` }}
          >
            {/* card header */}
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-black flex items-center gap-2" style={{ color: "#1a1a2e" }}>
                <span
                  className="text-2xl w-10 h-10 flex items-center justify-center rounded-xl"
                  style={{ background: accent.color + "22" }}
                >
                  {accent.emoji}
                </span>
                {sec.title}
              </h2>
              <span
                className="text-xs font-black px-3 py-1 rounded-full"
                style={{ background: accent.color + "22", color: accent.color }}
              >
                {sec.post_count} 件
              </span>
            </div>

            {/* divider */}
            <div
              className="h-0.5 rounded-full mb-4"
              style={{
                background: `linear-gradient(90deg, ${accent.color}88, transparent)`,
              }}
            />

            {/* summary text */}
            <div className="space-y-1">
              {stripMarkdown(sec.summary)
                .split("\n")
                .filter((line) => line.trim() !== "")
                .map((line, j) => (
                  <p key={j} className="text-base font-semibold leading-relaxed" style={{ color: "#333" }}>
                    {line}
                  </p>
                ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
