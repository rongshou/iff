"""
天枢 · 八字排盘模块
公历日期 → 农历 → 四柱干支 → 日主 → 五行 → 喜用神
"""
from datetime import datetime, date
from lunardate import LunarDate

# 天干
TIANGAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
# 地支
DIZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
# 五行
WUXING = {"木": "木", "火": "火", "土": "土", "金": "金", "水": "水"}
# 天干五行
TG_WUXING = {
    "甲": "木", "乙": "木",
    "丙": "火", "丁": "火",
    "戊": "土", "己": "土",
    "庚": "金", "辛": "金",
    "壬": "水", "癸": "水",
}
# 地支五行
DZ_WUXING = {
    "子": "水", "亥": "水",
    "寅": "木", "卯": "木",
    "巳": "火", "午": "火",
    "申": "金", "酉": "金",
    "辰": "土", "丑": "土", "未": "土", "戌": "土",
}

# 阳历年的天干(以公元 4 年为甲子年起算)
def year_tiangan(year: int) -> str:
    """公元年 → 年干。公元 4 年 = 甲子。"""
    idx = (year - 4) % 10
    return TIANGAN[idx]


def year_dizhi(year: int) -> str:
    """公元年 → 年支。公元 4 年 = 甲子。"""
    idx = (year - 4) % 12
    return DIZHI[idx]


def month_dizhi(year: int, lunar_month: int) -> str:
    """农历月 → 月支。
    月支固定:正月寅、二月卯、三月辰、四月巳、五月午、六月未、
            七月申、八月酉、九月戌、十月亥、十一月子、十二月丑
    """
    base = ["寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑"]
    return base[(lunar_month - 1) % 12]


def month_tiangan(year_tg: str, lunar_month: int) -> str:
    """根据年干推月干(五虎遁年起月法)。
    甲己之年丙作首,乙庚之岁戊为头,
    丙辛必定寻庚起,丁壬壬位顺行流,
    戊癸之年何处起,甲寅之上好追求。
    """
    year_to_start = {
        "甲": "丙", "己": "丙",
        "乙": "戊", "庚": "戊",
        "丙": "庚", "辛": "庚",
        "丁": "壬", "壬": "壬",
        "戊": "甲", "癸": "甲",
    }
    start = year_to_start[year_tg]
    idx = (TIANGAN.index(start) + (lunar_month - 1)) % 10
    return TIANGAN[idx]


def day_pillar(target_date: datetime.date) -> tuple[str, str]:
    """公历日 → 日柱干支。
    使用 lunardate 反推 + 已知锚点(1900-01-01 = 甲戌日)。
    """
    # 1900-01-01 是甲戌日(第 11 个干支,索引 10)
    anchor = date(1900, 1, 1)
    delta_days = (target_date - anchor).days
    pillar_idx = (10 + delta_days) % 60
    tg = TIANGAN[pillar_idx % 10]
    dz = DIZHI[pillar_idx % 12]
    return tg, dz


def hour_tiangan(day_tg: str, hour_branch: str) -> str:
    """根据日干推时干(五鼠遁日起时法)。
    甲己还加甲,乙庚丙作初,
    丙辛从戊起,丁壬庚子居,
    戊癸何方发,壬子是真途。
    """
    day_to_start = {
        "甲": "甲", "己": "甲",
        "乙": "丙", "庚": "丙",
        "丙": "戊", "辛": "戊",
        "丁": "庚", "壬": "庚",
        "戊": "壬", "癸": "壬",
    }
    start = day_to_start[day_tg]
    branch_idx = DIZHI.index(hour_branch)
    idx = (TIANGAN.index(start) + branch_idx) % 10
    return TIANGAN[idx]


def hour_branch(dt: datetime) -> str:
    """根据小时数 → 时支。
    子(23-1)、丑(1-3)、寅(3-5)、卯(5-7)、辰(7-9)、巳(9-11)、
    午(11-13)、未(13-15)、申(15-17)、酉(17-19)、戌(19-21)、亥(21-23)
    """
    h = dt.hour
    if h == 23 or h == 0:
        return "子"
    idx = (h + 1) // 2
    return DIZHI[idx]


