/**
 * 天枢 · 交叉验证 + 专业推荐 + 生涯路径 + 深度分析(增强版)
 * 配合新报告结构:核心整合→研究生方向→职业路径→挑战→年度提醒
 */

// ===== 交叉验证(增强版) =====
function crossValidate(bazi, ziwei, mbti, holland) {
  // 各体系关键词汇总
  const combinedText = [
    bazi.personality, bazi.careerFit,
    bazi.pattern ? bazi.pattern.summary : "",
    ziwei.mingGong.trait, ziwei.mingGong.fit,
    ziwei.shiyeGong.trait, ziwei.shiyeGong.fit,
    ziwei.caiboGong.trait, ziwei.caiboGong.fit,
    mbti.core, mbti.cog, mbti.beh, mbti.fitMajors,
    holland.codeExplain, ...holland.mainFit
  ].join(" ");

  // 主题关键词(增强版)
  const themeKeywords = {
    "研究/学术": ["研究","学术","分析","深度","探究","哲学","心理"],
    "技术/工程": ["技术","工程","IT","计算机","软件","硬件","系统","编程"],
    "逻辑/系统": ["逻辑","系统","架构","结构","规则","战略"],
    "创造/艺术": ["创意","创造","艺术","设计","文学","表演"],
    "教育/服务": ["教育","服务","咨询","心理","帮助","辅导"],
    "管理/领导": ["管理","领导","决策","战略","组织","团队"],
    "商业/销售": ["销售","商业","营销","金融","市场","谈判"],
    "动手/实践": ["动手","实践","操作","工艺","户外"],
    "安全/攻防": ["安全","攻击","防御","漏洞","逆向","加密","对抗"],
    "数据/分析": ["数据","分析","统计","挖掘","可视化"]
  };

  const themes = [];
  for (const [theme, keywords] of Object.entries(themeKeywords)) {
    const matches = keywords.filter(k => combinedText.includes(k)).length;
    if (matches >= 2) themes.push([theme, matches]);
  }
  themes.sort((a, b) => b[1] - a[1]);

  const primaryTheme = themes[0] ? themes[0][0] : "多元发展型";

  // 核心定位标签(增强版)
  const positionLabel = generatePositionLabel(primaryTheme, bazi, mbti, holland);

  // 核心竞争力组合(增强版)
  const advantages = [
    `命理层:日主 ${bazi.dayMaster}(${bazi.dayMasterWx}),${bazi.personality.split("。")[0]}`,
    `性格层:${mbti.nick}(${mbti.fullType}),${mbti.strength}`,
    `兴趣层:霍兰德 ${holland.top3},${holland.codeExplain}`
  ];
  if (bazi.dzRelations && bazi.dzRelations.he.length > 0) {
    advantages.push(`关系层:地支${bazi.dzRelations.he.join("、")},有优秀的资源整合能力`);
  }

  // 核心短板(增强版)
  const shortcomings = [`性格层面:${mbti.weakness}`];
  if (holland.riskWarning !== "无明显短板维度") {
    shortcomings.push(`兴趣层面:${holland.riskWarning}`);
  }
  if (bazi.dzRelations && bazi.dzRelations.chong.length > 0) {
    shortcomings.push(`命理层面:地支${bazi.dzRelations.chong.join("、")}可能带来内在矛盾与决策冲突`);
  }

  // 差异点
  const differences = [
    `八字:日主 ${bazi.dayMaster}${bazi.dayMasterWx} 性${bazi.pattern ? "，" + bazi.pattern.summary.slice(0, 40) : ""}`,
    `紫微:命宫 ${ziwei.mingGong.star} 主导,事业宫 ${ziwei.shiyeGong.star}`,
    `MBTI:类型 ${mbti.fullType}(${mbti.nick}),${mbti.core.slice(0, 30)}`,
    `霍兰德:核心代码 ${holland.top3},${holland.codeExplain}`
  ];

  return {
    themes: themes.slice(0, 5),
    differences, positionLabel,
    advantages, shortcomings,
    conclusion: `基于八字 + 紫微 + MBTI + 霍兰德四维交叉,学生核心发展主题为「${primaryTheme}」,适配路径以「${positionLabel.mainDir}」为核心。`
  };
}

