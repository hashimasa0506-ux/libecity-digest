import { getLatestSummary } from "@/lib/summaries";
import SummaryView from "@/components/SummaryView";

export default function HomePage() {
  const summary = getLatestSummary();

  if (!summary) {
    return (
      <div className="text-center py-20 text-gray-400">
        <p className="text-xl">まだ要約データがありません。</p>
        <p className="text-sm mt-2">GitHub Actions が実行されると自動的に表示されます。</p>
      </div>
    );
  }

  return <SummaryView summary={summary} />;
}
