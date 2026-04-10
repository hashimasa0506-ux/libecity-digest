import fs from "fs";
import path from "path";

export interface Section {
  title: string;
  room_id: string;
  summary: string;
  post_count: number;
}

export interface Summary {
  date: string;
  generated_at: string;
  highlight?: string;
  sections: Section[];
}

const DATA_DIR = path.join(process.cwd(), "data", "summaries");

/** 全JSONファイルの日付リストを新しい順に返す */
export function getAllDates(): string[] {
  if (!fs.existsSync(DATA_DIR)) return [];
  return fs
    .readdirSync(DATA_DIR)
    .filter((f) => f.endsWith(".json"))
    .map((f) => f.replace(".json", ""))
    .sort((a, b) => b.localeCompare(a));
}

/** 指定日の要約データを返す（存在しない場合は null） */
export function getSummary(date: string): Summary | null {
  const filePath = path.join(DATA_DIR, `${date}.json`);
  if (!fs.existsSync(filePath)) return null;
  const raw = fs.readFileSync(filePath, "utf-8");
  return JSON.parse(raw) as Summary;
}

/** 最新の要約データを返す */
export function getLatestSummary(): Summary | null {
  const dates = getAllDates();
  if (dates.length === 0) return null;
  return getSummary(dates[0]);
}