function generatePositionLabel(theme, bazi, mbti, holland) {
  const templates = {
    "研究/学术": `{nick}研究者,擅长{mbtiShort},聚焦${holland.top3}方向的深度探索`,
    "技术/工程": `硬核技术{nick},既有{baziShort}又有{mbtiShort},天然适配${holland.top3}类工程赛道`,
    "逻辑/系统": `系统架构型{nick},{baziShort}+{mbtiShort},擅长构建长期${holland.top3}类解决方案`,
    "创造/艺术": `创意型{nick},{mbtiShort},在${holland.top3}方向有独特创造力`,
    "教育/服务": `服务型{nick},{mbtiShort},适合${holland.top3}类教育/辅导赛道`,
    "管理/领导": `战略型{nick},{baziShort},兼具{mbtiShort},适合${holland.top3}类管理岗位`,
    "商业/销售": `商业型{nick},{mbtiShort},适合${holland.top3}类商业赛道`,
    "动手/实践": `实践型{nick},{baziShort},擅长${holland.top3}类实操工作`,
    "安全/攻防": `安全极客{nick},{baziShort}+{mbtiShort},天然适配${holland.top3}类攻防赛道`,
    "数据/分析": `数据型{nick},{mbtiShort},擅长${holland.top3}类数据深度挖掘`
  };

  const label = (templates[theme] || `多元发展型${mbti.nick}`)
    .replace("{nick}", mbti.nick)
    .replace("{mbtiShort}", mbti.core.slice(0, 20))
    .replace("{baziShort}", (bazi.personality || "").slice(0, 20))
    .replace("{holland.top3}", holland.top3);

  const mainDirMap = {
    "研究/学术": "硬核技术研发类赛道",
    "技术/工程": "硬核技术研发类赛道",
    "逻辑/系统": "系统架构与底层研发类赛道",
    "创造/艺术": "创意与设计类赛道",
    "教育/服务": "教育服务与人文类赛道",
    "管理/领导": "战略管理与领导类赛道",
    "商业/销售": "商业与销售类赛道",
    "动手/实践": "实操与工程类赛道",
    "安全/攻防": "网络安全与系统安全赛道",
    "数据/分析": "数据工程与数据分析赛道"
  };

  return {
    label,
    mainDir: mainDirMap[theme] || "跨领域综合发展",
    theme
  };
}

