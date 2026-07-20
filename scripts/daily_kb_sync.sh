#!/bin/bash
# 每日知识库同步脚本
# 从 werss.db 处理新文章到 kb_processed

cd /home/admin/tianquan
LOG_DIR="/home/admin/tianquan/logs"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/kb_pipeline_$(date +%Y%m%d).log"

echo "=== KB Pipeline Sync $(date) ===" >> "$LOG"

# 每次最多处理 500 篇
python3 -u scripts/kb_pipeline.py --limit 500 >> "$LOG" 2>&1

# 重建 FTS 索引，确保搜索覆盖所有文章
echo "=== Rebuild FTS $(date) ===" >> "$LOG"
sqlite3 backend/data/advisor.db "DELETE FROM kb_processed_fts; INSERT INTO kb_processed_fts (article_id, title, summary, clean_text, article_type, countries, tags) SELECT article_id, COALESCE(title,''), COALESCE(summary,''), COALESCE(clean_text,''), COALESCE(article_type,''), COALESCE(countries,''), COALESCE(tags,'') FROM kb_processed;" >> "$LOG" 2>&1
FTS_COUNT=$(sqlite3 backend/data/advisor.db "SELECT COUNT(*) FROM kb_processed_fts;")
echo "FTS rebuilt: $FTS_COUNT articles" >> "$LOG"

echo "=== Done $(date) ===" >> "$LOG"

# 清理超过 7 天的日志
find "$LOG_DIR" -name "kb_pipeline_*.log" -mtime +7 -delete 2>/dev/null
