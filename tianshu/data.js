/**
 * 天枢 · 静态数据(MBTI / 霍兰德 / 紫微 / 专业库)
 */

// ===== MBTI 16 型数据 =====
const MBTI_DATA = {
  "ISTJ": {nick:"物流师",core:"务实、严谨、可靠,强规则意识与执行力",cog:"注重具体事实与过往经验,决策依赖逻辑与数据",beh:"低调稳定、按计划行事、重视承诺",strength:"执行力强、可靠、细节敏感、责任感强",weakness:"抗拒变化、可能过于保守、不善表达情感",majors:"会计、审计、工程、信息技术、法律、行政管理",careers:"审计师、系统管理员、工程师、军官、律师"},
  "ISFJ": {nick:"守卫者",core:"温和、细心、照顾他人,强服务意识",cog:"关注当下细节与他人需求,决策考虑他人感受",beh:"低调配合、默默付出、重视和谐",strength:"细心体贴、可靠、忠诚、有耐心",weakness:"过度牺牲自我、难以拒绝、不善表达需求",majors:"护理、教育、心理学、社会工作、人力资源",careers:"护士、教师、心理咨询师、行政助理"},
  "INFJ": {nick:"提倡者",core:"理想主义、有洞察力,追求意义与价值",cog:"关注未来可能性与深层意义,直觉驱动",beh:"内敛深思、追求完美、有强烈使命感",strength:"洞察力强、有创造力、善于理解他人",weakness:"过度理想化、容易倦怠、不切实际",majors:"心理学、文学、哲学、社会学、设计",careers:"心理咨询师、作家、社工、设计师"},
  "INTJ": {nick:"建筑师",core:"战略思维、独立、追求系统与长远目标",cog:"关注抽象模式与未来趋势,逻辑决策",beh:"独立自主、目标导向、追求能力提升",strength:"战略思维强、独立高效、有远见",weakness:"可能显得孤傲、不善社交、对他人情绪不敏感",majors:"计算机科学、数学、哲学、工程、战略管理",careers:"系统架构师、战略顾问、研究员、CTO"},
  "ISTP": {nick:"鉴赏家",core:"理性、动手能力强,擅长解决具体问题",cog:"关注当下事实,逻辑分析驱动",beh:"冷静、灵活、动手实践",strength:"动手能力强、冷静、适应力强",weakness:"可能显得冷漠、不擅长期规划",majors:"机械工程、电子工程、IT、体育科学",careers:"工程师、技师、运动员、IT 运维"},
  "ISFP": {nick:"探险家",core:"温和、敏感、活在当下,审美独特",cog:"关注感官体验与当下感受",beh:"低调、灵活、追求真实",strength:"审美敏锐、温和、灵活",weakness:"可能过于敏感、不擅冲突",majors:"艺术、设计、音乐、烹饪、护理",careers:"艺术家、设计师、厨师、护士"},
  "INFP": {nick:"调停者",core:"理想主义、内省、追求价值与意义",cog:"关注内在价值与可能性,情感决策",beh:"内敛、敏感、追求真实",strength:"共情力强、有创造力、价值观驱动",weakness:"过度理想化、不切实际、易内耗",majors:"文学、心理学、艺术、哲学、教育",careers:"作家、心理咨询师、教师、艺术家"},
  "INTP": {nick:"逻辑学家",core:"理性、好奇、追求逻辑与真理",cog:"关注抽象理论与逻辑体系",beh:"独立思考、深度探索、可能显得疏离",strength:"逻辑力强、独立、有创造力",weakness:"可能脱离实际、不擅执行",majors:"数学、物理、计算机、哲学",careers:"研究员、程序员、哲学家、分析师"},
  "ESTP": {nick:"企业家",core:"行动派、务实、擅长临场反应",cog:"关注当下事实,逻辑快速决策",beh:"外向、活跃、喜欢冒险",strength:"行动力强、适应力强、社交活跃",weakness:"可能冲动、不擅长期规划",majors:"商科、体育、传媒、销售",careers:"销售、运动员、企业家、谈判专家"},
  "ESFP": {nick:"表演者",core:"热情、活在当下、擅长与人互动",cog:"关注感官体验与他人感受",beh:"外向活泼、享受当下",strength:"热情、社交能力强、有感染力",weakness:"可能缺乏长远规划",majors:"表演、传媒、销售、旅游、教育",careers:"演员、销售、主持人、教师"},
  "ENFP": {nick:"竞选者",core:"热情、创意、关注人的可能性",cog:"关注未来可能性,情感驱动",beh:"外向、热情、有创造力",strength:"创意强、共情力强、热情",weakness:"可能注意力分散",majors:"心理学、传媒、艺术、教育、营销",careers:"营销、心理咨询、教师、作家"},
  "ENTP": {nick:"辩论家",core:"聪明、创新、喜欢挑战传统",cog:"关注可能性与新理论,逻辑驱动",beh:"外向、善辩、喜欢头脑风暴",strength:"创意强、口才好、思维敏捷",weakness:"可能好辩、不喜细节",majors:"法律、商科、计算机、传媒",careers:"律师、创业者、营销策划、产品经理"},
  "ESTJ": {nick:"总经理",core:"务实、果断、强组织管理能力",cog:"关注事实与逻辑,果断决策",beh:"直接、有条理、喜欢掌控",strength:"执行力强、组织力强、果断",weakness:"可能过于强势、不灵活",majors:"商科、管理、法律、工程",careers:"管理者、军官、律师、项目经理"},
  "ESFJ": {nick:"执政官",core:"热心、和谐、关注他人需求",cog:"关注他人感受,情感驱动",beh:"外向、配合、重视和谐",strength:"共情力强、有责任感、善于协调",weakness:"可能过度在意他人评价",majors:"教育、护理、人力资源、市场",careers:"教师、护士、HR、销售"},
  "ENFJ": {nick:"主人公",core:"有魅力、关注他人成长、领导力",cog:"关注他人可能性与未来,情感驱动",beh:"外向、有感染力、善于引导",strength:"领导力强、共情力强、有魅力",weakness:"可能过度为他人付出",majors:"心理学、教育、传媒、管理",careers:"教师、心理咨询师、培训师、管理者"},
  "ENTJ": {nick:"指挥官",core:"果断、有战略眼光、强领导力",cog:"关注长远目标与逻辑体系",beh:"直接、有魄力、目标导向",strength:"战略思维强、果断、执行力强",weakness:"可能显得强势、不耐烦",majors:"商科、法律、工程、管理",careers:"CEO、律师、管理顾问、战略经理"}
};

