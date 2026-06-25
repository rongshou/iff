#!/bin/bash
# 天枢冒烟测试 — 验证三端部署 + JS 资源可访问
set -euo pipefail

PASS=0
FAIL=0

ok()   { PASS=$((PASS+1)); echo "  ✅ $1"; }
fail() { FAIL=$((FAIL+1)); echo "  ❌ $1"; }

check_url() {
  local label="$1" url="$2"
  local code
  code=$(curl -sS -o /dev/null -w "%{http_code}" --connect-timeout 5 --max-time 10 "$url" 2>/dev/null || echo "000")
  if [ "$code" = "200" ]; then ok "$label → $code"; else fail "$label → $code"; fi
}

check_contains() {
  local label="$1" url="$2" keyword="$3"
  if curl -sS --connect-timeout 5 --max-time 10 "$url" 2>/dev/null | grep -qF "$keyword"; then
    ok "$label (contains '$keyword')"
  else
    fail "$label (missing '$keyword')"
  fi
}

echo "========== 天枢冒烟测试 =========="
echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# —— 端口 80 (nginx) ——
echo "--- localhost:80 ---"
check_url       "index.html"            "http://127.0.0.1/tianshu/"
check_url       "beidou.js"             "http://127.0.0.1/tianshu/beidou.js"
check_url       "bazi.js"               "http://127.0.0.1/tianshu/bazi.js"
check_url       "data.js"               "http://127.0.0.1/tianshu/data.js"
check_url       "engine.js"             "http://127.0.0.1/tianshu/engine.js"
check_url       "app.js"                "http://127.0.0.1/tianshu/app.js"
check_contains  "页面标题含'天枢'"      "http://127.0.0.1/tianshu/"    "天枢"
check_contains  "页面含 MBTI 引用"      "http://127.0.0.1/tianshu/"    "MBTI"
check_contains  "页面含霍兰德引用"      "http://127.0.0.1/tianshu/"    "霍兰德"
check_contains  "引入 bazi.js"          "http://127.0.0.1/tianshu/"    "bazi.js"
check_contains  "引入 beidou.js"        "http://127.0.0.1/tianshu/"    "beidou.js"
check_contains  "引入 data.js"          "http://127.0.0.1/tianshu/"    "data.js"
check_contains  "引入 engine.js"        "http://127.0.0.1/tianshu/"    "engine.js"
check_contains  "引入 app.js"           "http://127.0.0.1/tianshu/"    "app.js"

# —— 端口 8080 (Vite preview) ——
echo ""
echo "--- localhost:8080 ---"
check_url       "index.html"            "http://127.0.0.1:8080/tianshu/"
check_url       "beidou.js"             "http://127.0.0.1:8080/tianshu/beidou.js"
check_url       "bazi.js"               "http://127.0.0.1:8080/tianshu/bazi.js"
check_url       "data.js"               "http://127.0.0.1:8080/tianshu/data.js"
check_url       "engine.js"             "http://127.0.0.1:8080/tianshu/engine.js"
check_url       "app.js"                "http://127.0.0.1:8080/tianshu/app.js"
check_contains  "页面标题含'天枢'"      "http://127.0.0.1:8080/tianshu/"    "天枢"

# —— 构建产物验证 ——
echo ""
echo "--- dist/tianshu/ ---"
for f in index.html app.js bazi.js beidou.js data.js engine.js; do
  if [ -f "/home/admin/tianquan/dist/tianshu/$f" ]; then
    ok "dist/tianshu/$f exists"
  else
    fail "dist/tianshu/$f MISSING"
  fi
done

echo ""
echo "========== 结果: $PASS 通过, $FAIL 失败, 总计 $((PASS+FAIL)) =========="
exit $FAIL