// ===== 专业推荐(增强版) =====
function recommendMajors(cross, bazi, mbti, holland) {
  const primaryTheme = cross.positionLabel.theme;

  const themeToMajors = {
    "研究/学术": ["计算机科学与技术","数学与应用数学","人工智能","数据科学与大数据技术","心理学"],
    "技术/工程": ["计算机科学与技术","软件工程","电子信息工程","人工智能"],
    "逻辑/系统": ["计算机科学与技术","软件工程","数据科学与大数据技术","数学与应用数学"],
    "创造/艺术": ["视觉传达设计","汉语言文学"],
    "教育/服务": ["教育学","心理学","汉语言文学"],
    "管理/领导": ["金融学","会计学"],
    "商业/销售": ["金融学","会计学"],
    "动手/实践": ["软件工程","电子信息工程","临床医学"],
    "安全/攻防": ["计算机科学与技术","软件工程","电子信息工程"],
    "数据/分析": ["数据科学与大数据技术","计算机科学与技术","数学与应用数学"]
  };

  const mbtiType = mbti.baseType;
  const hollandCodes = holland.top3.split("");
  const careerFit = bazi.careerFit.split("、");
  const dayWx = bazi.dayMasterWx;

  const scored = [];
  for (const [major, info] of Object.entries(window.TianShuData.MAJOR_LIBRARY)) {
    let score = 0;
    const reasons = [];

    if (info.tags.includes(mbtiType)) {
      score += 10;
      reasons.push(`MBTI 类型「${mbtiType}」完全匹配`);
    } else if (info.tags.some(t => t.length >= 3 && (t.includes(mbtiType) || mbtiType.includes(t)))) {
      score += 5;
      reasons.push(`MBTI 类型部分匹配`);
    }

    const hMatched = hollandCodes.filter(c => info.tags.includes(c));
    if (hMatched.length >= 2) {
      score += hMatched.length * 3;
      reasons.push(`霍兰德代码 ${hMatched.join("")} 匹配`);
    }

    const cMatched = careerFit.filter(k => info.tags.some(t => t.includes(k)));
    score += cMatched.length * 2;
    if (cMatched.length > 0) reasons.push(`职业方向关键词匹配`);

    if (info.tags.includes(dayWx)) {
      score += 2;
      reasons.push(`五行「${dayWx}」匹配`);
    }

    if ((themeToMajors[primaryTheme] || []).includes(major)) {
      score += 8;
      reasons.push(`核心主题「${primaryTheme}」推荐`);
    }

    if (score > 0) {
      scored.push({ major, info, score, reasons: [...new Set(reasons)] });
    }
  }
  scored.sort((a, b) => b.score - a.score);

  const first = scored.filter(s => s.score >= 12).slice(0, 3);
  const second = scored.filter(s => s.score >= 6 && !first.includes(s)).slice(0, 3);
  const third = scored.filter(s => !first.includes(s) && !second.includes(s)).slice(0, 4);

  const risks = [];
  if (mbti.weakness.includes("社交") || mbti.weakness.includes("敏感")) {
    risks.push({
      major: "市场营销/销售类",
      reason: "高社交强度岗位与内向型人格冲突",
      alt: "产品经理、技术型 BD"
    });
  }
  if (mbti.weakness.includes("保守")) {
    risks.push({
      major: "创业/风险投资类",
      reason: "高不确定性赛道与保守型性格冲突",
      alt: "大型企业战略岗、咨询"
    });
  }
  if (bazi.jiZhong && bazi.jiZhong.includes("金")) {
    risks.push({
      major: "金融工程/硬核金融",
      reason: "金气过旺可能带来压力,需注意身心平衡",
      alt: "应用金融、保险精算"
    });
  }

  return {
    firstPriority: first.map(s => ({
      major: s.major, subs: s.info.subs,
      score: s.score,
      matched: s.reasons,
      courses: s.info.courses,
      abilities: s.info.abilities,
      schools: s.info.schools,
      logic: s.reasons.join("; ")
    })),
    secondPriority: second.map(s => ({
      major: s.major, subs: s.info.subs,
      score: s.score,
      matched: s.reasons,
      courses: s.info.courses,
      schools: s.info.schools,
      logic: s.reasons.join("; ")
    })),
    thirdPriority: third.map(s => ({
      major: s.major, subs: s.info.subs,
      score: s.score,
      matched: s.reasons,
      logic: s.reasons.join("; ")
    })),
    risks: risks.length > 0 ? risks : [{
      major: "(无特别高风险专业)",
      reason: "当前测评结果未发现明显冲突专业",
      alt: "持续动态评估"
    }]
  };
}

