#!/bin/bash
# 安装 post-merge git hook，使 git pull 后自动构建 tianshu
# 安装: bash scripts/post-merge-build.sh install
# 卸载: bash scripts/post-merge-build.sh uninstall

HOOK_DIR=$(git rev-parse --git-dir 2>/dev/null || echo ".git")
HOOK_FILE="$HOOK_DIR/hooks/post-merge"

case "${1:-install}" in
  install)
    cat > "$HOOK_FILE" << 'HOOK'
#!/bin/bash
# post-merge hook: git pull 后自动构建
CHANGED=$(git diff-tree --no-commit-id -r --name-only HEAD 2>/dev/null | grep -c "^tianshu/")
if [ "$CHANGED" -gt 0 ]; then
  echo "🔨 tianshu 文件变更，自动构建..."
  npm run build --silent 2>&1
  echo "✅ 构建完成"
fi
HOOK
    chmod +x "$HOOK_FILE"
    echo "✅ post-merge hook 已安装"
    ;;
  uninstall)
    rm -f "$HOOK_FILE"
    echo "✅ post-merge hook 已卸载"
    ;;
esac
