import Link from "next/link";
import { getAllDates, getSummary } from "@/lib/summaries";

export default function HistoryPage() {
  const dates = getAllDates();

  if (dates.length === 0) {
    return (
      <div className="text-center py-20 text-gray-400">
        <p className="text-xl">履歴データがありません。</p>
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">過去の要約一覧</h1>
      <div className="grid gap-4">
        {dates.map((date) => {
          const summary = getSummary(date);
          return (
            <Link key={date} href={`/summary/${date}`}>
              <div className="bg-white rounded-xl border border-gray-200 p-4 hover:border-indigo-400 hover:shadow-md transition-all cursor-pointer">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-semibold text-indigo-700 bg-indigo-50 px-3 py-1 rounded-full">
                    {date}
                  </span>
                  <span className="text-xs text-gray-400">
                    {summary
                      ? summary.sections.reduce((s, sec) => s + sec.post_count, 0) + " 件"
                      : ""}
                  </span>
                </div>
                {summary && (
                  <p className="text-sm text-gray-600 line-clamp-2">{summary.highlight}</p>
                )}
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