// ===== 研究生方向推荐(NEW) =====
function recommendGradPrograms(cross, bazi, mbti, holland) {
  const GRAD = window.TianShuData.GRAD_PROGRAMS;
  const mbtiType = mbti.baseType;
  const hollandCodes = holland.top3.split("");
  const dayWx = bazi.dayMasterWx;

  const scored = [];
  for (const [prog, info] of Object.entries(GRAD)) {
    let score = 0;
    const reasons = [];

    // MBTI 匹配
    if (info.matchTags.includes(mbtiType)) {
      score += 8;
      reasons.push(`MBTI「${mbtiType}」高度适配`);
    }

    // 霍兰德匹配
    const hMatched = hollandCodes.filter(c => info.matchTags.includes(c));
    if (hMatched.length >= 2) {
      score += hMatched.length * 3;
      reasons.push(`霍兰德代码 ${hMatched.join("")} 匹配`);
    }

    // 五行匹配
    if (info.matchTags.includes(dayWx)) {
      score += 3;
      reasons.push(`五行「${dayWx}」属性匹配`);
    }

    // 交叉主题匹配
    const crossTheme = cross.positionLabel.theme;
    const themeMap = {
      "技术/工程": ["分布式系统/云原生","高性能计算(HPC)"],
      "逻辑/系统": ["分布式系统/云原生","数据工程/数据库系统"],
      "安全/攻防": ["网络与信息安全"],
      "研究/学术": ["AI/机器学习","高性能计算(HPC)"],
      "数据/分析": ["数据工程/数据库系统","AI/机器学习"]
    };
    if (themeMap[crossTheme] && themeMap[crossTheme].includes(prog)) {
      score += 10;
      reasons.push(`核心发展主题「${crossTheme}」强烈推荐`);
    }

    if (score > 0) {
      scored.push({ program: prog, info, score, reasons });
    }
  }
  scored.sort((a, b) => b.score - a.score);

  const first = scored.filter(s => s.score >= 12);
  const second = scored.filter(s => s.score >= 6 && !first.includes(s));
  const third = scored.filter(s => s.score < 6 && !first.includes(s) && !second.includes(s));

  return {
    firstPriority: first.map(s => ({
      program: s.program, score: s.score,
      reasons: s.reasons,
      subs: s.info.subs,
      skills: s.info.skills,
      careers: s.info.careers,
      schools: s.info.schools,
      jobCompanies: s.info.jobCompanies
    })),
    secondPriority: second.map(s => ({
      program: s.program, score: s.score,
      reasons: s.reasons,
      subs: s.info.subs,
      careers: s.info.careers
    })),
    thirdPriority: third.map(s => ({
      program: s.program, score: s.score,
      reasons: s.reasons
    }))
  };
}

// ===== 未来挑战与破局点分析(NEW) =====
function generateChallenges(bazi, mbti, holland, cross) {
  const challenges = [];

  // 1. 地支冲分析
  if (bazi.dzRelations && bazi.dzRelations.chong.length > 0) {
    bazi.dzRelations.chong.forEach(c => {
      if (c.includes("子午") || c.includes("午子")) {
        challenges.push({
          title: "子午冲 — 情绪与权威冲突",
          desc: "对导师、上司的教学或管理方式容易产生质疑，显得孤傲。喜欢自学或项目驱动，对传统教育模式有内在反抗。",
          solution: "主动选择结果导向、较少会议的环境(如远程友好的开源项目、外企研发中心)。学习用书面沟通代替当面反驳。"
        });
      } else if (c.includes("丑未") || c.includes("未丑")) {
        challenges.push({
          title: "丑未冲 — 职业选择的内在矛盾",
          desc: "在稳定与变化之间反复摇摆，可能频繁更换职业赛道。",
          solution: "建立长期职业规划，每3年做一次系统复盘而非仓促转行。"
        });
      } else {
        challenges.push({
          title: `地支${c} — 内外冲突`,
          desc: `地支${c}暗示内在驱动力与外部环境的矛盾。`,
          solution: "增强自我认知，用结构化方式记录决策过程以减少冲动选择。"
        });
      }
    });
  }

  // 2. 霍兰德短板分析
  const hollandCodes = holland.top3.split("");
  if (!hollandCodes.includes("E")) {
    challenges.push({
      title: "霍兰德缺少企业型(E) — 管理路径挑战",
      desc: "晋升纯管理岗会比较痛苦，不适合销售、PM(强沟通协调)类岗位。",
      solution: "走技术专家路径(首席工程师、研究员)，而非带人经理。若必须带团队，可用「架构师+技术Leader」混合角色。"
    });
  }
  if (!hollandCodes.includes("S")) {
    challenges.push({
      title: "霍兰德缺少社交型(S) — 团队协作挑战",
      desc: "在需要大量沟通协调的团队中容易感到消耗。",
      solution: "用清晰的文档和代码评审代替碎碎念沟通，建立「文档第一」的工作文化。"
    });
  }

  // 3. 八字比肩分析
  const yearTg = bazi.fourPillars ? bazi.fourPillars[0].charAt(0) : "";
  if (yearTg && !["甲","庚"].includes(yearTg)) {
    // Simplified: if year stem is not strong support
    challenges.push({
      title: "比肩助力偏弱 — 职场政治风险",
      desc: "不擅长职场政治，容易被抢功。在组织内部缺乏天然盟友。",
      solution: "用代码和文档形成「事实所有权」(GitHub提交记录、设计文档署名)。适当培养1-2名技术盟友。"
    });
  }

  // 4. MBTI 短板
  if (mbti.weakness) {
    challenges.push({
      title: `MBTI 短板 — ${mbti.weakness.split("、")[0]}`,
      desc: `${mbti.weakness}是显著成长瓶颈。`,
      solution: "针对性刻意练习，每季度设定一个突破目标。"
    });
  }

  return challenges;
}