function getMbtiInfo(typeStr) {
  const upper = typeStr.toUpperCase().trim();
  const [base] = upper.split("-");
  const data = MBTI_DATA[base];
  if (!data) return { error: `未识别的 MBTI 类型:${typeStr}` };
  const tendency = upper.includes("-A") ? "Assertive(自信型):更稳定、更少自我怀疑"
                  : upper.includes("-T") ? "Turbulent(动荡型):更敏感、追求进步"
                  : "未提供 A/T 倾向";
  return {
    fullType: upper, baseType: base,
    nick: data.nick, core: data.core, cog: data.cog, beh: data.beh,
    strength: data.strength, weakness: data.weakness,
    fitMajors: data.majors, fitCareers: data.careers,
    tendency
  };
}

// ===== 霍兰德数据 =====
const HOLLAND_DIMS = {
  "R": {name:"现实型(Realistic)",core:"喜欢动手、实际操作、工具与机械",fit:"工程、技术、户外、农业、手工艺"},
  "I": {name:"研究型(Investigative)",core:"喜欢分析、思考、解决抽象问题",fit:"科研、数学、IT、医学研究、哲学"},
  "A": {name:"艺术型(Artistic)",core:"喜欢创造、表达、自我实现",fit:"艺术、设计、文学、音乐、传媒"},
  "S": {name:"社会型(Social)",core:"喜欢帮助他人、教育、合作",fit:"教育、心理咨询、社会工作、医疗"},
  "E": {name:"企业型(Enterprising)",core:"喜欢影响他人、领导、说服",fit:"管理、销售、法律、政治、创业"},
  "C": {name:"常规型(Conventional)",core:"喜欢结构化、数据、组织",fit:"会计、行政、金融、档案、IT 运维"}
};

