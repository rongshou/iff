#!/bin/bash
set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

echo "========================================="
echo "天权 · 部署脚本"
echo "========================================="

# 1. 检查前置数据
if [ ! -L backend/data/advisor.db ]; then
    echo "[!] 数据链接不存在，创建中..."
    mkdir -p backend/data
    SOURCE_DB="/home/admin/.openclaw/workspace-study-abroad/study-abroad-advisor/data/advisor.db"
    SOURCE_PROB="/home/admin/.openclaw/workspace-study-abroad/study-abroad-advisor/data/real_case_probability.json"
    if [ -f "$SOURCE_DB" ]; then
        ln -sf "$SOURCE_DB" backend/data/advisor.db
    fi
    if [ -f "$SOURCE_PROB" ]; then
        ln -sf "$SOURCE_PROB" backend/data/real_case_probability.json
    fi
fi

# 2. 构建前端
echo ""
echo "[1/3] 构建前端..."
cd frontend
npm install --silent
npm run build
cd ..

# 3. Docker 构建 + 启动
echo ""
echo "[2/3] Docker 构建..."
docker compose build --quiet

echo ""
echo "[3/3] 启动服务..."
docker compose up -d

# 4. 等待健康检查
echo ""
echo "等待服务就绪..."
for i in $(seq 1 30); do
    if curl -sf http://localhost/api/health > /dev/null 2>&1; then
        echo "✅ 服务启动成功!"
        echo ""
        echo "访问地址: http://localhost"
        echo "API 健康: http://localhost/api/health"
        exit 0
    fi
    sleep 2
done

echo "⚠️ 服务启动超时，请检查 docker compose logs"
exit 1