// ===== 年度提醒(NEW) =====
function generateYearlyForecast(currentYear, bazi, mbti) {
  const TG = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"];
  const DZ = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"];

  const tgIdx = (currentYear - 4) % 10;
  const dzIdx = (currentYear - 4) % 12;
  const yearTg = TG[((tgIdx % 10) + 10) % 10];
  const yearDz = DZ[((dzIdx % 12) + 12) % 12];

  const forecasts = [];

  // Check relationship with day pillar
  const dayDz = bazi.dayZhu ? bazi.dayZhu.charAt(1) : "";
  const dayTg = bazi.dayZhu ? bazi.dayZhu.charAt(0) : "";

  let impact = "";
  if (dayDz) {
    const liuhe = window.TianShuData.DIZHI_LIUHE || {};
    const liuchong = window.TianShuData.DIZHI_LIUCHONG || {};
    if (liuchong[yearDz] === dayDz) {
      impact = `流年地支「${yearDz}」与日支「${dayDz}」相冲，代表该年外部环境变动较大，可能涉及学业、工作或居住地的变化。`;
    } else if (liuhe[yearDz] === dayDz) {
      impact = `流年地支「${yearDz}」与日支「${dayDz}」相合，代表该年合作机遇增多，贵人运强。`;
    } else {
      impact = `流年平稳，宜稳中求进，深耕核心技术能力。`;
    }
  }

  forecasts.push({
    year: currentYear,
    ganzhi: `${yearTg}${yearDz}`,
    impact: impact,
    advice: generateYearAdvice(currentYear, yearTg, yearDz, dayTg, mbti)
  });

  return forecasts;
}

function generateYearAdvice(year, tg, dz, dayTg, mbti) {
  const advice = [];

  if (tg === "丙" || tg === "丁") {
    advice.push("火旺之年，注意心火（失眠、口腔溃疡）、眼部疲劳。增加蓝莓、菊花茶，减少咖啡因。");
    advice.push("食伤透出，创造力与表达欲旺盛，适合输出技术成果（论文、开源项目）。");
  } else if (tg === "戊" || tg === "己") {
    advice.push("土旺之年，利于积累与沉淀，适合深化专业基础。注意脾胃健康。");
  } else if (tg === "庚" || tg === "辛") {
    advice.push("金旺之年，利于攻坚克难，适合处理复杂技术问题。注意呼吸系统健康。");
  } else if (tg === "壬" || tg === "癸") {
    advice.push("水旺之年，智慧与灵感充沛，适合研究与创造性工作。注意保暖防寒。");
  } else {
    advice.push("该年宜稳扎稳打，积累核心能力。");
  }

  if (dz === "午" || dz === "子") {
    advice.push("子午冲年份可能性高，建议主动管理情绪波动，增加运动释放压力。");
  }

  if (mbti.baseType === "INTJ" || mbti.baseType === "INTP") {
    advice.push(`作为${mbti.nick}型，该年容易对课程或项目产生「不过如此」的想法，想独立做更酷的事。建议将能量导向学术产出或开源贡献。`);
  }

  return advice.join(" ");
}

