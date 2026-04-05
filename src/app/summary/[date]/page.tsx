import { notFound } from "next/navigation";
import { getAllDates, getSummary } from "@/lib/summaries";
import SummaryView from "@/components/SummaryView";

interface Props {
  params: { date: string };
}

export function generateStaticParams() {
  return getAllDates().map((date) => ({ date }));
}

export default function SummaryPage({ params }: Props) {
  const summary = getSummary(params.date);
  if (!summary) notFound();
  return <SummaryView summary={summary} />;
}
