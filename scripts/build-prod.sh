#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "=== tsc ==="
npx tsc -b

echo "=== vite build ==="
npx vite build

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
mkdir -p dist/tianshu
cp tianshu/index.html tianshu/*.js tianshu/VERSION dist/tianshu/

echo "=== build complete ==="
ls -la dist/
echo "---"
ls -la dist/tianquan/
echo "---"
ls -la dist/tianshu/