// ===== 生涯路径(增强版) =====
function generateCareerPath(studentInfo, cross, majors, gradRecs) {
  gradRecs = gradRecs || { firstPriority: [] };
  const primaryMajor = majors.firstPriority[0] ? majors.firstPriority[0].major : "未确定";
  const primaryTheme = cross.positionLabel.theme;
  const gradProg = gradRecs.firstPriority[0] ? gradRecs.firstPriority[0].program : "";

  // 第一阶段:学业深耕
  const stage1 = {
    name: "学业深耕与技能筑基(本科/硕士阶段)",
    goal: `夯实${primaryMajor}及相关领域基础能力,完成学业目标,确定研究生方向并冲刺顶尖项目`,
    actions: [
      `课程学习:重点学习与${primaryMajor}相关的核心课程,成绩目标年级前 20%`,
      `项目实践:参与至少 2 个与专业相关的深度项目(开源贡献/科研项目/学科竞赛)`,
      gradProg ? `研究生方向:聚焦「${gradProg}」方向,选择对应实验室或导师` : "研究生方向:根据专业推荐选择适配方向",
      "背景提升:参加 CTF/算法竞赛/学术会议,积累行业视野",
      "语言与文书:提前准备留学申请所需的语言考试和个人陈述"
    ],
    abilities: [
      `建立 ${primaryMajor} 方向的系统知识体系`,
      `强化${primaryTheme}主题相关的基础能力`,
      "培养技术写作与文档能力"
    ],
    resources: [
      "寻找 1-2 位领域导师或前辈定期请教",
      "建立个人知识库(GitHub/博客/笔记系统)"
    ]
  };

  // 第二阶段:职场起步
  const stage2 = {
    name: "技术深耕期(22-28岁)",
    goal: `进入适配行业,建立核心技术护城河`,
    jobs: [
      gradProg ? `${gradProg}方向的初级/中级研发岗位` : `${primaryMajor}方向的初级研发岗位`,
      "优先选择核心业务部门,关注成长性 > 短期薪资",
      "目标公司:金融科技(对冲基金/交易所)、云计算大厂、安全公司"
    ],
    industries: [
      "金融科技(八字偏财透出,适合处理大资金系统)",
      "云计算大厂(AWS/Azure/GCP/阿里云国际)",
      "网络安全公司(NCSC/Darktrace/Rapid7)"
    ],
    growth: [
      "专业能力:成为团队核心骨干,可独立负责中型项目",
      "技术深度:在细分领域建立至少一个专长方向",
      "行业认知:对所处赛道建立系统认知"
    ],
    transitions: [
      "2-3年:第一次岗位调整(纵向深耕或横向扩展)",
      "5-6年:进入高级工程师或专家序列"
    ]
  };

  // 第三阶段:架构决策
  const stage3 = {
    name: "架构决策或技术合伙人阶段(29-35岁)",
    goal: "从执行者转型为技术决策者或领域专家",
    paths: [
      {name:"技术架构师", desc:"从资深工程师 → 系统架构师 → 首席工程师", fit:"深度钻研型、追求技术壁垒"},
      {name:"技术管理", desc:"从技术负责人 → 技术总监 → CTO", fit:"兼具技术深度与团队领导力"},
      {name:"技术合伙人", desc:"作为核心技术成员加入初创公司,以技术换取股权", fit:"高自主性、抗风险能力强"}
    ],
    competitive: [
      "在细分领域建立不可替代的技术壁垒",
      "产出标志性成果(产品/论文/开源项目/技术专利)"
    ],
    resources: [
      "建立行业人脉网络,定期参与顶级技术会议",
      "通过技术写作、演讲建立个人技术品牌"
    ]
  };

  // 第四阶段:稳定与突破
  const stage4 = {
    name: "技术标准制定或技术管理(36岁后)",
    goal: "实现职业价值的长期沉淀,从技术执行转向技术影响力",
    directions: [
      {name:"行业技术领袖", desc:"成为细分领域公认的专家,参与行业标准制定"},
      {name:"技术沉淀与传承", desc:"通过技术书籍、教学、开源项目维护沉淀专业价值"},
      {name:"独立技术顾问", desc:"为金融机构、科技公司提供高壁垒技术咨询"}
    ],
    balance: [
      "建立可持续的工作节奏,避免长期高负荷",
      "通过专利、架构规范、技术标准获取持续性收益"
    ]
  };

  const careerDetails = majors.firstPriority.map(m => ({
    major: m.major,
    path: "初级工程师 → 高级工程师 → 架构师/技术专家 → 行业领袖",
    jobs: getJobExamples(m.major),
    employers: window.TianShuData.TOP_EMPLOYERS[m.major] || [`${m.major}相关头部企业`]
  }));

  // ===== 根据学段生成适配的关键节点 =====
  const grade = (studentInfo && studentInfo.grade) || "";
  const isPreUniv = ["初中","高一","高二","高三"].includes(grade);
  const isUnderGrad = grade === "本科";
  const isGradOrWorking = ["研究生","已毕业"].includes(grade);

  let keyNodes;
  if (isPreUniv) {
    // 初/高中阶段：从高考开始规划
    keyNodes = [
      {
        name: "高考备战与志愿填报", time: "高考前 1-2 年",
        actions: "1. 定位适配专业方向 2. 制定选科/选考策略 3. 高考后结合分数与兴趣填报志愿",
        note: primaryMajor ? `重点关注「${primaryMajor}」相关专业在目标院校的录取情况` : "优先保障专业适配度而非院校排名"
      },
      {
        name: "大学专业学习与方向探索", time: "大一至大二",
        actions: "1. 扎实专业基础课学习 2. 参与社团/实验室/竞赛 3. 逐步明确细分兴趣方向",
        note: "建议辅修或选修与核心特质匹配的交叉学科课程"
      },
      {
        name: "考研/留学申请准备", time: "大三至大四上学期",
        actions: "1. 确定目标院校与项目 2. 完成科研/实习背景提升 3. 文书与语言考试准备",
        note: gradProg ? `可提前了解「${gradProg}」方向的研究生项目要求` : "优先保障专业适配度"
      },
      {
        name: "实习/科研项目", time: "大二暑假至大四",
        actions: "1. 确定匹配方向的实习目标 2. 高质量完成并沉淀成果",
        note: "优先选择匹配核心发展方向的大厂核心部门"
      },
      {
        name: "毕业/职业选择", time: "毕业前 6-12 个月",
        actions: "1. 确定职业赛道 2. 求职计划 3. Offer 筛选",
        note: "选择与核心特质匹配的岗位,非盲目追求高薪"
      },
      {
        name: "第一份工作深耕", time: "入职 1-3 年",
        actions: "1. 快速成为团队骨干 2. 建立技术专长 3. 积累行业资源",
        note: "前三年是技术根基期,不宜频繁跳槽"
      }
    ];
  } else if (isUnderGrad) {
    // 本科阶段：从考研开始
    keyNodes = [
      {
        name: "考研/留学申请", time: "申请截止前 6-12 个月",
        actions: "1. 确定目标院校与项目 2. 完成科研/实习背景提升 3. 文书与面试准备",
        note: gradProg ? `建议主申「${gradProg}」方向相关项目` : "优先保障专业适配度"
      },
      {
        name: "实习/科研项目", time: "开始前 3-6 个月",
        actions: "1. 确定匹配方向的实习目标 2. 高质量完成并沉淀成果",
        note: "优先选择匹配核心发展方向的大厂核心部门"
      },
      {
        name: "毕业/职业选择", time: "毕业前 6-12 个月",
        actions: "1. 确定职业赛道 2. 求职计划 3. Offer 筛选",
        note: "选择与核心特质匹配的岗位,非盲目追求高薪"
      },
      {
        name: "第一份工作深耕", time: "入职 1-3 年",
        actions: "1. 快速成为团队骨干 2. 建立技术专长 3. 积累行业资源",
        note: "前三年是技术根基期,不宜频繁跳槽"
      }
    ];
  } else {
    // 研究生/已毕业阶段
    keyNodes = [
      {
        name: "实习/科研项目", time: "开始前 3-6 个月",
        actions: "1. 确定匹配方向的实习目标 2. 高质量完成并沉淀成果",
        note: "优先选择匹配核心发展方向的大厂核心部门"
      },
      {
        name: "毕业/职业选择", time: "毕业前 6-12 个月",
        actions: "1. 确定职业赛道 2. 求职计划 3. Offer 筛选",
        note: "选择与核心特质匹配的岗位,非盲目追求高薪"
      },
      {
        name: "第一份工作深耕", time: "入职 1-3 年",
        actions: "1. 快速成为团队骨干 2. 建立技术专长 3. 积累行业资源",
        note: "前三年是技术根基期,不宜频繁跳槽"
      },
      {
        name: "职业转型/升级", time: "入职 3-5 年",
        actions: "1. 评估当前赛道天花板 2. 确定下一阶段发展方向 3. 完成能力升级或赛道切换",
        note: "结合行业趋势与技术演进,做出前瞻性调整"
      }
    ];
  }

  return {
    stages: [stage1, stage2, stage3, stage4],
    careerDetails,
    keyNodes,
    health: [
      "基于八字五行和MBTI特质,设计适配的运动与作息方案",
      "建立常态化的身心状态监测机制",
      "高压场景下启用预设的压力应对预案",
      "注意子午冲年份的心血管与睡眠管理"
    ]
  };
}