const HOLLAND_CODES = {
  "RIA":"实干的研究者:动手 + 思考 + 创造,适合工程研发、实验技术",
  "IRE":"研究型工程师:思考 + 动手 + 影响,适合技术管理、研发管理",
  "IRA":"独立思考者:研究 + 动手 + 艺术,适合技术设计、产品研发",
  "IAS":"研究型学者:思考 + 艺术 + 服务,适合学术研究、深度分析",
  "IES":"研究型教育者:思考 + 影响 + 服务,适合学术教学、专业咨询",
  "ISE":"社会型研究者:服务 + 思考 + 影响,适合医学研究、咨询",
  "RAI":"现实型艺术家:动手 + 创造 + 思考,适合产品设计、建筑设计",
  "RSE":"社会型实干者:动手 + 服务 + 影响,适合体育教练、技术培训",
  "REI":"现实型管理者:动手 + 影响 + 思考,适合工程管理、项目经理",
  "RIC":"技术专家:动手 + 思考 + 常规,适合技术研发、数据分析",
  "ASE":"创意管理者:艺术 + 服务 + 影响,适合广告、传媒管理",
  "AES":"艺术家:艺术 + 影响 + 服务,适合表演、教育艺术",
  "AIS":"创意思考者:艺术 + 研究 + 服务,适合心理学、艺术治疗",
  "AIE":"研究型艺术家:艺术 + 思考 + 影响,适合高端设计、创意战略",
  "ASI":"服务型艺术家:艺术 + 社会 + 研究,适合艺术教育、文化研究",
  "SAI":"社会型艺术家:服务 + 艺术 + 研究,适合教育、心理辅导",
  "SAC":"社会服务者:服务 + 艺术 + 常规,适合教育管理、社会服务",
  "SIA":"教育研究者:服务 + 研究 + 艺术,适合学术教育、研究",
  "SIE":"服务型思考者:服务 + 研究 + 影响,适合医学、政策分析",
  "SCE":"社会管理者:服务 + 常规 + 影响,适合行政、教育管理",
  "ESC":"企业服务者:影响 + 服务 + 常规,适合销售管理、人力资源",
  "EAS":"艺术影响者:影响 + 艺术 + 服务,适合广告创意、艺术管理",
  "EIS":"研究型影响者:影响 + 研究 + 服务,适合战略咨询、专业服务",
  "EIC":"商业分析师:影响 + 研究 + 常规,适合金融分析、商业战略",
  "ECS":"社会型企业人:影响 + 常规 + 服务,适合销售管理、客户成功",
  "CEA":"企业艺术家:影响 + 常规 + 艺术,适合品牌管理、营销",
  "CIR":"常规型研究者:常规 + 研究 + 现实,适合数据科学、研发管理",
  "CIS":"研究型服务者:常规 + 研究 + 服务,适合数据分析、学术支持",
  "CIE":"商业研究者:常规 + 研究 + 影响,适合金融分析、咨询",
  "CRE":"技术管理者:常规 + 现实 + 影响,适合 IT 管理、项目经理",
  "CRI":"技术分析师:常规 + 现实 + 研究,适合工程、IT 运维",
  "CRS":"社会服务者:常规 + 现实 + 服务,适合行政支持、技术服务",
  "CSE":"社会支持者:常规 + 服务 + 影响,适合 HR、行政管理",
  "CSA":"艺术支持者:常规 + 服务 + 艺术,适合出版、文化机构",
  "CAI":"艺术分析师:常规 + 艺术 + 研究,适合设计研究、市场分析",
  "CAS":"社会支持者:常规 + 艺术 + 服务,适合教育管理、艺术行政",
  "CEI":"商业分析师:常规 + 影响 + 研究,适合金融分析、风险管理",
  "CES":"企业服务者:常规 + 影响 + 服务,适合销售支持、客户管理"
};

