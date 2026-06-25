/**
 * 天枢 · 交叉验证 + 专业推荐 + 生涯路径(纯 JS 版)
 */

// ===== 交叉验证 =====
function crossValidate(bazi, ziwei, mbti, holland) {
  // 各体系关键词汇总
  const combinedText = [
    bazi.personality, bazi.careerFit,
    ziwei.mingGong.trait, ziwei.mingGong.fit,
    ziwei.shiyeGong.trait, ziwei.shiyeGong.fit,
    ziwei.caiboGong.trait, ziwei.caiboGong.fit,
    mbti.core, mbti.cog, mbti.beh, mbti.fitMajors,
    holland.codeExplain, ...holland.mainFit
  ].join(" ");

  // 主题关键词
  const themeKeywords = {
    "研究/学术": ["研究","学术","分析","深度","探究","哲学","心理"],
    "技术/工程": ["技术","工程","IT","计算机","软件","硬件","系统"],
    "逻辑/系统": ["逻辑","系统","架构","结构","规则","战略"],
    "创造/艺术": ["创意","创造","艺术","设计","文学","表演"],
    "教育/服务": ["教育","服务","咨询","心理","帮助","辅导"],
    "管理/领导": ["管理","领导","决策","战略","组织","团队"],
    "商业/销售": ["销售","商业","营销","金融","市场","谈判"],
    "动手/实践": ["动手","实践","操作","工艺","户外"]
  };

  const themes = [];
  for (const [theme, keywords] of Object.entries(themeKeywords)) {
    const matches = keywords.filter(k => combinedText.includes(k)).length;
    if (matches >= 2) themes.push([theme, matches]);
  }
  themes.sort((a, b) => b[1] - a[1]);

  const primaryTheme = themes[0] ? themes[0][0] : "多元发展型";

  // 核心定位标签
  const positionLabel = generatePositionLabel(primaryTheme, bazi, mbti, holland);

  // 核心竞争力组合
  const advantages = [
    `天赋层:日主 ${bazi.dayMaster}(${bazi.dayMasterWx}),${bazi.personality}`,
    `性格层:${mbti.nick}(${mbti.fullType}),${mbti.strength}`,
    `兴趣层:霍兰德 ${holland.top3},${holland.codeExplain}`
  ];

  // 核心短板
  const shortcomings = [`性格:${mbti.weakness}`];
  if (holland.riskWarning !== "无明显短板维度") {
    shortcomings.push(`能力:${holland.riskWarning}`);
  }

  // 差异点
  const differences = [
    `八字:偏 ${bazi.dayMasterWx} 性,核心适配 ${bazi.careerFit.split("、")[0]}`,
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
    "动手/实践": `实践型{nick},{baziShort},擅长${holland.top3}类实操工作`
  };

  const label = (templates[theme] || `多元发展型${mbti.nick}`)
    .replace("{nick}", mbti.nick)
    .replace("{mbtiShort}", mbti.core.slice(0, 20))
    .replace("{baziShort}", bazi.personality.slice(0, 20))
    .replace("{holland.top3}", holland.top3);

  const mainDirMap = {
    "研究/学术": "硬核技术研发类赛道",
    "技术/工程": "硬核技术研发类赛道",
    "逻辑/系统": "系统架构与底层研发类赛道",
    "创造/艺术": "创意与设计类赛道",
    "教育/服务": "教育服务与人文类赛道",
    "管理/领导": "战略管理与领导类赛道",
    "商业/销售": "商业与销售类赛道",
    "动手/实践": "实操与工程类赛道"
  };

  return {
    label,
    mainDir: mainDirMap[theme] || "跨领域综合发展",
    theme
  };
}

