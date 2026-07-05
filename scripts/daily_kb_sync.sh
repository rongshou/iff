#!/bin/bash
# 每日知识库同步脚本
# 从 werss.db 处理新文章到 kb_processed

cd /home/admin/tianquan
LOG_DIR="/home/admin/tianquan/logs"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/kb_pipeline_$(date +%Y%m%d).log"

echo "=== KB Pipeline Sync $(date) ===" >> "$LOG"

# 每次最多处理 100 篇（避免跑太久）
python3 -u scripts/kb_pipeline.py --limit 500 >> "$LOG" 2>&1

echo "=== Done $(date) ===" >> "$LOG"

# 清理超过 7 天的日志
find "$LOG_DIR" -name "kb_pipeline_*.log" -mtime +7 -delete 2>/dev/null