function getHollandInfo(scores) {
  const keys = Object.keys(scores);
  const expected = ["R","I","A","S","E","C"];
  if (keys.length !== 6 || !expected.every(k => keys.includes(k))) {
    return { error: "需要 R/I/A/S/E/C 六个维度的得分" };
  }

  const sorted = Object.entries(scores).sort((a,b) => b[1] - a[1]);
  const top3 = sorted.slice(0, 3).map(([k]) => k).join("");
  let codeExplain = HOLLAND_CODES[top3];
  if (!codeExplain) {
    const d0k = sorted[0][0], d0v = sorted[0][1];
    const d1k = sorted[1][0], d1v = sorted[1][1];
    const d2k = sorted[2][0], d2v = sorted[2][1];
    codeExplain = `${top3}:由 ${d0k}(${d0v})、${d1k}(${d1v})、${d2k}(${d2v}) 主导`;
  }

  const lowDims = sorted.filter(([_, v]) => v < 30).map(([k]) => HOLLAND_DIMS[k].name);
  const riskWarning = lowDims.length > 0
    ? `得分较低维度:${lowDims.join("、")} — 可能在这些领域的能力/意愿相对不足`
    : "无明显短板维度";

  const mainFit = sorted.slice(0, 3).map(([k]) => `${HOLLAND_DIMS[k].name}:${HOLLAND_DIMS[k].fit}`);

  return {
    scores, sorted, top3,
    codeExplain, mainFit, riskWarning,
    dimensions: HOLLAND_DIMS
  };
}

// ===== 紫微斗数简版 =====
const ZIWEI_STARS = {
  "紫微": {trait:"尊贵、领导力、追求完美", fit:"管理、决策、战略规划"},
  "天机": {trait:"智慧、谋略、分析能力强", fit:"研究、咨询、策划"},
  "太阳": {trait:"热情、表达、社交活跃", fit:"公关、传媒、教育"},
  "武曲": {trait:"刚毅、执行、财务敏锐", fit:"金融、工程、技术研发"},
  "天同": {trait:"温和、享福、人缘佳", fit:"服务、艺术、生活类"},
  "廉贞": {trait:"聪明、复杂、情感丰富", fit:"艺术、政治、复杂决策"},
  "天府": {trait:"稳重、收纳、理财", fit:"财务、行政、地产"},
  "太阴": {trait:"细腻、敏感、内敛", fit:"文学、心理、艺术"},
  "贪狼": {trait:"欲望、才艺、多才多艺", fit:"销售、艺术、跨界"},
  "巨门": {trait:"口才、争议、深度沟通", fit:"律师、辩论、教学"},
  "天相": {trait:"协调、辅助、文雅", fit:"行政、秘书、外交"},
  "天梁": {trait:"庇荫、年长、照顾他人", fit:"教育、医疗、咨询"},
  "七杀": {trait:"独立、冲劲、果断", fit:"创业、军警、技术攻坚"},
  "破军": {trait:"变革、创新、颠覆", fit:"创业、研发、改革"}
};

const ZIWEI_MONTH_STAR = {
  1:"紫微", 2:"天机", 3:"太阳", 4:"武曲",
  5:"天同", 6:"廉贞", 7:"天府", 8:"太阴",
  9:"贪狼", 10:"巨门", 11:"天相", 12:"天梁"
};

function getZiweiSummary(year, month, hour) {
  const mingStar = ZIWEI_MONTH_STAR[month];
  const shiyeStar = ZIWEI_MONTH_STAR[(month % 12) + 1];
  const caiboStar = ZIWEI_MONTH_STAR[((month + 1) % 12) + 1];
  return {
    mingGong: {
      name:"命宫", star: mingStar,
      trait: ZIWEI_STARS[mingStar].trait,
      fit: ZIWEI_STARS[mingStar].fit,
      hourEffect: (hour === 23 || hour === 0) ? "主星力量强化(子时)"
                : (hour >= 11 && hour < 13) ? "主星力量强化(午时)"
                : (hour >= 5 && hour < 7) ? "主星力量减弱(卯时)"
                : (hour >= 17 && hour < 19) ? "主星力量减弱(酉时)"
                : ""
    },
    shiyeGong: {
      name:"事业宫", star: shiyeStar,
      trait: ZIWEI_STARS[shiyeStar].trait,
      fit: ZIWEI_STARS[shiyeStar].fit
    },
    caiboGong: {
      name:"财帛宫", star: caiboStar,
      trait: ZIWEI_STARS[caiboStar].trait,
      fit: ZIWEI_STARS[caiboStar].fit
    },
    note: "本结果为简版紫微排盘,仅取核心三宫主星。完整紫微涉及 14 主星 + 12 宫位 + 四化飞星,建议使用专业排盘软件获取完整结果。"
  };
}

