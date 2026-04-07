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

      {/* ── Highlight banner ───────────────────────── */}
      <div
        className="rounded-3xl p-6 shadow-lg animate-fade-in delay-100 relative overflow-hidden"
        style={{
          background: "linear-gradient(135deg, #ff6b6b 0%, #c77dff 50%, #4d96ff 100%)",
          color: "#fff",
        }}
      >
        {/* decorative circles */}
        <div
          className="absolute -top-6 -right-6 w-28 h-28 rounded-full opacity-20"
          style={{ background: "#fff" }}
        />
        <div
          className="absolute -bottom-4 -left-4 w-20 h-20 rounded-full opacity-15"
          style={{ background: "#ffd93d" }}
        />

        <p className="text-xs font-black uppercase tracking-widest mb-3 opacity-80">
          ✨ Today&apos;s Highlight
        </p>
        <p className="text-lg font-bold leading-relaxed whitespace-pre-wrap relative z-10">
          {stripMarkdown(summary.highlight)}
        </p>
        <p className="text-xs mt-4 opacity-60">
          生成日時: {new Date(summary.generated_at).toLocaleString("ja-JP")}
        </p>
      </div>

      {/* ── Section cards ──────────────────────────── */}
      {summary.sections.map((sec, i) => {
        const accent = ROOM_ACCENT[sec.room_id] ?? { color: "var(--purple)", emoji: "💬" };
        return (
          <div
            key={sec.room_id}
            className={`card hover-pop animate-fade-in delay-${(i + 2) * 100}`}
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
            <div
              className="text-base font-semibold leading-loose whitespace-pre-wrap"
              style={{ color: "#333" }}
            >
              {stripMarkdown(sec.summary)}
            </div>
          </div>
        );
      })}
    </div>
  );
}
