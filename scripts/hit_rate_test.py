#!/usr/bin/env python3
"""
天权选校引擎命中率测试
从真实案例中抽取样本，测试推荐引擎的学校命中率

测试逻辑：
1. 从 cases 表中抽取 N 个真实案例
2. 对每个案例，用其 GPA/国家/学位/专业/本科学校 构建推荐请求
3. 调用推荐引擎
4. 检查案例中实际录取的学校是否出现在推荐结果中
5. 计算命中率 = (命中数 / 总测试数) × 100%
"""
import sqlite3
import sys
import os
import json
import random
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
os.chdir(os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.services.recommend import run as run_recommend

DB_PATH = "/home/admin/.openclaw/workspace-study-abroad/study-abroad-advisor/data/advisor.db"

# 国家名称映射: cases 用中文 → universities 用 ISO
COUNTRY_MAP = {
    "英国": "UK", "美国": "US", "澳大利亚": "AU", "加拿大": "CA",
    "中国香港": "HK", "新加坡": "SG", "日本": "JP", "韩国": "KR",
    "中国澳门": "MO", "新西兰": "NZ", "爱尔兰": "IE", "德国": "DE",
    "法国": "FR", "荷兰": "NL", "瑞士": "CH", "瑞典": "SE",
    "丹麦": "DK", "意大利": "IT", "西班牙": "ES", "马来西亚": "MY",
}

SAMPLE_SIZE = 600  # 总测试样本数
TOP_K = 10  # 每个国家推荐 K 所


def load_test_cases():
    """加载高质量测试样本: 有完整 GPA/学校/专业信息的案例"""
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row

    rows = db.execute("""
        SELECT c.id, c.country, c.university, c.university_id,
               c.gpa_score, c.gpa_format, c.study_level,
               c.admitted_major, c.original_major, c.undergraduate_school,
               u.qs_rank, u.name as uni_name
        FROM cases c
        JOIN universities u ON c.university_id = u.id
        WHERE c.gpa_score IS NOT NULL
          AND c.gpa_format IS NOT NULL
          AND c.gpa_format IN ('四分制', '4分制', '百分制', '5分制')
          AND c.study_level IS NOT NULL
          AND c.study_level IN ('硕士', '本科', '博士')
          AND c.country IS NOT NULL
          AND c.country IN ('英国', '美国', '澳大利亚', '加拿大', '中国香港', '新加坡')
          AND u.qs_rank > 0 AND u.qs_rank < 1000
          AND c.admitted_major NOT LIKE '%Pre-Master%'
          AND c.admitted_major NOT LIKE '%预科%'
          AND c.gpa_score NOT LIKE '%/%'
        ORDER BY RANDOM()
        LIMIT 3000
    """).fetchall()

    db.close()
    return [dict(r) for r in rows]


def gpa_format_to_standard(fmt: str) -> str:
    """标准化 GPA 格式"""
    fmt = (fmt or "").strip()
    mapping = {
        "4分制": "4分制", "四分制": "4分制",
        "百分制": "百分制",
        "5分制": "5分制",
        "英制百分制": "百分制",
    }
    return mapping.get(fmt, fmt)


def clean_gpa_score(score):
    """清理GPA分数"""
    try:
        s = str(score).strip()
        if '-' in s:
            parts = s.split('-')
            return float(parts[0])
        return float(s)
    except (ValueError, TypeError):
        return None


def run_hit_test(samples: list[dict], top_k: int = 10) -> dict:
    """运行命中率测试"""
    results = {
        "total": 0,
        "hits": 0,
        "by_country": defaultdict(lambda: {"total": 0, "hits": 0, "details": []}),
        "by_tier": defaultdict(lambda: {"total": 0, "hits": 0}),
        "by_gpa_range": defaultdict(lambda: {"total": 0, "hits": 0}),
        "miss_details": [],
        "errors": [],
    }

    tested = 0
    for case in samples:
        if tested >= SAMPLE_SIZE:
            break

        # 解析案例数据
        country = case.get("country", "")
        gpa_score = clean_gpa_score(case.get("gpa_score"))
        gpa_format = gpa_format_to_standard(case.get("gpa_format", ""))
        study_level = case.get("study_level", "硕士")
        target_major = case.get("admitted_major", "")
        original_major = case.get("original_major") or ""
        undergrad_school = case.get("undergraduate_school") or ""
        actual_uni = case.get("university", "")
        actual_uni_id = case.get("university_id")

        if gpa_score is None:
            continue
        if not gpa_format:
            continue
        if country not in COUNTRY_MAP:
            continue

        # 截断过长的专业名 (Reduce noise)
        if target_major and len(target_major) > 20:
            target_major = target_major[:20]

        profile = {
            "target_countries": [country],
            "gpa_score": gpa_score,
            "gpa_format": gpa_format,
            "study_level": study_level,
            "target_major": target_major or None,
            "original_major": original_major or None,
            "undergraduate_school": undergrad_school or None,
        }

        try:
            result = run_recommend(profile)
        except Exception as e:
            results["errors"].append({
                "case_id": case.get("id"),
                "profile": profile,
                "error": str(e),
            })
            continue

        # 检查命中：实际录取学校是否在推荐列表中
        hit = False
        hit_rank = -1
        for c in result.get("by_country", []):
            for i, s in enumerate(c.get("schools", [])):
                if s["name"] == actual_uni:
                    hit = True
                    hit_rank = i + 1
                    break

        tested += 1
        results["total"] = tested

        if hit:
            results["hits"] += 1

        # 按国家统计
        results["by_country"][country]["total"] += 1
        if hit:
            results["by_country"][country]["hits"] += 1

        # 按学校层次统计
        tier = result["background"]["school_tier_label"]
        results["by_tier"][tier]["total"] += 1
        if hit:
            results["by_tier"][tier]["hits"] += 1

        # 按 GPA 范围统计
        gpa4 = result["background"].get("gpa4") or 0
        if gpa4 < 2.5:
            gpa_bucket = "GPA<2.5"
        elif gpa4 < 3.0:
            gpa_bucket = "GPA2.5-3.0"
        elif gpa4 < 3.3:
            gpa_bucket = "GPA3.0-3.3"
        elif gpa4 < 3.5:
            gpa_bucket = "GPA3.3-3.5"
        else:
            gpa_bucket = "GPA>3.5"
        results["by_gpa_range"][gpa_bucket]["total"] += 1
        if hit:
            results["by_gpa_range"][gpa_bucket]["hits"] += 1

        if not hit and len(results["miss_details"]) < 20:
            results["miss_details"].append({
                "case_id": case.get("id"),
                "actual_uni": actual_uni,
                "country": country,
                "gpa4": gpa4,
                "tier": tier,
                "major": (target_major or "")[:15],
                "recommended": [s["name"] for c in result["by_country"] for s in c["schools"]],
            })

        if tested % 50 == 0:
            sys.stderr.write(f"\r  已测试 {tested}/{SAMPLE_SIZE}... ")
            sys.stderr.flush()

    return results


def print_report(results: dict):
    """打印测试报告"""
    total = max(results["total"], 1)
    hit_rate = results["hits"] / total * 100

    print()
    print("=" * 70)
    print("天权选校引擎命中率测试报告")
    print("=" * 70)
    print(f"  测试样本: {total}")
    print(f"  命中数:   {results['hits']}")
    print(f"  **总体命中率: {hit_rate:.1f}%**")
    if results["errors"]:
        print(f"  错误数:   {len(results['errors'])}")
    print()

    # 按国家
    print("─" * 50)
    print("按目标国家:")
    print(f"  {'国家':<10} {'样本':<6} {'命中':<6} {'命中率':<8}")
    for country in sorted(results["by_country"].keys()):
        d = results["by_country"][country]
        rate = d["hits"] / max(d["total"], 1) * 100
        bar = "█" * int(rate / 5) + "░" * (20 - int(rate / 5))
        print(f"  {country:<10} {d['total']:<6} {d['hits']:<6} {rate:5.1f}%  {bar}")

    # 按学校层次
    print("\n─" * 50)
    print("按本科学校层次:")
    print(f"  {'层次':<10} {'样本':<6} {'命中':<6} {'命中率':<8}")
    for tier in ["C9", "985", "211", "双非"]:
        d = results["by_tier"][tier]
        if d["total"] == 0:
            continue
        rate = d["hits"] / max(d["total"], 1) * 100
        bar = "█" * int(rate / 5) + "░" * (20 - int(rate / 5))
        print(f"  {tier:<10} {d['total']:<6} {d['hits']:<6} {rate:5.1f}%  {bar}")

    # 按 GPA
    print("\n─" * 50)
    print("按 GPA 范围:")
    print(f"  {'范围':<12} {'样本':<6} {'命中':<6} {'命中率':<8}")
    for bucket in sorted(results["by_gpa_range"].keys()):
        d = results["by_gpa_range"][bucket]
        if d["total"] == 0:
            continue
        rate = d["hits"] / max(d["total"], 1) * 100
        bar = "█" * int(rate / 5) + "░" * (20 - int(rate / 5))
        print(f"  {bucket:<12} {d['total']:<6} {d['hits']:<6} {rate:5.1f}%  {bar}")

    # 未命中案例样本
    if results["miss_details"]:
        print("\n─" * 50)
        print(f"未命中案例样本 (展示前 {len(results['miss_details'])} 个):")
        for m in results["miss_details"][:10]:
            print(f"  ✗ {m['actual_uni']}({m['country']}) GPA{m['gpa4']} {m['tier']} "
                  f"→ 推荐: {', '.join(m['recommended'][:5])}")

    print("\n" + "=" * 70)


def main():
    print("加载测试案例...")
    all_cases = load_test_cases()
    print(f"  候选池: {len(all_cases)} 条")

    # 按国家分层抽样
    country_buckets = defaultdict(list)
    for c in all_cases:
        country_buckets[c["country"]].append(c)

    samples = []
    per_country = SAMPLE_SIZE // max(len(country_buckets), 1)
    for country, cases in country_buckets.items():
        random.shuffle(cases)
        samples.extend(cases[:per_country])

    # 补足到 SAMPLE_SIZE
    if len(samples) < SAMPLE_SIZE:
        remaining = [c for c in all_cases if c not in samples]
        random.shuffle(remaining)
        samples.extend(remaining[:SAMPLE_SIZE - len(samples)])

    random.shuffle(samples)
    samples = samples[:SAMPLE_SIZE]

    print(f"  测试样本: {len(samples)}")
    for c in sorted(country_buckets.keys()):
        cnt = sum(1 for s in samples if s["country"] == c)
        print(f"    {c}: {cnt}")

    print("\n运行命中率测试...")
    results = run_hit_test(samples, top_k=TOP_K)
    print_report(results)

    return results


if __name__ == "__main__":
    main()