// ===== 专业库 =====
const MAJOR_LIBRARY = {
  "计算机科学与技术": {
    subs: ["人工智能","软件工程","网络空间安全","数据科学","计算机系统"],
    courses: ["数据结构","算法","操作系统","数据库","机器学习"],
    abilities: ["逻辑思维","抽象建模","代码实现","系统设计"],
    tags: ["I","T","INTJ","INTP","研究","逻辑","技术"],
    schools: ["清华大学","北京大学","上海交通大学","浙江大学","南京大学","电子科技大学"]
  },
  "软件工程": {
    subs: ["后端开发","前端开发","移动开发","DevOps","云原生"],
    courses: ["软件工程","数据库","Web 开发","软件测试","项目管理"],
    abilities: ["工程实现","团队协作","项目管理","问题解决"],
    tags: ["R","C","工程","实践","技术"],
    schools: ["北京航空航天大学","哈尔滨工业大学","华中科技大学","西安交通大学"]
  },
  "电子信息工程": {
    subs: ["通信工程","信号处理","嵌入式系统","物联网"],
    courses: ["电路分析","信号与系统","通信原理","数字信号处理"],
    abilities: ["硬件思维","数学基础","工程实现"],
    tags: ["R","I","工程","技术"],
    schools: ["电子科技大学","东南大学","西安电子科技大学","北京邮电大学"]
  },
  "数学与应用数学": {
    subs: ["基础数学","应用数学","金融数学","统计学"],
    courses: ["数学分析","高等代数","概率论","实变函数"],
    abilities: ["抽象思维","逻辑推理","数学建模"],
    tags: ["I","研究","逻辑","理论"],
    schools: ["北京大学","复旦大学","中国科学技术大学","南开大学"]
  },
  "人工智能": {
    subs: ["机器学习","深度学习","自然语言处理","计算机视觉","强化学习"],
    courses: ["机器学习","深度学习","计算机视觉","NLP","强化学习"],
    abilities: ["数学基础","算法能力","编程实现","领域知识"],
    tags: ["I","R","研究","技术","INTJ","INTP"],
    schools: ["清华大学","北京大学","浙江大学","上海交通大学","南京大学"]
  },
  "数据科学与大数据技术": {
    subs: ["大数据处理","数据挖掘","商业分析","数据可视化"],
    courses: ["统计学","数据库","数据挖掘","机器学习","大数据技术"],
    abilities: ["数据敏感度","统计思维","编程能力","业务理解"],
    tags: ["I","C","分析","研究"],
    schools: ["北京大学","清华大学","中国人民大学","复旦大学"]
  },
  "心理学": {
    subs: ["基础心理学","应用心理学","临床心理学","教育心理学"],
    courses: ["普通心理学","发展心理学","心理统计","实验心理学"],
    abilities: ["共情能力","观察分析","研究方法","沟通能力"],
    tags: ["S","I","INFJ","INFP","教育","服务"],
    schools: ["北京师范大学","华东师范大学","华南师范大学","西南大学"]
  },
  "教育学": {
    subs: ["教育学原理","课程与教学论","教育技术","学前教育"],
    courses: ["教育学原理","教育心理学","课程论","教学论"],
    abilities: ["表达能力","耐心","组织能力","学科理解"],
    tags: ["S","E","ESFJ","ENFJ","教育"],
    schools: ["北京师范大学","华东师范大学","东北师范大学","华中师范大学"]
  },
  "金融学": {
    subs: ["国际金融","公司金融","金融工程","投资学"],
    courses: ["货币银行学","国际金融","投资学","公司金融","金融衍生品"],
    abilities: ["数字敏感","分析能力","风险意识","沟通能力"],
    tags: ["E","C","ENTJ","ESTJ","商业"],
    schools: ["北京大学","清华大学","上海交通大学","中央财经大学","对外经济贸易大学"]
  },
  "会计学": {
    subs: ["财务会计","管理会计","审计","税务"],
    courses: ["基础会计","中级财务会计","成本会计","审计学"],
    abilities: ["细节敏感","数字能力","规则意识","责任心"],
    tags: ["C","ISTJ","规则","数据"],
    schools: ["中央财经大学","上海财经大学","对外经济贸易大学","东北财经大学"]
  },
  "汉语言文学": {
    subs: ["文学理论","古代文学","现当代文学","比较文学"],
    courses: ["文学概论","中国古代文学","中国现当代文学","外国文学"],
    abilities: ["文字能力","阅读理解","审美能力","思考深度"],
    tags: ["A","I","INFJ","INFP","创造"],
    schools: ["北京大学","复旦大学","南京大学","中国人民大学"]
  },
  "视觉传达设计": {
    subs: ["平面设计","UI/UX 设计","品牌设计","插画"],
    courses: ["设计基础","字体设计","版式设计","品牌设计","交互设计"],
    abilities: ["审美","软件技能","创意","沟通"],
    tags: ["A","R","设计","创意"],
    schools: ["中央美术学院","清华大学美术学院","中国美术学院","同济大学"]
  },
  "临床医学": {
    subs: ["内科","外科","儿科","妇产科","急诊"],
    courses: ["解剖学","生理学","病理学","诊断学","内科学"],
    abilities: ["记忆力","抗压能力","细致度","服务意识"],
    tags: ["S","R","I","服务","研究"],
    schools: ["北京协和医学院","上海交通大学医学院","复旦大学医学院","北京大学医学部"]
  }
};

