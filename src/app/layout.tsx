import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "リベシティ日次ダイジェスト",
  description: "リベシティ チャットルームの日次要約",
  icons: {
    apple: "/apple-touch-icon.png",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ja">
      <body className="min-h-screen" style={{ background: "var(--bg)", color: "#1a1a2e" }}>
        {/* ── Header ── */}
        <header className="sticky top-0 z-20 bg-white shadow-sm">
          <div
            className="max-w-3xl mx-auto px-4 py-3 flex items-center justify-between"
          >
            <Link
              href="/"
              className="text-xl font-black tracking-tight"
              style={{
                fontFamily: "'Poppins', sans-serif",
                background: "linear-gradient(90deg, var(--red), var(--orange), var(--yellow), var(--green), var(--blue), var(--purple))",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
                backgroundClip: "text",
              }}
            >
              LibeCity Digest
            </Link>
            <nav className="flex gap-3 text-sm font-bold">
              <Link
                href="/"
                className="px-3 py-1 rounded-full transition-all hover:scale-105"
                style={{ background: "var(--blue)", color: "#fff" }}
              >
                最新
              </Link>
              <Link
                href="/history"
                className="px-3 py-1 rounded-full transition-all hover:scale-105"
                style={{ background: "var(--purple)", color: "#fff" }}
              >
                履歴
              </Link>
            </nav>
          </div>
          {/* rainbow bottom bar */}
          <div
            style={{
              height: 4,
              background: "linear-gradient(90deg, var(--red), var(--orange), var(--yellow), var(--green), var(--blue), var(--purple))",
            }}
          />
        </header>

        <main className="max-w-3xl mx-auto px-4 py-8">{children}</main>

        <footer
          className="text-center text-xs py-8 font-semibold"
          style={{ color: "#aaa" }}
        >
          © {new Date().getFullYear()} LibeCity Digest ✨
        </footer>
      </body>
    </html>
  );
}
