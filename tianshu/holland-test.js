/**
 * 天枢 · 霍兰德职业兴趣测试(60 题,完整版)
 * 来源:基于 SDS(Self-Directed Search)简化改编
 * 6 维度各 10 题:R/I/A/S/E/C
 * 每题两选一(我喜欢 A 活动 / 我更喜欢 B 活动)
 *
 * 用法:window.TianShuHollandTest.start()
 */

const HOLLAND_QUESTIONS = [
  { dim: "R", text: "你更愿意花一个周末", A: { v: "R", desc: "自己动手修家具、做木工" }, B: { v: "A", desc: "去画展或看一场戏剧" }},
  { dim: "R", text: "看到一辆摩托车的机械构造,你", A: { v: "R", desc: "好奇它是怎么运转的" }, B: { v: "S", desc: "好奇骑它的人是什么感受" }},
  { dim: "R", text: "你更喜欢的工作环境是", A: { v: "R", desc: "车间、户外、操作设备" }, B: { v: "C", desc: "办公室、整理文件和数据" }},
  { dim: "R", text: "如果做一顿饭,你更享受", A: { v: "R", desc: "切菜、控火候的实操过程" }, B: { v: "A", desc: "尝试新菜式的创造性搭配" }},
  { dim: "R", text: "以下哪项更吸引你", A: { v: "R", desc: "组装一个复杂的电子设备" }, B: { v: "I", desc: "研究这个设备的工作原理" }},
  { dim: "R", text: "在户外活动时,你更喜欢", A: { v: "R", desc: "徒步、攀岩、骑行等实操" }, B: { v: "I", desc: "观察自然、记录生态" }},
  { dim: "R", text: "你对自己的动手能力", A: { v: "R", desc: "比较自信,喜欢动手" }, B: { v: "A", desc: "一般,更欣赏有创意的人" }},
  { dim: "R", text: "如果能选一辆车,你更在意", A: { v: "R", desc: "性能、马力、机械感" }, B: { v: "E", desc: "品牌、外观、商务属性" }},
  { dim: "R", text: "面对故障设备,你通常", A: { v: "R", desc: "动手拆开检查" }, B: { v: "I", desc: "查资料研究原因" }},
  { dim: "R", text: "你更愿意的工作是", A: { v: "R", desc: "电工、木匠、机械师" }, B: { v: "C", desc: "会计、档案员、统计员" }},
  { dim: "I", text: "你更愿意读", A: { v: "I", desc: "深度分析某个专题的研究报告" }, B: { v: "S", desc: "讲述真实人物故事的传记" }},
  { dim: "I", text: "看到为什么天是蓝的这种问题", A: { v: "I", desc: "很兴奋,想搞清楚原理" }, B: { v: "A", desc: "不太感兴趣,觉得没必要" }},
  { dim: "I", text: "在课堂上,你更喜欢", A: { v: "I", desc: "数学、物理、哲学这类抽象课" }, B: { v: "R", desc: "实验课、手工课、体育课" }},
  { dim: "I", text: "面对一个复杂问题,你更愿意", A: { v: "I", desc: "深入研究,找到根本原因" }, B: { v: "E", desc: "快速决策,边做边调整" }},
  { dim: "I", text: "以下哪个更让你满足", A: { v: "I", desc: "解开一个困扰很久的难题" }, B: { v: "S", desc: "帮朋友解决一个困难" }},
  { dim: "I", text: "你更喜欢的电视节目是", A: { v: "I", desc: "科学纪录片、宇宙探索" }, B: { v: "A", desc: "艺术创作、明星访谈" }},
  { dim: "I", text: "在团队中,你更擅长", A: { v: "I", desc: "研究问题、提供数据支持" }, B: { v: "E", desc: "组织协调、调动气氛" }},
  { dim: "I", text: "你更喜欢", A: { v: "I", desc: "有自己的方法和节奏" }, B: { v: "C", desc: "按流程和制度办事" }},
  { dim: "I", text: "对于理论和实践,你", A: { v: "I", desc: "觉得理论更重要" }, B: { v: "R", desc: "觉得实践出真知" }},
  { dim: "I", text: "如果做研究,你更愿意", A: { v: "I", desc: "在实验室独立做实验" }, B: { v: "S", desc: "在田野做社会调研" }},
  { dim: "A", text: "看到美丽的风景,你更想", A: { v: "A", desc: "拍照或画下来表达感受" }, B: { v: "I", desc: "思考它形成的地质原因" }},
  { dim: "A", text: "你更喜欢哪种表达方式", A: { v: "A", desc: "写诗、画画、唱歌" }, B: { v: "E", desc: "演讲、辩论、谈判" }},
  { dim: "A", text: "对于美的事物", A: { v: "A", desc: "特别敏感,会被触动" }, B: { v: "C", desc: "觉得功能更重要" }},
  { dim: "A", text: "你更愿意学", A: { v: "A", desc: "吉他、绘画、摄影" }, B: { v: "R", desc: "编程、烹饪、缝纫" }},
  { dim: "A", text: "你的房间更可能是", A: { v: "A", desc: "有艺术品、颜色丰富" }, B: { v: "C", desc: "整洁简约、黑白灰" }},
  { dim: "A", text: "你对哪种活动更有热情", A: { v: "A", desc: "创作、设计、即兴发挥" }, B: { v: "E", desc: "组织、销售、说服他人" }},
  { dim: "A", text: "如果你办聚会,你会", A: { v: "A", desc: "自己设计装饰和流程" }, B: { v: "E", desc: "邀请朋友、活跃气氛" }},
  { dim: "A", text: "你更讨厌", A: { v: "A", desc: "千篇一律、毫无创意" }, B: { v: "C", desc: "混乱无序、没有规则" }},
  { dim: "A", text: "工作时,你更喜欢", A: { v: "A", desc: "有自由发挥的空间" }, B: { v: "C", desc: "有明确的指标和标准" }},
  { dim: "A", text: "对于规则和流程", A: { v: "A", desc: "想打破,创造新的" }, B: { v: "C", desc: "遵守,稳定就好" }},
  { dim: "S", text: "看到有人难过,你", A: { v: "S", desc: "想立刻安慰和帮助" }, B: { v: "I", desc: "想了解他难过的原因" }},
  { dim: "S", text: "你更愿意做", A: { v: "S", desc: "志愿者、支教、辅导" }, B: { v: "R", desc: "维修、搬运、清洁" }},
  { dim: "S", text: "在朋友圈里,你是", A: { v: "S", desc: "倾听者,大家爱找你聊" }, B: { v: "E", desc: "活跃者,经常组织活动" }},
  { dim: "S", text: "你更擅长的领域是", A: { v: "S", desc: "理解他人、调解冲突" }, B: { v: "E", desc: "说服他人、达成交易" }},
  { dim: "S", text: "工作时,你更看重", A: { v: "S", desc: "能否帮助到他人" }, B: { v: "C", desc: "能否符合规范" }},
  { dim: "S", text: "你更容易被哪种内容打动", A: { v: "S", desc: "人与人之间的温情故事" }, B: { v: "A", desc: "美好的艺术作品" }},
  { dim: "S", text: "如果你做老师,你会", A: { v: "S", desc: "关心每个学生的成长" }, B: { v: "I", desc: "专注传授知识和方法" }},
  { dim: "S", text: "你更讨厌", A: { v: "S", desc: "人与人之间的冷漠" }, B: { v: "I", desc: "低效和无知的决策" }},
  { dim: "S", text: "你认为团队最重要的是", A: { v: "S", desc: "关系和谐、相互支持" }, B: { v: "C", desc: "目标清晰、分工明确" }},
  { dim: "S", text: "你更愿意从事", A: { v: "S", desc: "心理咨询、社会工作" }, B: { v: "E", desc: "销售、市场、管理" }},
  { dim: "E", text: "你更愿意担任", A: { v: "E", desc: "团队 leader,做决策" }, B: { v: "S", desc: "协调者,服务大家" }},
  { dim: "E", text: "你更喜欢的工作是", A: { v: "E", desc: "商务、销售、创业" }, B: { v: "C", desc: "行政、档案、数据" }},
  { dim: "E", text: "面对挑战,你", A: { v: "E", desc: "兴奋,把它当成机会" }, B: { v: "I", desc: "谨慎,先分析利弊" }},
  { dim: "E", text: "你更善于", A: { v: "E", desc: "说服他人、达成目标" }, B: { v: "S", desc: "倾听他人、安抚情绪" }},
  { dim: "E", text: "在团队里,你通常", A: { v: "E", desc: "推动事情往前走" }, B: { v: "A", desc: "想新的点子和创意" }},
  { dim: "E", text: "你更倾向于被评价为", A: { v: "E", desc: "有魄力、有影响力" }, B: { v: "R", desc: "踏实、可靠、技术过硬" }},
  { dim: "E", text: "如果你做一个项目,你会", A: { v: "E", desc: "主动找资源、谈合作" }, B: { v: "I", desc: "深入研究、做精做深" }},
  { dim: "E", text: "对于竞争,你认为", A: { v: "E", desc: "是好事,激发潜力" }, B: { v: "S", desc: "伤害感情,应该避免" }},
  { dim: "E", text: "你更喜欢", A: { v: "E", desc: "结果导向,讲效率" }, B: { v: "C", desc: "过程规范,讲合规" }},
  { dim: "E", text: "面对一个新机会,你会", A: { v: "E", desc: "果断出手,抢占先机" }, B: { v: "I", desc: "深入研究,再做决定" }},
  { dim: "C", text: "你更喜欢处理", A: { v: "C", desc: "结构化、有规则的事务" }, B: { v: "A", desc: "自由、灵活的工作" }},
  { dim: "C", text: "面对一堆文件,你更擅长", A: { v: "C", desc: "分类整理、建立索引" }, B: { v: "E", desc: "抽取要点、汇报给领导" }},
  { dim: "C", text: "你更看重工作", A: { v: "C", desc: "稳定、可预期、有保障" }, B: { v: "E", desc: "高收入、高挑战" }},
  { dim: "C", text: "面对细节,你的表现是", A: { v: "C", desc: "细致、不容易出错" }, B: { v: "A", desc: "粗放、但有大局观" }},
  { dim: "C", text: "你更喜欢", A: { v: "C", desc: "明确的指令和流程" }, B: { v: "A", desc: "自己探索和创造" }},
  { dim: "C", text: "面对截止日期,你", A: { v: "C", desc: "严格遵守,提前完成" }, B: { v: "P", desc: "灵活调整,差不多就行" }},
  { dim: "C", text: "你更讨厌", A: { v: "C", desc: "混乱的流程、不清晰的要求" }, B: { v: "E", desc: "按部就班、缺乏挑战" }},
  { dim: "C", text: "在团队里,你更可能是", A: { v: "C", desc: "把控进度、规范流程的人" }, B: { v: "S", desc: "关心同事、组织团建的人" }},
  { dim: "C", text: "你更喜欢的工作是", A: { v: "C", desc: "会计、审计、行政" }, B: { v: "I", desc: "研究、咨询、分析" }},
  { dim: "C", text: "对于循规蹈矩和打破常规,你", A: { v: "C", desc: "倾向循规蹈矩,稳妥" }, B: { v: "A", desc: "倾向打破常规,创新" }},
];