// ===== 专业推荐 =====
function recommendMajors(cross, bazi, mbti, holland) {
  const studentTags = [];
  studentTags.push(bazi.dayMasterWx);
  studentTags.push(bazi.minWx);
  studentTags.push(...bazi.xiZhong);
  studentTags.push(...bazi.careerFit.split("、"));
  studentTags.push(mbti.baseType);
  studentTags.push(...mbti.fitMajors.split("、"));
  studentTags.push(...holland.top3.split(""));

  const primaryTheme = cross.positionLabel.theme;

  // 主题 → 专业映射
  const themeToMajors = {
    "研究/学术": ["计算机科学与技术","数学与应用数学","人工智能","数据科学与大数据技术","心理学"],
    "技术/工程": ["计算机科学与技术","软件工程","电子信息工程","人工智能"],
    "逻辑/系统": ["计算机科学与技术","软件工程","数据科学与大数据技术"],
    "创造/艺术": ["视觉传达设计","汉语言文学"],
    "教育/服务": ["教育学","心理学"],
    "管理/领导": ["金融学"],
    "商业/销售": ["金融学"],
    "动手/实践": ["软件工程","电子信息工程"]
  };

  const scored = [];
  for (const [major, info] of Object.entries(window.TianShuData.MAJOR_LIBRARY)) {
    let score = 0;
    const matched = [];
    for (const tag of studentTags) {
      for (const kw of info.tags) {
        if (String(tag).includes(kw) || kw.includes(String(tag))) {
          score += 2;
          matched.push(kw);
        }
      }
    }
    if ((themeToMajors[primaryTheme] || []).includes(major)) score += 5;
    if (score > 0) {
      scored.push({ major, info, score, matched: [...new Set(matched)] });
    }
  }
  scored.sort((a, b) => b.score - a.score);

  const first = scored.slice(0, 2);
  const second = scored.slice(2, 4);
  const third = scored.slice(4, 6);

  // 风险规避
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
  if (bazi.jiZhong.includes("金")) {
    risks.push({
      major: "金融工程/硬核金融",
      reason: "金气过旺可能带来压力,需注意身心平衡",
      alt: "应用金融、保险精算"
    });
  }

  return {
    firstPriority: first.map(s => ({
      major: s.major,
      subs: s.info.subs,
      score: s.score,
      tags: s.info.tags,
      matched: s.matched,
      courses: s.info.courses,
      abilities: s.info.abilities,
      schools: s.info.schools,
      logic: `与学生「${primaryTheme}」主题高度契合 + 与${mbti.baseType}+${holland.top3}特征匹配`
    })),
    secondPriority: second.map(s => ({
      major: s.major,
      subs: s.info.subs,
      score: s.score,
      tags: s.info.tags,
      courses: s.info.courses,
      schools: s.info.schools,
      logic: `匹配学生${mbti.baseType}优势 + 可作为备选长期发展`
    })),
    thirdPriority: third.map(s => ({
      major: s.major,
      subs: s.info.subs,
      score: s.score,
      tags: s.info.tags,
      logic: "具备一定匹配度,可作为补充选择或交叉学科方向"
    })),
    risks: risks.length > 0 ? risks : [{
      major: "(无特别高风险专业)",
      reason: "当前测评结果未发现明显冲突专业",
      alt: "持续动态评估"
    }]
  };
}