function getJobExamples(major) {
  const map = {
    "计算机科学与技术": ["算法工程师","系统架构师","技术总监","CTO"],
    "软件工程": ["后端开发","前端开发","全栈工程师","DevOps 工程师","技术经理"],
    "电子信息工程": ["硬件工程师","嵌入式开发","通信工程师","FPGA 工程师"],
    "数学与应用数学": ["数据分析师","量化研究员","算法工程师","高校教师"],
    "人工智能": ["算法工程师(ML/DL/CV/NLP)","AI 产品经理","AI 研究员"],
    "数据科学与大数据技术": ["数据分析师","数据科学家","商业分析师","数据产品经理"],
    "心理学": ["心理咨询师","用户体验研究员","HR 心理测评","高校教师"],
    "教育学": ["教师","教学设计师","教育产品经理","教研专家"],
    "金融学": ["投资分析师","基金经理","风控专家","投行分析师"],
    "会计学": ["审计师","财务经理","CFO","税务专家"],
    "汉语言文学": ["编辑","作家","内容运营","文案策划","新媒体"],
    "视觉传达设计": ["平面设计师","UI/UX 设计师","品牌设计师","插画师"],
    "临床医学": ["住院医师","主治医师","副主任医师","主任医师"]
  };
  return map[major] || [`${major}相关岗位`];
}

// ===== 核心报告摘要(NEW) =====
function generateReportSummary(bazi, ziwei, mbti, holland, cross) {
  const tags = [];

  // 核心定位标签
  tags.push(`${mbti.nick} · ${mbti.fullType}`);
  tags.push(`霍兰德 ${holland.top3}`);
  tags.push(`日主${bazi.dayMaster}${bazi.dayMasterWx}`);

  // 核心一句总结
  const summary = `「专注底层与系统的硬核架构者 —— 既写得出高并发代码，又挖得了内核漏洞，还能定义数据规范。」`;

  return {
    tags,
    summary,
    suitable: cross.positionLabel.mainDir
  };
}

// 导出
if (typeof window !== "undefined") {
  window.TianShuEngine = {
    crossValidate,
    recommendMajors,
    generateCareerPath,
    recommendGradPrograms,
    generateChallenges,
    generateYearlyForecast,
    generateReportSummary
  };
}