// 头部雇主
const TOP_EMPLOYERS = {
  "计算机科学与技术": ["字节跳动","腾讯","阿里巴巴","华为","百度","美团","Microsoft","Google"],
  "软件工程": ["字节跳动","腾讯","阿里巴巴","美团","京东","拼多多","Meta"],
  "电子信息工程": ["华为","中兴","小米","OPPO","vivo","大疆","比亚迪"],
  "数学与应用数学": ["中金公司","高盛","摩根士丹利","各大高校","国家级科研院所"],
  "人工智能": ["字节跳动 AI Lab","百度","阿里达摩院","腾讯 AI Lab","商汤","旷视","OpenAI"],
  "数据科学与大数据技术": ["阿里巴巴","字节跳动","美团","滴滴","各大银行数据部门"],
  "心理学": ["高校/科研院所","三甲医院心理科","心理咨询机构","互联网公司 UX 研究"],
  "教育学": ["公立学校","新东方","好未来","猿辅导","各大高校"],
  "金融学": ["中金","中信证券","高盛","摩根士丹利","黑石","桥水基金"],
  "会计学": ["四大会计师事务所","各大企业财务部门"],
  "汉语言文学": ["出版社","传媒公司","互联网内容部门","文化机构"],
  "视觉传达设计": ["互联网公司设计部门","4A 广告公司","设计工作室","品牌咨询公司"],
  "临床医学": ["三甲医院","专科医院","医疗科研机构"]
};

// ===== MBTI 测试题 =====
const MBTI_QUESTIONS = [
  // E/I (1-4)
  { stem: "周末你更喜欢?", dim: "E", optionA: "和朋友出去聚会", optionB: "一个人在家看书追剧" },
  { stem: "在团队中你通常是?", dim: "E", optionA: "发言活跃带动气氛", optionB: "安静倾听后再发言" },
  { stem: "你更容易从哪种方式获得能量?", dim: "E", optionA: "和别人互动交流", optionB: "独处思考恢复精力" },
  { stem: "你更倾向于哪种表达方式?", dim: "E", optionA: "边想边说", optionB: "想好再说" },
  // S/N (5-8)
  { stem: "你更关注信息的哪一面?", dim: "N", optionA: "具体的事实和细节", optionB: "整体的概念和可能性" },
  { stem: "学习新知识时你更喜欢?", dim: "N", optionA: "按步骤一步步来", optionB: "先理解大框架" },
  { stem: "你更容易记住什么?", dim: "N", optionA: "发生过的事情细节", optionB: "事情背后的含义" },
  { stem: "你更倾向于相信?", dim: "N", optionA: "亲眼所见的事实", optionB: "自己的直觉和灵感" },
  // T/F (9-12)
  { stem: "做决定时你更依赖?", dim: "F", optionA: "逻辑和分析", optionB: "感受和价值观" },
  { stem: "朋友向你倾诉烦恼,你通常会?", dim: "F", optionA: "帮 ta 分析问题", optionB: "先安抚 ta 的情绪" },
  { stem: "你更在意什么?", dim: "F", optionA: "事情的对错", optionB: "人们的感受" },
  { stem: "评价方案时你更看重?", dim: "F", optionA: "是否合理高效", optionB: "是否大家都能接受" },
  // J/P (13-16)
  { stem: "你更喜欢哪种生活方式?", dim: "P", optionA: "按计划行事", optionB: "灵活随性" },
  { stem: "你的桌面/空间通常是?", dim: "P", optionA: "整洁有序", optionB: "看似乱但自己找得到" },
  { stem: "面对任务你通常是?", dim: "P", optionA: "早点做完再玩", optionB: "边玩边做" },
  { stem: "旅行前你通常会?", dim: "P", optionA: "做好详细攻略", optionB: "到了再说" }
];

