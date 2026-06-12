SCHOOL_TIERS = {
    1: "985/海本",
    2: "211",
    3: "双非",
    4: "普通高中/独立学院",
    5: "大专",
}

C9_SCHOOLS = {
    "北京大学", "清华大学", "复旦大学", "上海交通大学", "浙江大学",
    "南京大学", "中国科学技术大学", "哈尔滨工业大学", "西安交通大学",
}

TIER_985_KEYWORDS = {
    "北京大学", "清华大学", "浙江大学", "复旦大学", "上海交通大学",
    "南京大学", "中国人民大学", "武汉大学", "中山大学", "中国科学技术大学",
    "同济大学", "南开大学", "天津大学", "北京航空航天大学", "北京理工大学",
    "华中科技大学", "厦门大学", "东南大学", "华南理工大学", "四川大学",
    "电子科技大学", "中南大学", "吉林大学", "山东大学", "华东师范大学",
    "大连理工大学", "西北工业大学", "重庆大学", "中国农业大学", "湖南大学",
    "东北大学", "兰州大学", "北京师范大学", "中国海洋大学", "西北农林科技大学",
    "中央民族大学", "国防科技大学",
}

def classify_school_tier(undergrad_school: str | None) -> tuple[int, str]:
    if not undergrad_school:
        return 3, "双非"

    name = undergrad_school.strip()

    if name in ("海本", "英本", "美本", "加本", "澳本", "日韩本", "欧陆本"):
        return 1, "海本"

    for c9 in C9_SCHOOLS:
        if c9 in name:
            return 1, "C9"

    for kw_985 in TIER_985_KEYWORDS:
        if kw_985 in name:
            return 1, "985"

    if "大学" in name:
        return 2, "211"

    return 3, "双非"


def get_tier_label(tier: int) -> str:
    return SCHOOL_TIERS.get(tier, "双非")