// ===== 生涯路径 =====
function generateCareerPath(studentInfo, cross, majors) {
  const primaryMajor = majors.firstPriority[0] ? majors.firstPriority[0].major : "未确定";
  const primaryTheme = cross.positionLabel.theme;
  const mbtiShort = cross.advantages[1];

  const stage1 = {
    name: "学业深耕期(在校阶段)",
    goal: `夯实${primaryMajor}相关基础能力,完成学业目标,为升学/求职做好充分准备`,
    actions: [
      `课程学习:重点学习与${primaryMajor}相关的基础课程,成绩目标设定在年级前 20%`,
      `实践项目:参与至少 1 个与${primaryMajor}相关的科研项目/学科竞赛/开源贡献`,
      "阅读积累:每年精读 10-15 本专业相关书籍 + 行业研究报告",
      "升学/求职准备:提前 1-2 年了解目标院校/雇主的核心要求"
    ],
    abilities: [
      `强化 ${primaryTheme} 主题相关的基础能力`,
      `基于${mbtiShort.split("、")[0]}特质,刻意练习薄弱环节(如沟通、协作)`
    ],
    resources: [
      "寻找 1-2 位领域内的导师或前辈,定期请教",
      "建立专业知识库(笔记、代码、文档)"
    ]
  };

  const stage2 = {
    name: "职场起步期(毕业 0-5 年)",
    goal: `进入与${primaryMajor}相关的适配行业,完成学生到职场人转型`,
    jobs: [
      `在${primaryMajor}方向选择头部公司的初级岗位(校招为主)`,
      "关注岗位的成长性 > 短期薪资,优先选择核心业务部门"
    ],
    industries: [
      "结合 MBTI + 霍兰德,选择与核心特质匹配的行业赛道",
      "研究行业头部 10 家企业的招聘要求,锁定 3-5 家重点求职"
    ],
    growth: [
      "专业能力:成为岗位内的核心骨干,可独立负责中型项目",
      "职场能力:沟通、协作、项目管理等通用能力快速提升",
      "行业认知:对所处行业的趋势、玩法、关键资源建立系统认知"
    ],
    transitions: [
      "2-3 年:第一次岗位调整(纵向深耕或横向扩展)",
      "5 年:进入团队 leader 或专家序列的分水岭"
    ]
  };

  const stage3 = {
    name: "职场上升期(毕业 5-15 年)",
    goal: "实现职业角色升级,从执行者转型为决策者/领域专家",
    paths: [
      {name:"技术专家路径", desc:"从骨干工程师 → 高级工程师 → 领域专家 / 首席工程师 / 首席科学家", fit:"深度钻研型、追求技术壁垒"},
      {name:"管理路径", desc:"从团队负责人 → 部门管理者 → 公司高管", fit:"强组织能力、善于协调团队"},
      {name:"创业/自由职业路径", desc:"基于核心优势,开启创业、独立咨询、自媒体/内容创作", fit:"高自主性、有独特洞察、抗风险能力强"}
    ],
    competitive: [
      "建立不可替代的差异化优势(技术深度 / 行业资源 / 个人品牌)",
      "在所选方向上做出标志性成果(产品 / 论文 / 行业标准)"
    ],
    resources: [
      "建立行业人脉网络,定期参与行业会议",
      "通过写作、演讲、开源等方式建立个人品牌"
    ]
  };

  const stage4 = {
    name: "职业稳定/突破期(毕业 15 年以上)",
    goal: "实现职业价值的长期沉淀,完成终极目标 + 工作生活平衡",
    directions: [
      {name:"行业顶层角色", desc:"成为行业内头部专家、企业核心决策者、行业协会核心成员,参与行业标准制定"},
      {name:"价值沉淀方向", desc:"通过写作、教学、公益、导师角色沉淀个人专业价值"},
      {name:"转型与二次发展", desc:"基于核心优势开启二次创业、跨界发展"}
    ],
    balance: [
      "明确工作与生活的边界,避免长期过度消耗",
      "建立可持续的生活节奏与健康管理机制"
    ]
  };

  // 头部雇主
  const careerDetails = majors.firstPriority.map(m => ({
    major: m.major,
    path: "初级岗位 → 中级骨干 → 高级专家/管理者 → 行业领军",
    jobs: getJobExamples(m.major),
    employers: window.TianShuData.TOP_EMPLOYERS[m.major] || [`${m.major}相关头部企业`]
  }));

  const keyNodes = [
    {
      name: "高考志愿填报", time: "高三下学期(截止前 1-3 月)",
      actions: "1. 完成测评最终验证 2. 确定专业分级推荐 3. 完成院校梯队筛选 4. 制定志愿填报方案",
      note: "优先保障专业适配度,非盲目追求院校排名;预留保底选项"
    },
    {
      name: "考研/留学申请", time: "申请截止前 6-12 个月",
      actions: "1. 确定目标院校与项目 2. 备考/申请分阶段计划 3. 完成科研/实习背景提升 4. 文书与面试准备",
      note: "针对目标项目核心录取偏好,重点突出核心特质与适配度"
    },
    {
      name: "实习/科研项目", time: "开始前 3-6 个月",
      actions: "1. 确定匹配方向的实习/项目目标 2. 申请与参与的分阶段计划 3. 高质量完成并沉淀成果",
      note: "优先选择匹配核心发展方向的项目,非盲目追求大厂/title"
    },
    {
      name: "毕业/职业选择", time: "毕业前 6-12 个月",
      actions: "1. 确定职业目标赛道 2. 求职分阶段计划 3. 简历优化 + 面试准备 4. offer 筛选与谈判",
      note: "选择与核心特质匹配的岗位,非盲目追求高薪"
    }
  ];

  return {
    stages: [stage1, stage2, stage3, stage4],
    careerDetails,
    keyNodes,
    health: [
      "基于 MBTI 和五行特质,设计适配的运动、作息、情绪管理方案",
      "建立常态化的身心状态监测机制",
      "遇到高压场景时,启用预设的压力应对预案"
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

if (typeof window !== "undefined") {
  window.TianShuEngine = { crossValidate, recommendMajors, generateCareerPath };
}