#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "=== read version ==="
VERSION="$(cat tianshu/VERSION 2>/dev/null || echo "v0.0")"
echo "version: $VERSION"

echo "=== tsc ==="
npx tsc -b

echo "=== vite build ==="
VITE_APP_VERSION="$VERSION" npx vite build

echo "=== move React app to dist/tianquan/ ==="
mkdir -p dist/tianquan
for f in dist/*; do
  fname="$(basename "$f")"
  [ "$fname" = "tianquan" ] && continue
  [ "$fname" = "tianshu" ] && continue
  mv "$f" dist/tianquan/
done

echo "=== SPA fallback (404.html) ==="
cp dist/tianquan/index.html dist/tianquan/404.html

echo "=== landing page ==="
cp landing/index.html dist/index.html
cp dist/index.html dist/404.html

echo "=== tianshu ==="
# 步骤 2：tianshu 也走 Vite 构建（输出到 tianshu/dist/）
cd tianshu && pnpm install 2>&1 | tail -3
pnpm build 2>&1
cd ..
mkdir -p dist/tianshu
cp -r tianshu/dist/* dist/tianshu/
# 保留旧测评到 /tianshu/legacy/ 下（步骤 3 才会彻底删除）
mkdir -p dist/tianshu/legacy
cp tianshu/legacy/* dist/tianshu/legacy/ 2>/dev/null || true

echo "=== .nojekyll (GitHub Pages) ==="
touch dist/.nojekyll

echo "=== build complete ==="
ls -la dist/
echo "---"
ls -la dist/tianquan/
echo "---"
ls -la dist/tianshu/
