/**
 * 天枢 · MBTI 完整测试(60 题)
 * 来源:基于 MBTI Form M 量表改编,4 维度各 15 题
 * 4 维度:E/I(外向/内向)、S/N(实感/直觉)、T/F(思考/情感)、J/P(判断/知觉)
 * 每题两选一,得 1 分
 *
 * 用法:window.TianShuMbtiTest.start() 启动测试
 */

const MBTI_QUESTIONS = [
  { dim: "EI", text: "在聚会中,你更倾向于", A: { v: "E", desc: "主动与多人交谈,享受热闹氛围" }, B: { v: "I", desc: "与少数熟悉的人深入交流" }},
  { dim: "EI", text: "工作一天后,你的充电方式是", A: { v: "E", desc: "出门社交,和朋友吃饭聊天" }, B: { v: "I", desc: "回家独处,看书、看剧、发呆" }},
  { dim: "EI", text: "面对问题时,你更愿意", A: { v: "E", desc: "找人讨论,边说边想" }, B: { v: "I", desc: "独自思考,想清楚再开口" }},
  { dim: "EI", text: "在陌生场合,你会", A: { v: "E", desc: "主动介绍自己,认识新朋友" }, B: { v: "I", desc: "等别人来搭话,或先观察" }},
  { dim: "EI", text: "你说话时的风格更接近", A: { v: "E", desc: "边想边说,经常自我修正" }, B: { v: "I", desc: "想清楚再说,语言精炼" }},
  { dim: "EI", text: "朋友圈/社交媒体对你来说", A: { v: "E", desc: "是分享生活的必备工具" }, B: { v: "I", desc: "可有可无,不发也不会少什么" }},
  { dim: "EI", text: "当你需要做重大决定时", A: { v: "E", desc: "倾向找信任的人讨论" }, B: { v: "I", desc: "倾向自己反复权衡" }},
  { dim: "EI", text: "在团队讨论中,你是", A: { v: "E", desc: "发言较多的人" }, B: { v: "I", desc: "倾听较多的人" }},
  { dim: "EI", text: "周末你更喜欢的活动是", A: { v: "E", desc: "约朋友逛街、看展、运动" }, B: { v: "I", desc: "一个人宅家或去安静的地方" }},
  { dim: "EI", text: "你的注意力更多来自", A: { v: "E", desc: "外部的人和事" }, B: { v: "I", desc: "内部的想法和感受" }},
  { dim: "EI", text: "新认识一个朋友时", A: { v: "E", desc: "很快就能找到话题聊起来" }, B: { v: "I", desc: "需要一段时间才会熟悉" }},
  { dim: "EI", text: "被人误解时,你的第一反应是", A: { v: "E", desc: "立刻解释清楚" }, B: { v: "I", desc: "先消化,看情况再说" }},
  { dim: "EI", text: "工作时被打断,你的感受是", A: { v: "E", desc: "还好,可以再切回去" }, B: { v: "I", desc: "挺烦躁,要重新进入状态" }},
  { dim: "EI", text: "你觉得自己的能量来源主要是", A: { v: "E", desc: "与人互动产生的活力" }, B: { v: "I", desc: "独处时获得的充电" }},
  { dim: "EI", text: "如果必须长途独行 8 小时,你会", A: { v: "E", desc: "觉得有点无聊,想找人聊" }, B: { v: "I", desc: "很享受,可以自由发呆" }},
  { dim: "SN", text: "你更相信", A: { v: "S", desc: "看得见摸得着的具体经验" }, B: { v: "N", desc: "直觉和第六感" }},
  { dim: "SN", text: "描述事物时,你更习惯", A: { v: "S", desc: "用具体数字和细节" }, B: { v: "N", desc: "用比喻和意象" }},
  { dim: "SN", text: "你更感兴趣的话题是", A: { v: "S", desc: "当下正在发生的事" }, B: { v: "N", desc: "未来的可能性" }},
  { dim: "SN", text: "面对新项目,你更关注", A: { v: "S", desc: "具体怎么一步步做" }, B: { v: "N", desc: "整体愿景和大方向" }},
  { dim: "SN", text: "回忆往事时,你更容易想起", A: { v: "S", desc: "具体的场景和细节" }, B: { v: "N", desc: "当时的感受和领悟" }},
  { dim: "SN", text: "你更喜欢的书/电影类型是", A: { v: "S", desc: "写实、历史、传记" }, B: { v: "N", desc: "科幻、奇幻、象征主义" }},
  { dim: "SN", text: "学习新技能时,你更倾向", A: { v: "S", desc: "按部就班,一步步练习" }, B: { v: "N", desc: "先理解原理,再实践" }},
  { dim: "SN", text: "你更欣赏的人的特点是", A: { v: "S", desc: "脚踏实地、经验丰富" }, B: { v: "N", desc: "富有创意、见解独到" }},
  { dim: "SN", text: "遇到问题时,你更倾向", A: { v: "S", desc: "用过往类似经验解决" }, B: { v: "N", desc: "尝试全新的方法" }},
  { dim: "SN", text: "你更擅长", A: { v: "S", desc: "关注眼前的细节" }, B: { v: "N", desc: "把握整体的趋势" }},
  { dim: "SN", text: "对于理论性内容,你感觉", A: { v: "S", desc: "比较枯燥,不如案例" }, B: { v: "N", desc: "很兴奋,愿意深入" }},
  { dim: "SN", text: "描述未来时,你更常说", A: { v: "S", desc: "一步一步具体的计划" }, B: { v: "N", desc: "愿景式的蓝图和可能性" }},
  { dim: "SN", text: "你认为", A: { v: "S", desc: "经验是最重要的老师" }, B: { v: "N", desc: "想象力能创造新世界" }},
  { dim: "SN", text: "你更容易被吸引的内容是", A: { v: "S", desc: "具体可操作的方法论" }, B: { v: "N", desc: "启发心智的概念和隐喻" }},
  { dim: "SN", text: "你的思维更偏向", A: { v: "S", desc: "务实,关注现实" }, B: { v: "N", desc: "想象,关注可能" }},
  { dim: "TF", text: "做决定时,你更依赖", A: { v: "T", desc: "逻辑分析和客观事实" }, B: { v: "F", desc: "个人价值观和他人感受" }},
  { dim: "TF", text: "朋友向你倾诉烦恼时,你会", A: { v: "T", desc: "帮他分析问题、出主意" }, B: { v: "F", desc: "先共情,陪他消化情绪" }},
  { dim: "TF", text: "你更难接受的是", A: { v: "T", desc: "逻辑混乱、不讲道理" }, B: { v: "F", desc: "冷漠无情、不近人情" }},
  { dim: "TF", text: "评价一个人时,你更看重", A: { v: "T", desc: "能力和逻辑" }, B: { v: "F", desc: "善良和真诚" }},
  { dim: "TF", text: "与朋友发生分歧时,你会", A: { v: "T", desc: "坚持自己的观点,讲道理" }, B: { v: "F", desc: "考虑对方感受,缓和气氛" }},
  { dim: "TF", text: "你更容易被哪种说法说服", A: { v: "T", desc: "数据充分、逻辑严密" }, B: { v: "F", desc: "触动人心、引发共鸣" }},
  { dim: "TF", text: "面对批评,你的第一反应是", A: { v: "T", desc: "分析批评是否合理" }, B: { v: "F", desc: "感到受伤或不舒服" }},
  { dim: "TF", text: "你认为自己更接近", A: { v: "T", desc: "理性冷静的人" }, B: { v: "F", desc: "温暖体贴的人" }},
  { dim: "TF", text: "如果有人做事方式不对,你会", A: { v: "T", desc: "直接指出问题所在" }, B: { v: "F", desc: "看情况,委婉提醒或不管" }},
  { dim: "TF", text: "团队里有矛盾时,你更倾向", A: { v: "T", desc: "用规则和流程解决" }, B: { v: "F", desc: "私下沟通、协调关系" }},
  { dim: "TF", text: "别人对你的评价更可能是", A: { v: "T", desc: "公正、客观" }, B: { v: "F", desc: "善良、有同理心" }},
  { dim: "TF", text: "做艰难决定时,你更看重", A: { v: "T", desc: "利弊分析、最优解" }, B: { v: "F", desc: "对所有人的影响、价值观" }},
  { dim: "TF", text: "你看电影/小说时,更关注", A: { v: "T", desc: "情节是否合理、逻辑通顺" }, B: { v: "F", desc: "人物情感是否打动你" }},
  { dim: "TF", text: "工作中,你更讨厌", A: { v: "T", desc: "无效的争论、不讲逻辑" }, B: { v: "F", desc: "冲突、人与人之间的冷漠" }},
  { dim: "TF", text: "对于对错和好坏,你认为", A: { v: "T", desc: "对错比好坏更重要" }, B: { v: "F", desc: "好坏比对错更重要" }},
  { dim: "JP", text: "出门旅行时,你更倾向", A: { v: "J", desc: "提前做详细攻略和计划" }, B: { v: "P", desc: "到了再说,随性探索" }},
  { dim: "JP", text: "你的桌面/房间通常", A: { v: "J", desc: "整洁有序,东西有固定位置" }, B: { v: "P", desc: "有点乱,但你知道东西在哪" }},
  { dim: "JP", text: "面对截止日期,你", A: { v: "J", desc: "会提前完成,不喜欢最后赶" }, B: { v: "P", desc: "在压力下效率最高,常常赶工" }},
  { dim: "JP", text: "对于计划被打乱,你的反应是", A: { v: "J", desc: "不舒服,想尽快恢复计划" }, B: { v: "P", desc: "还好,顺其自然" }},
  { dim: "JP", text: "你更喜欢的工作方式是", A: { v: "J", desc: "目标明确,有清晰的路线" }, B: { v: "P", desc: "灵活自由,保留可能性" }},
  { dim: "JP", text: "做项目时,你更倾向", A: { v: "J", desc: "先定计划,再分步执行" }, B: { v: "P", desc: "边做边调整,灵活应变" }},
  { dim: "JP", text: "对于待办清单,你", A: { v: "J", desc: "每天都会更新并勾选" }, B: { v: "P", desc: "做了就忘,想起来才看" }},
  { dim: "JP", text: "你更喜欢的生活节奏是", A: { v: "J", desc: "规律、稳定、可预期" }, B: { v: "P", desc: "随性、有变化、有惊喜" }},
  { dim: "JP", text: "面对选择时,你会", A: { v: "J", desc: "尽快决定,不喜欢纠结" }, B: { v: "P", desc: "保留选项,等到不得不选" }},
  { dim: "JP", text: "对准时的态度", A: { v: "J", desc: "非常重要,守时是基本" }, B: { v: "P", desc: "差不多就行,弹性一点" }},
  { dim: "JP", text: "你认为完成比完美", A: { v: "J", desc: "不完全同意,要做就做好" }, B: { v: "P", desc: "挺对的,先完成再迭代" }},
  { dim: "JP", text: "你更讨厌", A: { v: "J", desc: "事情没结论、悬而未决" }, B: { v: "P", desc: "被规则束缚、失去自由" }},
  { dim: "JP", text: "买大件物品时,你会", A: { v: "J", desc: "研究很久,做对比表格" }, B: { v: "P", desc: "看眼缘,看中了就买" }},
  { dim: "JP", text: "对于规则和流程,你", A: { v: "J", desc: "尊重,按规则做事效率高" }, B: { v: "P", desc: "觉得是参考,具体情况具体看" }},
  { dim: "JP", text: "你更欣赏的生活方式是", A: { v: "J", desc: "有序、有目标、有积累" }, B: { v: "P", desc: "自由、随性、体验丰富" }},
];