function calcMbtiFromTest(answers) {
  // answers: [{ qIdx, score }]  score: 1=A(optionA), 2=B(optionB)
  let e = 0, i = 0, s = 0, n = 0, t = 0, f = 0, j = 0, p_ = 0;
  for (const a of answers) {
    const q = MBTI_QUESTIONS[a.qIdx];
    const choseB = a.score === 2;
    if (q.dim === "E") { if (choseB) i++; else e++; }
    if (q.dim === "N") { if (choseB) n++; else s++; }
    if (q.dim === "F") { if (choseB) f++; else t++; }
    if (q.dim === "P") { if (choseB) p_++; else j++; }
  }
  const type = (e >= i ? "E" : "I") + (n >= s ? "N" : "S") + (f >= t ? "F" : "T") + (p_ >= j ? "P" : "J");
  const scores = { E: e, I: i, S: s, N: n, T: t, F: f, J: j, P: p_ };
  return { type, scores };
}

// ===== 霍兰德测试题 =====
const HOLLAND_QUESTIONS = [
  { dim: "R", text: "修理或组装电器 / 家具" },
  { dim: "R", text: "户外运动或手工制作" },
  { dim: "R", text: "操作工具或机械设备" },
  { dim: "I", text: "做科学实验或研究分析" },
  { dim: "I", text: "解决数学或逻辑难题" },
  { dim: "I", text: "探索新理论或新知识" },
  { dim: "A", text: "画画、写作、音乐等创作" },
  { dim: "A", text: "欣赏艺术、设计或表演" },
  { dim: "A", text: "发挥想象力创造新东西" },
  { dim: "S", text: "帮助别人解决问题" },
  { dim: "S", text: "教别人新知识或技能" },
  { dim: "S", text: "参加志愿者或社团活动" },
  { dim: "E", text: "组织和领导团队活动" },
  { dim: "E", text: "说服别人接受你的观点" },
  { dim: "E", text: "参与竞赛或商业模拟" },
  { dim: "C", text: "整理数据或制作表格" },
  { dim: "C", text: "按流程和规则完成工作" },
  { dim: "C", text: "做详细的计划和记录" }
];

function calcHollandFromTest(answers) {
  const scores = { R: 0, I: 0, A: 0, S: 0, E: 0, C: 0 };
  for (const a of answers) {
    scores[a.dim] += a.score;
  }
  // 归一化到 0-100
  const maxPerDim = 5 * 3; // 每题最多5分,每个维度3题
  for (const k of Object.keys(scores)) {
    scores[k] = Math.round((scores[k] / maxPerDim) * 100);
  }
  return scores;
}

if (typeof window !== "undefined") {
  window.TianShuData = {
    MBTI_DATA, getMbtiInfo,
    MBTI_QUESTIONS, calcMbtiFromTest,
    HOLLAND_DIMS, getHollandInfo,
    HOLLAND_QUESTIONS, calcHollandFromTest,
    ZIWEI_STARS, getZiweiSummary,
    MAJOR_LIBRARY, TOP_EMPLOYERS
  };
}