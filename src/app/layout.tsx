import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "リベシティ日次ダイジェスト",
  description: "リベシティ チャットルームの日次要約",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ja">
      <body className="bg-gray-50 text-gray-800 min-h-screen">
        <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
          <div className="max-w-3xl mx-auto px-4 py-3 flex items-center justify-between">
            <a href="/" className="text-lg font-bold text-indigo-700 hover:text-indigo-900">
              リベシティ ダイジェスト
            </a>
            <nav className="flex gap-4 text-sm">
              <a href="/" className="text-gray-600 hover:text-indigo-700">最新</a>
              <a href="/history" className="text-gray-600 hover:text-indigo-700">履歴</a>
            </nav>
          </div>
        </header>
        <main className="max-w-3xl mx-auto px-4 py-6">{children}</main>
        <footer className="text-center text-xs text-gray-400 py-6">
          © {new Date().getFullYear()} LibeCity Digest
        </footer>
      </body>
    </html>
  );
}
