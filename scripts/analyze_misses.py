#!/usr/bin/env python3
"""分析未命中案例的根因"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
os.chdir(os.path.join(os.path.dirname(__file__), "..", "backend"))

import sqlite3
import random
from collections import defaultdict

DB_PATH = "/home/admin/.openclaw/workspace-study-abroad/study-abroad-advisor/data/advisor.db"
from app.services.recommend import run as run_recommend

COUNTRY_MAP = {
    "英国": "UK", "美国": "US", "澳大利亚": "AU", "加拿大": "CA",
    "中国香港": "HK", "新加坡": "SG",
}

def gpa_format_to_standard(fmt):
    fmt = (fmt or "").strip()
    m = {"4分制": "4分制", "四分制": "4分制", "百分制": "百分制", "5分制": "5分制", "英制百分制": "百分制"}
    return m.get(fmt, fmt)

def clean_gpa(score):
    try:
        s = str(score).strip()
        if '-' in s: return float(s.split('-')[0])
        return float(s)
    except: return None

def analyze_misses():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    rows = db.execute("""
        SELECT c.id, c.country, c.university, c.university_id,
               c.gpa_score, c.gpa_format, c.study_level,
               c.admitted_major, c.original_major, c.undergraduate_school,
               u.qs_rank, u.name
        FROM cases c JOIN universities u ON c.university_id = u.id
        WHERE c.gpa_score IS NOT NULL AND c.gpa_format IN ('四分制','4分制','百分制','5分制')
          AND c.study_level IN ('硕士','本科','博士')
          AND c.country IN ('英国','美国','澳大利亚')
          AND u.qs_rank > 0 AND u.qs_rank < 1000
          AND c.admitted_major NOT LIKE '%Pre-Master%' AND c.admitted_major NOT LIKE '%预科%'
          AND c.gpa_score NOT LIKE '%/%'
        ORDER BY RANDOM() LIMIT 1000
    """).fetchall()
    db.close()

    misses = []
    for case in [dict(r) for r in rows]:
        country = case["country"]
        gpa = clean_gpa(case["gpa_score"])
        fmt = gpa_format_to_standard(case["gpa_format"] or "")
        if not gpa or not fmt: continue

        profile = {
            "target_countries": [country],
            "gpa_score": gpa, "gpa_format": fmt,
            "study_level": case.get("study_level","硕士"),
            "target_major": (case.get("admitted_major") or "")[:20] or None,
            "original_major": case.get("original_major") or None,
            "undergraduate_school": case.get("undergraduate_school") or None,
        }

        try:
            result = run_recommend(profile)
        except: continue

        actual = case["university"]
        hit = any(s["name"] == actual for c in result["by_country"] for s in c.get("schools",[]))

        if not hit:
            rec_schools = [s["name"] for c in result["by_country"] for s in c.get("schools",[])]
            rec_count = sum(c["matched_schools"] for c in result["by_country"])
            misses.append({
                "country": country,
                "actual": actual,
                "qs": case["qs_rank"],
                "gpa4": result["background"]["gpa4"],
                "tier": result["background"]["school_tier_label"],
                "major": (case["admitted_major"] or "")[:15],
                "rec_count": rec_count,
                "rec_top3": rec_schools[:3],
            })
        if len(misses) >= 50: break

    # 分类统计
    print("=" * 70)
    print("未命中根因分析")
    print("=" * 70)
    print(f"总未命中样本: {len(misses)}\n")

    by_country = defaultdict(list)
    for m in misses: by_country[m["country"]].append(m)

    reasons = defaultdict(int)
    for m in misses:
        if m["rec_count"] == 0:
            reasons["0 所学校匹配（过滤过严）"] += 1
        elif m["rec_count"] < 5:
            reasons["<5 所学校匹配（候选过少）"] += 1
        else:
            reasons["有候选但未包含目标校"] += 1

    print("原因分布:")
    for k, v in sorted(reasons.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v} ({v/len(misses)*100:.0f}%)")

    # 按国家显示典型案例
    for country in sorted(by_country.keys()):
        ms = by_country[country]
        low_gpa = [m for m in ms if m["gpa4"] < 3.0]
        mid_gpa = [m for m in ms if 3.0 <= (m["gpa4"] or 0) < 3.5]
        high_gpa = [m for m in ms if m["gpa4"] >= 3.5]

        print(f"\n{country} 未命中 ({len(ms)}个):")
        print(f"  低GPA(<3.0): {len(low_gpa)}, 中GPA(3.0-3.5): {len(mid_gpa)}, 高GPA(>3.5): {len(high_gpa)}")

        for m in ms[:5]:
            print(f"  ✗ {m['actual']}(QS#{m['qs']}) GPA{m['gpa4']} {m['tier']} {m['major']}")
            if m['rec_top3']:
                print(f"    → {', '.join(m['rec_top3'])}")
            else:
                print(f"    → (无推荐)")

if __name__ == "__main__":
    analyze_misses()
