import Link from "next/link";
import { getAllDates, getSummary } from "@/lib/summaries";

const CARD_COLORS = [
  "var(--red)",
  "var(--orange)",
  "var(--yellow)",
  "var(--green)",
  "var(--blue)",
  "var(--purple)",
];

function formatDate(dateStr: string): string {
  const [y, m, d] = dateStr.split("-");
  return `${y}年${Number(m)}月${Number(d)}日`;
}

export default function HistoryPage() {
  const dates = getAllDates();

  if (dates.length === 0) {
    return (
      <div className="text-center py-20 animate-fade-in">
        <p className="text-4xl mb-4">📭</p>
        <p className="text-xl font-bold" style={{ color: "#aaa" }}>
          履歴データがありません。
        </p>
      </div>
    );
  }

  return (
    <div>
      <h1
        className="text-2xl font-black mb-8 deco-line animate-fade-in"
        style={{ fontFamily: "'Poppins', sans-serif" }}
      >
        過去の要約一覧
      </h1>

      <div className="grid gap-4">
        {dates.map((date, i) => {
          const summary = getSummary(date);
          const color = CARD_COLORS[i % CARD_COLORS.length];
          const totalPosts = summary
            ? summary.sections.reduce((s, sec) => s + sec.post_count, 0)
            : null;

          return (
            <Link key={date} href={`/summary/${date}`}>
              <div
                className={`card hover-pop animate-fade-in delay-${Math.min((i + 1) * 100, 600)}`}
                style={{ borderLeft: `5px solid ${color}` }}
              >
                <div className="flex items-center justify-between mb-2">
                  <span
                    className="text-sm font-black px-3 py-1 rounded-full"
                    style={{ background: color + "22", color }}
                  >
                    {formatDate(date)}
                  </span>
                  {totalPosts !== null && (
                    <span
                      className="text-xs font-bold px-2 py-0.5 rounded-full"
                      style={{ background: "#f0f0f0", color: "#888" }}
                    >
                      計 {totalPosts} 件
                    </span>
                  )}
                </div>
                {summary && (
                  <p
                    className="text-sm font-semibold leading-relaxed line-clamp-2 mt-1"
                    style={{ color: "#555" }}
                  >
                    {summary.highlight}
                  </p>
                )}
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
