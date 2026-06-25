"""
天枢 · 霍兰德职业兴趣测试解析模块
输入:6 维度得分 → 输出核心 3 位兴趣代码 + 适配专业/职业
"""

# 6 大维度
HOLLAND_DIMENSIONS = {
    "R": {"名": "现实型(Realistic)", "核心": "喜欢动手、实际操作、工具与机械", "适配": "工程、技术、户外、农业、手工艺"},
    "I": {"名": "研究型(Investigative)", "核心": "喜欢分析、思考、解决抽象问题", "适配": "科研、数学、IT、医学研究、哲学"},
    "A": {"名": "艺术型(Artistic)", "核心": "喜欢创造、表达、自我实现", "适配": "艺术、设计、文学、音乐、传媒"},
    "S": {"名": "社会型(Social)", "核心": "喜欢帮助他人、教育、合作", "适配": "教育、心理咨询、社会工作、医疗"},
    "E": {"名": "企业型(Enterprising)", "核心": "喜欢影响他人、领导、说服", "适配": "管理、销售、法律、政治、创业"},
    "C": {"名": "常规型(Conventional)", "核心": "喜欢结构化、数据、组织", "适配": "会计、行政、金融、档案、IT 运维"},
}

# 常见 3 位代码组合解析
COMMON_CODES = {
    "RIA": "实干的研究者:动手 + 思考 + 创造,适合工程研发、实验技术",
    "IRE": "研究型工程师:思考 + 动手 + 影响,适合技术管理、研发管理",
    "IRA": "独立思考者:研究 + 动手 + 艺术,适合技术设计、产品研发",
    "IAS": "研究型学者:思考 + 艺术 + 服务,适合学术研究、深度分析",
    "IES": "研究型教育者:思考 + 影响 + 服务,适合学术教学、专业咨询",
    "ISE": "社会型研究者:服务 + 思考 + 影响,适合医学研究、咨询",
    "RAI": "现实型艺术家:动手 + 创造 + 思考,适合产品设计、建筑设计",
    "RSE": "社会型实干者:动手 + 服务 + 影响,适合体育教练、技术培训",
    "REI": "现实型管理者:动手 + 影响 + 思考,适合工程管理、项目经理",
    "RIC": "技术专家:动手 + 思考 + 常规,适合技术研发、数据分析",
    "RSA": "艺术型实干者:动手 + 服务 + 创造,适合工艺美术、实用设计",
    "ASE": "创意管理者:艺术 + 服务 + 影响,适合广告、传媒管理",
    "AES": "艺术家:艺术 + 影响 + 服务,适合表演、教育艺术",
    "AIS": "创意思考者:艺术 + 研究 + 服务,适合心理学、艺术治疗",
    "AIE": "研究型艺术家:艺术 + 思考 + 影响,适合高端设计、创意战略",
    "ASI": "服务型艺术家:艺术 + 社会 + 研究,适合艺术教育、文化研究",
    "SAI": "社会型艺术家:服务 + 艺术 + 研究,适合教育、心理辅导",
    "SAC": "社会服务者:服务 + 艺术 + 常规,适合教育管理、社会服务",
    "SIA": "教育研究者:服务 + 研究 + 艺术,适合学术教育、研究",
    "SIE": "服务型思考者:服务 + 研究 + 影响,适合医学、政策分析",
    "SCE": "社会管理者:服务 + 常规 + 影响,适合行政、教育管理",
    "ESC": "企业服务者:影响 + 服务 + 常规,适合销售管理、人力资源",
    "EAS": "艺术影响者:影响 + 艺术 + 服务,适合广告创意、艺术管理",
    "EIS": "研究型影响者:影响 + 研究 + 服务,适合战略咨询、专业服务",
    "EIC": "商业分析师:影响 + 研究 + 常规,适合金融分析、商业战略",
    "ECS": "社会型企业人:影响 + 常规 + 服务,适合销售管理、客户成功",
    "ECI": "商业研究者:影响 + 常规 + 研究,适合金融、合规",
    "CEA": "企业艺术家:影响 + 常规 + 艺术,适合品牌管理、营销",
    "CIR": "常规型研究者:常规 + 研究 + 现实,适合数据科学、研发管理",
    "CIS": "研究型服务者:常规 + 研究 + 服务,适合数据分析、学术支持",
    "CIE": "商业研究者:常规 + 研究 + 影响,适合金融分析、咨询",
    "CRE": "技术管理者:常规 + 现实 + 影响,适合 IT 管理、项目经理",
    "CRI": "技术分析师:常规 + 现实 + 研究,适合工程、IT 运维",
    "CRS": "社会服务者:常规 + 现实 + 服务,适合行政支持、技术服务",
    "CSE": "社会支持者:常规 + 服务 + 影响,适合 HR、行政管理",
    "CSA": "艺术支持者:常规 + 服务 + 艺术,适合出版、文化机构",
    "CAI": "艺术分析师:常规 + 艺术 + 研究,适合设计研究、市场分析",
    "CAS": "社会支持者:常规 + 艺术 + 服务,适合教育管理、艺术行政",
    "CEI": "商业分析师:常规 + 影响 + 研究,适合金融分析、风险管理",
    "CES": "企业服务者:常规 + 影响 + 服务,适合销售支持、客户管理",
}


def get_holland_info(scores: dict) -> dict:
    """
    输入:6 维度得分字典,如 {"R": 30, "I": 80, "A": 60, "S": 40, "E": 50, "C": 35}
    输出:核心 3 位代码 + 解析
    """
    if not scores or len(scores) != 6:
        return {"错误": "需要 6 个维度得分(R/I/A/S/E/C)"}

    # 检查维度是否齐全
    required = set("RIASEC")
    if set(scores.keys()) != required:
        return {"错误": f"需要 6 个维度:{required},实际输入:{set(scores.keys())}"}

    # 按得分从高到低排序
    sorted_dims = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top3_code = "".join([d[0] for d in sorted_dims[:3]])

    # 查找常见代码解释,没有就给通用解释
    code_explain = COMMON_CODES.get(top3_code, None)
    if not code_explain:
        d0, s0 = sorted_dims[0]
        d1, s1 = sorted_dims[1]
        d2, s2 = sorted_dims[2]
        code_explain = f"组合 {top3_code}:由 {d0}({s0})、{d1}({s1})、{d2}({s2}) 主导,需结合具体场景判断适配方向"

    # 各维度详细分析
    dimensions = {k: HOLLAND_DIMENSIONS[k] for k in "RIASEC"}

    # 主适配方向(基于 Top3)
    main_fit = []
    for code in top3_code:
        main_fit.append(f"{dimensions[code]['名']}:{dimensions[code]['适配']}")

    # 缺失维度风险提示
    low_dims = [d[0] for d in sorted_dims if d[1] < 30]
    risk_warning = ""
    if low_dims:
        names = [dimensions[d]['名'] for d in low_dims]
        risk_warning = f"得分较低维度:{', '.join(names)} — 可能在这些领域的能力/意愿相对不足,作为发展参考"

    return {
        "6维度得分": scores,
        "排序": sorted_dims,
        "核心3位代码": top3_code,
        "代码解析": code_explain,
        "各维度详情": dimensions,
        "主适配方向": main_fit,
        "缺失维度预警": risk_warning if risk_warning else "无明显短板维度",
    }


if __name__ == "__main__":
    # 测试:研究型(I) + 艺术型(A) + 社会型(S) 主导
    test_scores = {"R": 30, "I": 85, "A": 70, "S": 65, "E": 40, "C": 35}
    result = get_holland_info(test_scores)
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