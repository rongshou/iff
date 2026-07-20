#!/bin/bash
# 天枢冒烟测试 — 验证 Vite 构建产物 + 部署可访问
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

echo "========== 天枢冒烟测试 (Vite) =========="
echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# —— localhost:8080 (nginx, 唯一部署端口) ——
echo "--- localhost:8080 ---"
check_url       "tianshu index.html"            "http://127.0.0.1:8080/tianshu/"
check_contains  "页面标题含'天枢'"              "http://127.0.0.1:8080/tianshu/"    "天枢"
check_contains  "引入 Vite JS bundle"           "http://127.0.0.1:8080/tianshu/"    "assets/index"
check_contains  "引入 CSS asset"                "http://127.0.0.1:8080/tianshu/"    "assets/index"

# —— tianquan API (通过 nginx 反向代理) ——
echo ""
echo "--- tianquan API ---"
check_url       "api health"                    "http://127.0.0.1:8080/api/health"
check_contains  "api health 响应 status=ok"     "http://127.0.0.1:8080/api/health"  '"status":"ok"'

# —— 构建产物验证 ——
echo ""
echo "--- dist/tianshu/ (Vite 构建) ---"
for f in index.html; do
  if [ -f "/home/admin/tianquan/dist/tianshu/$f" ]; then
    ok "dist/tianshu/$f exists"
  else
    fail "dist/tianshu/$f MISSING"
  fi
done
# 检查 Vite JS 资产
JS_COUNT=$(ls /home/admin/tianquan/dist/tianshu/assets/index-*.js 2>/dev/null | wc -l)
if [ "$JS_COUNT" -ge 1 ]; then
  ok "Vite JS assets: $JS_COUNT files"
else
  fail "Vite JS assets MISSING"
fi

echo ""
echo "========== 结果: $PASS 通过, $FAIL 失败, 总计 $((PASS+FAIL)) =========="
exit $FAIL
