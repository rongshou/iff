"""
天枢 · 紫微斗数简版模块
只算命宫主星 + 事业宫主星 + 财帛宫主星,用于辅助交叉验证。
完整紫微排盘涉及 14 主星 + 12 宫位 + 四化飞星,简版只取核心。
"""
from datetime import datetime

# 14 主星(简化分组,主星按强度)
MAIN_STARS = {
    "紫微": {"特质": "尊贵、领导力、追求完美", "适配": "管理、决策、战略规划"},
    "天机": {"特质": "智慧、谋略、分析能力强", "适配": "研究、咨询、策划"},
    "太阳": {"特质": "热情、表达、社交活跃", "适配": "公关、传媒、教育"},
    "武曲": {"特质": "刚毅、执行、财务敏锐", "适配": "金融、工程、技术研发"},
    "天同": {"特质": "温和、享福、人缘佳", "适配": "服务、艺术、生活类"},
    "廉贞": {"特质": "聪明、复杂、情感丰富", "适配": "艺术、政治、复杂决策"},
    "天府": {"特质": "稳重、收纳、理财", "适配": "财务、行政、地产"},
    "太阴": {"特质": "细腻、敏感、内敛", "适配": "文学、心理、艺术"},
    "贪狼": {"特质": "欲望、才艺、多才多艺", "适配": "销售、艺术、跨界"},
    "巨门": {"特质": "口才、争议、深度沟通", "适配": "律师、辩论、教学"},
    "天相": {"特质": "协调、辅助、文雅", "适配": "行政、秘书、外交"},
    "天梁": {"特质": "庇荫、年长、照顾他人", "适配": "教育、医疗、咨询"},
    "七杀": {"特质": "独立、冲劲、果断", "适配": "创业、军警、技术攻坚"},
    "破军": {"特质": "变革、创新、颠覆", "适配": "创业、研发、改革"},
}

# 命宫主星速算法(简化版)
# 基于出生月份 + 时辰生成主星组合
def calc_ming_gong(dt: datetime) -> dict:
    """根据公历月 + 时辰,简版推算命宫主星。"""
    month = dt.month
    hour = dt.hour

    # 简化映射:月份 → 命宫主星倾向
    month_star_map = {
        1: "紫微", 2: "天机", 3: "太阳", 4: "武曲",
        5: "天同", 6: "廉贞", 7: "天府", 8: "太阴",
        9: "贪狼", 10: "巨门", 11: "天相", 12: "天梁",
    }
    ming_star = month_star_map[month]

    # 时辰微调:子午时强化主星,卯酉时减弱
    hour_modifier = ""
    if hour % 12 in (0, 6):  # 子时或午时
        hour_modifier = "主星力量强化"
    elif hour % 12 in (3, 9):  # 卯时或酉时
        hour_modifier = "主星力量减弱"

    return {
        "宫位": "命宫",
        "主星": ming_star,
        "特质": MAIN_STARS[ming_star]["特质"],
        "适配": MAIN_STARS[ming_star]["适配"],
        "时辰影响": hour_modifier,
    }


def calc_shiye_gong(dt: datetime) -> dict:
    """事业宫主星 = 命宫主星 + 4 位移(简化:取下一个月主星)。"""
    month = dt.month
    month_star_map = {
        1: "紫微", 2: "天机", 3: "太阳", 4: "武曲",
        5: "天同", 6: "廉贞", 7: "天府", 8: "太阴",
        9: "贪狼", 10: "巨门", 11: "天相", 12: "天梁",
    }
    next_month = (month % 12) + 1
    star = month_star_map[next_month]
    return {
        "宫位": "事业宫",
        "主星": star,
        "特质": MAIN_STARS[star]["特质"],
        "适配": MAIN_STARS[star]["适配"],
    }


def calc_caibo_gong(dt: datetime) -> dict:
    """财帛宫主星 = 命宫主星 + 2 位移。"""
    month = dt.month
    month_star_map = {
        1: "紫微", 2: "天机", 3: "太阳", 4: "武曲",
        5: "天同", 6: "廉贞", 7: "天府", 8: "太阴",
        9: "贪狼", 10: "巨门", 11: "天相", 12: "天梁",
    }
    next_month = ((month + 1) % 12) + 1
    star = month_star_map[next_month]
    return {
        "宫位": "财帛宫",
        "主星": star,
        "特质": MAIN_STARS[star]["特质"],
        "适配": MAIN_STARS[star]["适配"],
    }


def get_ziwei_summary(dt: datetime) -> dict:
    """主函数:返回紫微简版摘要。"""
    return {
        "命宫": calc_ming_gong(dt),
        "事业宫": calc_shiye_gong(dt),
        "财帛宫": calc_caibo_gong(dt),
        "说明": "本结果为简版紫微排盘,仅取核心三宫主星。完整紫微涉及 14 主星 + 12 宫位 + 四化飞星,建议使用专业排盘软件获取完整结果。",
    }


if __name__ == "__main__":
    test_dt = datetime(2010, 5, 15, 14, 30)
    result = get_ziwei_summary(test_dt)
    for k, v in result.items():
        print(f"\n{k}:")
        if isinstance(v, dict):
            for kk, vv in v.items():
                print(f"  {kk}: {vv}")
        else:
            print(f"  {v}")