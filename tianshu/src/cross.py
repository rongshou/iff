"""
天枢 · 多维度交叉验证模块
输入:bazi_result + ziwei_result + mbti_result + holland_result
输出:核心匹配点 / 差异点 / 最终核心定位标签
"""

def cross_validate(bazi: dict, ziwei: dict, mbti: dict, holland: dict) -> dict:
    """
    多维度交叉验证,生成核心定位。
    简化版:不做复杂的相似度算法,而是按主题分类汇总核心特质。
    """
    # 提取各体系的核心关键词
    bazi_keywords = []
    bazi_keywords.append(bazi["核心性格"])
    bazi_keywords.append(bazi["学业事业适配"])

    ziwei_keywords = []
    for gong in ["命宫", "事业宫", "财帛宫"]:
        if gong in ziwei:
            ziwei_keywords.append(ziwei[gong]["特质"])
            ziwei_keywords.append(ziwei[gong]["适配"])

    mbti_keywords = [
        mbti["核心"],
        mbti["认知"],
        mbti["行为"],
    ]

    holland_top3 = holland["核心3位代码"]
    holland_keywords = [holland["代码解析"]] + holland["主适配方向"]

    # 找出共同方向(简化:统计"研究""逻辑""技术""分析""系统"等关键词)
    common_themes = []
    combined_text = " ".join([
        " ".join(bazi_keywords),
        " ".join(ziwei_keywords),
        " ".join(mbti_keywords),
        " ".join(holland_keywords),
    ])

    theme_keywords = {
        "研究/学术": ["研究", "学术", "分析", "深度", "探究", "哲学", "心理"],
        "技术/工程": ["技术", "工程", "IT", "计算机", "软件", "硬件", "系统"],
        "逻辑/系统": ["逻辑", "系统", "架构", "结构", "规则", "战略"],
        "创造/艺术": ["创意", "创造", "艺术", "设计", "文学", "表演"],
        "教育/服务": ["教育", "服务", "咨询", "心理", "帮助", "辅导"],
        "管理/领导": ["管理", "领导", "决策", "战略", "组织", "团队"],
        "商业/销售": ["销售", "商业", "营销", "金融", "市场", "谈判"],
        "动手/实践": ["动手", "实践", "操作", "工艺", "工程", "户外"],
    }

    for theme, keywords in theme_keywords.items():
        matches = sum(1 for kw in keywords if kw in combined_text)
        if matches >= 3:
            common_themes.append((theme, matches))

    # 排序:匹配次数最多的主题
    common_themes.sort(key=lambda x: x[1], reverse=True)

    # 差异点(简化:各体系关注的维度差异)
    differences = [
        f"八字:偏 {bazi['日主五行']} 性,核心适配 {bazi['学业事业适配'].split('、')[0]}",
        f"紫微:命宫 {ziwei['命宫']['主星']} 主导,事业宫 {ziwei['事业宫']['主星']}",
        f"MBTI:类型 {mbti['完整类型']}({mbti['昵称']}),{mbti['核心'][:30]}...",
        f"霍兰德:核心代码 {holland_top3},{holland['代码解析']}",
    ]

    # 生成核心定位标签(基于主导主题 + MBTI + 五行)
    primary_theme = common_themes[0][0] if common_themes else "多元发展型"
    position_label = generate_position_label(primary_theme, bazi, mbti, holland)

    # 核心竞争力组合
    competitive_advantages = [
        f"天赋层:日主 {bazi['日主']}({bazi['日主五行']}),{bazi['核心性格']}",
        f"性格层:{mbti['昵称']}({mbti['完整类型']}),{mbti['优势'][:40]}",
        f"兴趣层:霍兰德 {holland_top3},{holland['代码解析']}",
    ]

    # 核心短板
    shortcomings = [
        f"性格:{mbti['短板']}",
    ]
    if holland["缺失维度预警"] != "无明显短板维度":
        shortcomings.append(f"能力:{holland['缺失维度预警']}")

    return {
        "核心主题": common_themes[:5] if common_themes else [("多元型", 0)],
        "差异点": differences,
        "核心定位标签": position_label,
        "核心竞争力组合": competitive_advantages,
        "核心短板": shortcomings,
        "验证结论": f"基于八字 + 紫微 + MBTI + 霍兰德四维交叉,学生核心发展主题为「{primary_theme}」,适配路径以「{position_label['主方向']}」为核心。",
    }


def generate_position_label(theme: str, bazi: dict, mbti: dict, holland: dict) -> dict:
    """根据主导主题生成核心定位标签。"""
    # 不同主题的标签模板
    templates = {
        "研究/学术": "{mbti_nick}研究者,擅长{mbti_特质},聚焦{holland_代码}方向的深度探索",
        "技术/工程": "硬核技术{mbti_nick},既有{bazi_特质}又有{mbti_特质},天然适配{holland_代码}类工程赛道",
        "逻辑/系统": "系统架构型{mbti_nick},{bazi_特质}+{mbti_特质},擅长构建长期{holland_代码}类解决方案",
        "创造/艺术": "创意型{mbti_nick},{mbti_特质},在{holland_代码}方向有独特创造力",
        "教育/服务": "服务型{mbti_nick},{mbti_特质},适合{holland_代码}类教育/辅导赛道",
        "管理/领导": "战略型{mbti_nick},{bazi_特质},兼具{mbti_特质},适合{holland_代码}类管理岗位",
        "商业/销售": "商业型{mbti_nick},{mbti_特质},适合{holland_代码}类商业赛道",
        "动手/实践": "实践型{mbti_nick},{bazi_特质},擅长{holland_代码}类实操工作",
    }

    template = templates.get(theme, "多元发展型{mbti_nick},{bazi_特质}")

    label = template.format(
        mbti_nick=mbti["昵称"],
        mbti_特质=mbti["核心"][:20],
        bazi_特质=bazi["核心性格"][:20],
        holland_代码=holland["核心3位代码"],
    )

    # 主方向
    if theme in ["研究/学术", "技术/工程", "逻辑/系统"]:
        main_direction = "硬核技术研发类赛道"
    elif theme in ["创造/艺术"]:
        main_direction = "创意与设计类赛道"
    elif theme in ["教育/服务"]:
        main_direction = "教育服务与人文类赛道"
    elif theme in ["管理/领导"]:
        main_direction = "战略管理与领导类赛道"
    elif theme in ["商业/销售"]:
        main_direction = "商业与销售类赛道"
    else:
        main_direction = "跨领域综合发展"

    return {
        "标签": label,
        "主方向": main_direction,
        "主题": theme,
    }


if __name__ == "__main__":
    # 测试:导入其他模块
    from datetime import datetime
    from bazi import get_four_pillars
    from ziwei import get_ziwei_summary
    from mbti import get_mbti_info
    from holland import get_holland_info

    dt = datetime(2010, 5, 15, 14, 30)
    bazi = get_four_pillars(dt)
    ziwei = get_ziwei_summary(dt)
    mbti = get_mbti_info("INTJ-A")
    holland = get_holland_info({"R": 30, "I": 85, "A": 70, "S": 65, "E": 40, "C": 35})

    result = cross_validate(bazi, ziwei, mbti, holland)
    for k, v in result.items():
        print(f"\n{k}:")
        if isinstance(v, list):
            for item in v:
                print(f"  - {item}")
        elif isinstance(v, dict):
            for kk, vv in v.items():
                print(f"  {kk}: {vv}")
        else:
            print(f"  {v}")