// ===== 霍兰德测试引擎 =====

const HollandTest = {
  questions: HOLLAND_QUESTIONS,
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

    document.getElementById("holland-test-app").innerHTML = `
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
          <button class="test-option" data-choice="A" onclick="window.TianShuHollandTest.choose('A')">
            <div class="opt-letter">A</div>
            <div class="opt-text">${q.A.desc}</div>
          </button>
          <button class="test-option" data-choice="B" onclick="window.TianShuHollandTest.choose('B')">
            <div class="opt-letter">B</div>
            <div class="opt-text">${q.B.desc}</div>
          </button>
        </div>

        <div class="test-nav">
          <button class="test-nav-btn" onclick="window.TianShuHollandTest.prev()" ${this.currentIdx === 0 ? "disabled" : ""}>
            ← 上一题
          </button>
          <button class="test-nav-btn secondary" onclick="window.TianShuHollandTest.skip()">
            跳过
          </button>
        </div>
      </div>
    `;
    window.scrollTo(0, 0);
  },

  getDimLabel(dim) {
    return {
      R: "R 现实型",
      I: "I 研究型",
      A: "A 艺术型",
      S: "S 社会型",
      E: "E 企业型",
      C: "C 常规型"
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
    const counts = { R: 0, I: 0, A: 0, S: 0, E: 0, C: 0 };
    this.answers.forEach(a => {
      if (a && a.value) counts[a.value]++;
    });

    const scores = {};
    ["R","I","A","S","E","C"].forEach(d => {
      scores[d] = Math.round(counts[d] / 10 * 100);
    });

    const sorted = Object.entries(scores).sort((a,b) => b[1] - a[1]);
    const top3 = sorted.slice(0, 3).map(([k]) => k).join("");
    const answered = this.answers.filter(a => a !== null).length;

    const dimInfo = {
      R: ["R 现实型", "#10b981"],
      I: ["I 研究型", "#4f7cff"],
      A: ["A 艺术型", "#c084fc"],
      S: ["S 社会型", "#f59e0b"],
      E: ["E 企业型", "#ef4444"],
      C: ["C 常规型", "#6b7280"]
    };

    let statsHtml = "";
    for (const [code, [label, color]] of Object.entries(dimInfo)) {
      statsHtml += `<div class="stat-row">
        <span class="stat-label">${label}</span>
        <span class="stat-bar"><span class="stat-fill" style="width:${scores[code]}%;background:${color}"></span></span>
        <span class="stat-val">${scores[code]}</span>
      </div>`;
    }

    document.getElementById("holland-test-app").innerHTML = `
      <div class="mbti-result-card">
        <div class="result-emoji">🎯</div>
        <h1 class="result-title">测试完成!</h1>
        <div class="result-type">${top3}</div>
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

    document.getElementById("btn-use-result").onclick = () => this.useResult(top3, scores);
    document.getElementById("btn-retake").onclick = () => this.start();
    document.getElementById("btn-back").onclick = () => window.location.href = "index.html";

    localStorage.setItem("tianshu_holland_result", JSON.stringify({ top3, scores, answered, time: Date.now() }));
  },

  useResult(top3, scores) {
    localStorage.setItem("tianshu_holland_result", JSON.stringify({ top3, scores, autoUse: true, time: Date.now() }));
    window.location.href = "index.html?from=holland-test";
  },

  consumeResult() {
    const raw = localStorage.getItem("tianshu_holland_result");
    if (!raw) return null;
    try {
      const data = JSON.parse(raw);
      if (Date.now() - data.time > 5 * 60 * 1000) {
        localStorage.removeItem("tianshu_holland_result");
        return null;
      }
      return data;
    } catch (e) {
      return null;
    }
  }
};

if (typeof window !== "undefined") {
  window.TianShuHollandTest = HollandTest;
}
