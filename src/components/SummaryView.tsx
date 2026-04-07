import Link from "next/link";
import type { Summary } from "@/lib/summaries";

const ROOM_COLORS: Record<string, string> = {
  "President-Tweet": "border-amber-400 bg-amber-50",
  "LIVE-Text":       "border-sky-400  bg-sky-50",
  "Liberal-City":    "border-emerald-400 bg-emerald-50",
};

const ROOM_BADGE: Record<string, string> = {
  "President-Tweet": "bg-amber-100 text-amber-800",
  "LIVE-Text":       "bg-sky-100   text-sky-800",
  "Liberal-City":    "bg-emerald-100 text-emerald-800",
};

function formatDate(dateStr: string): string {
  const [y, m, d] = dateStr.split("-");
  return `${y}年${Number(m)}月${Number(d)}日`;
}

export default function SummaryView({ summary }: { summary: Summary }) {
  return (
    <div className="space-y-6">
      {/* ヘッダー */}
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-900">
          {formatDate(summary.date)}
        </h1>
        <Link href="/history" className="text-sm text-indigo-600 hover:underline">
          履歴一覧 →
        </Link>
      </div>

      {/* ハイライトバナー */}
      <div className="bg-gradient-to-r from-indigo-600 to-violet-600 text-white rounded-2xl p-5 shadow-md">
        <p className="text-xs font-semibold uppercase tracking-widest mb-2 opacity-80">
          Today&apos;s Highlight
        </p>
        <p className="text-lg leading-relaxed whitespace-pre-wrap">{summary.highlight}</p>
        <p className="text-xs mt-3 opacity-60">
          生成日時: {new Date(summary.generated_at).toLocaleString("ja-JP")}
        </p>
      </div>

      {/* セクションカード */}
      {summary.sections.map((sec) => (
        <div
          key={sec.room_id}
          className={`rounded-2xl border-2 p-5 ${ROOM_COLORS[sec.room_id] ?? "border-gray-300 bg-white"}`}
        >
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-base font-bold text-gray-800">{sec.title}</h2>
            <span
              className={`text-xs font-medium px-2.5 py-0.5 rounded-full ${ROOM_BADGE[sec.room_id] ?? "bg-gray-100 text-gray-700"}`}
            >
              {sec.post_count} 件
            </span>
          </div>
          <div className="text-base text-gray-700 leading-relaxed whitespace-pre-wrap">
            {sec.summary}
          </div>
        </div>
      ))}
    </div>
  );
}