// ===== MBTI 测试引擎 =====

const MbtiTest = {
  questions: MBTI_QUESTIONS,
  currentIdx: 0,
  answers: [],

  start() {
    this.currentIdx = 0;
    this.answers = new Array(this.questions.length).fill(null);
    this.renderQuestion();
  },

  renderQuestion() {
    const q = this.questions[this.currentIdx];
    const progress = ((this.currentIdx + 1) / this.questions.length * 100).toFixed(0);

    document.getElementById("mbti-test-app").innerHTML = `
      <div class="mbti-test-card">
        <div class="test-progress">
          <div class="test-progress-fill" style="width:${progress}%"></div>
        </div>
        <div class="test-progress-text">
          第 ${this.currentIdx + 1} / ${this.questions.length} 题
          <span class="dim-tag">${this.getDimLabel(q.dim)}</span>
        </div>

        <h2 class="test-question">${q.text}</h2>

        <div class="test-options">
          <button class="test-option" data-choice="A" onclick="window.TianShuMbtiTest.choose('A')">
            <div class="opt-letter">A</div>
            <div class="opt-text">${q.A.desc}</div>
          </button>
          <button class="test-option" data-choice="B" onclick="window.TianShuMbtiTest.choose('B')">
            <div class="opt-letter">B</div>
            <div class="opt-text">${q.B.desc}</div>
          </button>
        </div>

        <div class="test-nav">
          <button class="test-nav-btn" onclick="window.TianShuMbtiTest.prev()" ${this.currentIdx === 0 ? "disabled" : ""}>
            ← 上一题
          </button>
          <button class="test-nav-btn secondary" onclick="window.TianShuMbtiTest.skip()">
            跳过
          </button>
        </div>
      </div>
    `;
    window.scrollTo(0, 0);
  },

  getDimLabel(dim) {
    return {
      EI: "E 外向 ↔ I 内向",
      SN: "S 实感 ↔ N 直觉",
      TF: "T 思考 ↔ F 情感",
      JP: "J 判断 ↔ P 知觉"
    }[dim];
  },

  choose(choice) {
    const q = this.questions[this.currentIdx];
    const value = choice === "A" ? q.A.v : q.B.v;
    this.answers[this.currentIdx] = { idx: this.currentIdx, dim: q.dim, choice, value };

    document.querySelectorAll(".test-option").forEach(btn => {
      btn.classList.remove("selected");
      if (btn.dataset.choice === choice) btn.classList.add("selected");
    });

    setTimeout(() => this.next(), 280);
  },

  next() {
    if (this.currentIdx < this.questions.length - 1) {
      this.currentIdx++;
      this.renderQuestion();
    } else {
      this.finish();
    }
  },

  prev() {
    if (this.currentIdx > 0) {
      this.currentIdx--;
      this.renderQuestion();
    }
  },

  skip() {
    this.next();
  },

  finish() {
    const counts = { E: 0, I: 0, S: 0, N: 0, T: 0, F: 0, J: 0, P: 0 };
    this.answers.forEach(a => {
      if (a && a.value) counts[a.value]++;
    });

    const ePct = (counts.E / 15 * 100).toFixed(0);
    const iPct = (counts.I / 15 * 100).toFixed(0);
    const sPct = (counts.S / 15 * 100).toFixed(0);
    const nPct = (counts.N / 15 * 100).toFixed(0);
    const tPct = (counts.T / 15 * 100).toFixed(0);
    const fPct = (counts.F / 15 * 100).toFixed(0);
    const jPct = (counts.J / 15 * 100).toFixed(0);
    const pPct = (counts.P / 15 * 100).toFixed(0);

    const type =
      (counts.E > counts.I ? "E" : "I") +
      (counts.S > counts.N ? "S" : "N") +
      (counts.T > counts.F ? "T" : "F") +
      (counts.J > counts.P ? "J" : "P");

    const answered = this.answers.filter(a => a !== null).length;
    const aVsT = counts.J > counts.P ? "A" : "T";

    const bars = [
      ["E 外向", ePct, "#fbbf24"], ["I 内向", iPct, "#c084fc"],
      ["S 实感", sPct, "#fbbf24"], ["N 直觉", nPct, "#c084fc"],
      ["T 思考", tPct, "#fbbf24"], ["F 情感", fPct, "#c084fc"],
      ["J 判断", jPct, "#fbbf24"], ["P 知觉", pPct, "#c084fc"]
    ];

    let statsHtml = "";
    for (const [label, pct, color] of bars) {
      statsHtml += `<div class="stat-row">
        <span class="stat-label">${label}</span>
        <span class="stat-bar"><span class="stat-fill" style="width:${pct}%;background:${color}"></span></span>
        <span class="stat-val">${pct}%</span>
      </div>`;
    }

    const fullType = type + aVsT;
    document.getElementById("mbti-test-app").innerHTML = `
      <div class="mbti-result-card">
        <div class="result-emoji">🎉</div>
        <h1 class="result-title">测试完成!</h1>
        <div class="result-type">${fullType}</div>
        <div class="result-stats">${statsHtml}</div>
        <div class="result-tip">完成 ${answered} / ${this.questions.length} 题</div>
        <div class="result-actions">
          <button class="result-btn primary" id="btn-use-result">✅ 用这个结果继续测评</button>
          <button class="result-btn secondary" id="btn-retake">🔄 重新测试</button>
          <button class="result-btn secondary" id="btn-back">↩ 返回主页</button>
        </div>
      </div>
    `;
    window.scrollTo(0, 0);

    document.getElementById("btn-use-result").onclick = () => this.useResult(fullType);
    document.getElementById("btn-retake").onclick = () => this.start();
    document.getElementById("btn-back").onclick = () => window.location.href = "index.html";

    localStorage.setItem("tianshu_mbti_result", JSON.stringify({ type: fullType, counts, answered, time: Date.now() }));
  },

  useResult(type) {
    localStorage.setItem("tianshu_mbti_result", JSON.stringify({ type, autoUse: true, time: Date.now() }));
    window.location.href = "index.html?from=mbti-test";
  },

  consumeResult() {
    const raw = localStorage.getItem("tianshu_mbti_result");
    if (!raw) return null;
    try {
      const data = JSON.parse(raw);
      if (Date.now() - data.time > 5 * 60 * 1000) {
        localStorage.removeItem("tianshu_mbti_result");
        return null;
      }
      return data;
    } catch (e) {
      return null;
    }
  }
};

if (typeof window !== "undefined") {
  window.TianShuMbtiTest = MbtiTest;
}
