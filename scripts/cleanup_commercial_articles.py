"""
天权知识库商业化内容清理脚本

从 werss 公众号文章库识别 4 类商业化/低信息价值内容,
写入 tianquan 自己的 advisor.db 中的 excluded_articles 表,
news_knowledge 检索时过滤掉这些文章。

werss 原库不动,可逆。
"""
import sqlite3
import sys
from pathlib import Path

WERS_DB = Path("/home/admin/werss/data/db.db")
ADVISOR_DB = Path(__file__).parent.parent / "backend" / "data" / "advisor.db"


# 1. 纯电商/无关促销 (与留学无关的实物商品推广)
# 命中条件: 标题含商品关键词 + 同时出现价格/促销符号
RULE_ECOM = {
    "reason": "纯电商/无关促销",
    "title_keywords": [
        "限时抢", "秒杀", "包邮", "满减", "优惠券", "折扣码",
        "赠品", "尾单", "拼团", "团购",
    ],
    "title_commodity": [
        "床品", "床笠", "纸巾", "洗衣液", "面膜",
        "化妆品", "保温杯", "充电宝", "耳机", "手机壳",
    ],
    "price_signals": ["元", "¥", "$", "￥", "刀", "块"],
}

# 2. 节日问候
RULE_FESTIVAL = {
    "reason": "节日问候",
    "title_keywords": [
        "端午安康", "中秋快乐", "春节快乐", "新年快乐", "圣诞快乐",
        "元宵节", "国庆节快乐", "清明节", "母亲节快乐", "父亲节快乐",
        "感恩节快乐", "七夕快乐", "重阳节", "劳动节快乐",
    ],
}

# 3. 机构讲座/直播预告/私享会
RULE_WEBINAR = {
    "reason": "机构讲座/直播预告",
    "title_keywords": [
        "直播预告", "私享会", "讲座预告", "训练营", "特训营",
        "菁英汇", "大咖对谈", "线上分享会", "线下分享会",
        "分享会预告", "讲座报名", "直播报名",
    ],
}

# 4. 大学开放日/见面会/宣讲会 (时效性活动通告)
RULE_EVENT = {
    "reason": "大学开放日/见面会",
    "title_keywords": [
        "开放日", "见面会", "宣讲会", "信息日", "教育展", "留学展",
        "新生见面会", "中国信息日",
    ],
}

RULES = [RULE_ECOM, RULE_FESTIVAL, RULE_WEBINAR, RULE_EVENT]


def match_rule(title: str, rule: dict) -> bool:
    for kw in rule.get("title_keywords", []):
        if kw in title:
            return True
    # 电商类特殊判断: 商品词 + 价格信号同时出现
    if rule.get("title_commodity"):
        has_commodity = any(kw in title for kw in rule["title_commodity"])
        has_price = any(kw in title for kw in rule.get("price_signals", []))
        if has_commodity and has_price:
            return True
    return False


def find_candidates(wers_db: Path) -> list[dict]:
    """返回 [{id, title, reason}, ...]"""
    conn = sqlite3.connect(str(wers_db))
    rows = conn.execute("SELECT id, title FROM articles").fetchall()
    conn.close()

    candidates: list[dict] = []
    seen_ids: set[str] = set()
    for aid, title in rows:
        if not title:
            continue
        for rule in RULES:
            if match_rule(title, rule):
                if aid in seen_ids:
                    continue
                seen_ids.add(aid)
                candidates.append({
                    "article_id": aid,
                    "title": title,
                    "reason": rule["reason"],
                })
                break
    return candidates


def ensure_schema(advisor_db: Path) -> None:
    conn = sqlite3.connect(str(advisor_db))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS excluded_articles (
            article_id TEXT PRIMARY KEY,
            reason TEXT NOT NULL,
            title TEXT,
            created_at TEXT DEFAULT (datetime('now', '+8 hours'))
        )
    """)
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_excluded_reason ON excluded_articles(reason)"
    )
    conn.commit()
    conn.close()


def upsert_excludes(advisor_db: Path, candidates: list[dict]) -> int:
    conn = sqlite3.connect(str(advisor_db))
    inserted = 0
    for c in candidates:
        cur = conn.execute(
            "INSERT OR IGNORE INTO excluded_articles(article_id, reason, title) "
            "VALUES(?, ?, ?)",
            (c["article_id"], c["reason"], c["title"]),
        )
        inserted += cur.rowcount
    conn.commit()

    # 统计现有排除表
    stats = conn.execute(
        "SELECT reason, COUNT(*) FROM excluded_articles GROUP BY reason ORDER BY COUNT(*) DESC"
    ).fetchall()
    conn.close()
    print(f"本次新增 {inserted} 条;排除表当前汇总:")
    for reason, n in stats:
        print(f"  {reason}: {n}")
    return inserted


def preview(candidates: list[dict]) -> None:
    """按 reason 分组打印抽样"""
    by_reason: dict[str, list[dict]] = {}
    for c in candidates:
        by_reason.setdefault(c["reason"], []).append(c)

    for reason, items in by_reason.items():
        print(f"\n=== {reason} ({len(items)} 篇) ===")
        for c in items[:8]:
            print(f"  - {c['title'][:70]}")
        if len(items) > 8:
            print(f"  ... 还有 {len(items) - 8} 篇")


def main() -> int:
    if not WERS_DB.exists():
        print(f"ERROR: werss db 不存在: {WERS_DB}", file=sys.stderr)
        return 1
    if not ADVISOR_DB.exists():
        print(f"ERROR: advisor db 不存在: {ADVISOR_DB}", file=sys.stderr)
        return 1

    print(f"扫描 werss 库: {WERS_DB}")
    candidates = find_candidates(WERS_DB)
    print(f"命中 {len(candidates)} 篇待排除")
    preview(candidates)

    dry_run = "--dry-run" in sys.argv
    if dry_run:
        print("\n[--dry-run] 不写入数据库")
        return 0

    print(f"\n写入排除表: {ADVISOR_DB}")
    ensure_schema(ADVISOR_DB)
    upsert_excludes(ADVISOR_DB, candidates)
    print("完成。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