def get_four_pillars(dt: datetime) -> dict:
    """主函数:给定公历时间 → 四柱干支 + 五行统计 + 喜用神(简化版)。
    返回字典,供后续模块使用。
    """
    # 公历 → 农历
    lunar = LunarDate.fromSolarDate(dt.year, dt.month, dt.day)
    # 转回公历日期(只取年月日,不影响排盘,但用于日柱)
    solar = datetime(lunar.year, lunar.month, lunar.day)

    # 年柱(以立春为界,这里简化为春节前后统一用农历年)
    year_tg = year_tiangan(lunar.year)
    year_dz = year_dizhi(lunar.year)

    # 月柱
    month_tg = month_tiangan(year_tg, lunar.month)
    month_dz = month_dizhi(lunar.year, lunar.month)

    # 日柱(用公历日期算,因为日柱从子时就分日)
    solar_date = dt.date()
    day_tg, day_dz = day_pillar(solar_date)

    # 时柱
    h_branch = hour_branch(dt)
    h_tg = hour_tiangan(day_tg, h_branch)

    # 五行统计
    all_tg = [year_tg, month_tg, day_tg, h_tg]
    all_dz = [year_dz, month_dz, day_dz, h_branch]
    wuxing_count = {"木": 0, "火": 0, "土": 0, "金": 0, "水": 0}
    for tg in all_tg:
        wuxing_count[TG_WUXING[tg]] += 1
    for dz in all_dz:
        wuxing_count[DZ_WUXING[dz]] += 1

    # 日主五行
    day_master = TG_WUXING[day_tg]

    # 喜用神(简化规则:同类 + 生我者 = 喜用;克我 + 我克 + 我生 = 忌神)
    sheng_wo = {"木": "水", "火": "木", "土": "火", "金": "土", "水": "金"}
    ke_wo = {"木": "金", "火": "水", "土": "木", "金": "火", "水": "土"}
    xi_zhong = [day_master, sheng_wo[day_master]]
    ji_zhong = [ke_wo[day_master], sheng_wo[ke_wo[day_master]], ke_wo[sheng_wo[day_master]]]

    # 找最缺的五行作为最需要补的(简化)
    min_wx = min(wuxing_count, key=wuxing_count.get)

    # 大致性格特质(基于日主五行)
    personality = {
        "木": "仁慈、向上、条理分明、逻辑清晰,有成长型思维",
        "火": "热情、表达力强、行动力快,善于感染他人",
        "土": "稳重、包容、注重规则与执行,有强落地能力",
        "金": "刚毅、果断、追求精准与秩序,擅长结构化分析",
        "水": "灵活、智慧、善于变通,具备深度思考与适应力",
    }

    # 学业事业适配(基于五行)
    career_fit = {
        "木": "教育、文化、出版、设计、IT、互联网",
        "火": "传媒、新能源、电力、互联网运营、自媒体",
        "土": "建筑、房地产、农业、陶瓷、政府公共管理",
        "金": "金融、银行、证券、机械、硬件、芯片",
        "水": "物流、贸易、航运、水利、哲学研究",
    }

    return {
        "阳历": dt.strftime("%Y-%m-%d %H:%M"),
        "农历": f"{lunar.year}年{lunar.month}月{lunar.day}日",
        "年柱": f"{year_tg}{year_dz}",
        "月柱": f"{month_tg}{month_dz}",
        "日柱": f"{day_tg}{day_dz}",
        "时柱": f"{h_tg}{h_branch}",
        "日主": day_tg,
        "日主五行": day_master,
        "五行统计": wuxing_count,
        "最缺五行": min_wx,
        "喜用神": xi_zhong,
        "忌神": ji_zhong,
        "核心性格": personality[day_master],
        "学业事业适配": career_fit[day_master],
    }


if __name__ == "__main__":
    # 测试
    test_dt = datetime(2010, 5, 15, 14, 30)
    result = get_four_pillars(test_dt)
    for k, v in result.items():
        print(f"{k}: {v}")