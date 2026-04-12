/** @type {import('next').NextConfig} */
// GitHub Actions 環境では自動で GITHUB_ACTIONS=true がセットされる
const isGitHubPages = process.env.GITHUB_ACTIONS === "true";

const nextConfig = {
  output: "export",
  // GitHub Pages はリポジトリ名がサブパスになる（例: /libecity-digest）
  basePath:    isGitHubPages ? "/libecity-digest" : "",
  assetPrefix: isGitHubPages ? "/libecity-digest/" : "",
  trailingSlash: true,  // 静的ホスティング向け（/history → /history/index.html）
};

export default nextConfig;
