/**
 * 天枢 · 主交互逻辑(多步表单 + 报告生成)
 */

// ===== 状态 =====
const state = {
  step: 1,
  student: {
    name: "",
    gender: "男",
    birthYear: 2010,
    birthMonth: 5,
    birthDay: 15,
    birthHour: 14,
    grade: "高一"
  },
  mbtiType: "INTJ-A",
  hollandScores: {R: 30, I: 85, A: 70, S: 65, E: 40, C: 35},
  results: null
};

// ===== 初始化 =====
function init() {
  // 渲染北斗七星星座 logo
  const beidouEl = document.getElementById("beidou-container");
  if (beidouEl && window.TianShuBeidou) {
    beidouEl.innerHTML = window.TianShuBeidou.renderBeidouSvg({ size: 150, theme: "purple" });
  }
  // 设置版本号
  const vEl = document.getElementById("version-display");
  if (vEl) vEl.textContent = (window.TIANSHU_VERSION || "v0.2") + " (Web 版)";
  updateProgress(1);
  renderStep1();
}

// ===== 进度条更新 =====
function updateProgress(currentStep) {
  const steps = document.querySelectorAll(".progress-step");
  const fill = document.getElementById("progress-fill");
  if (!steps.length || !fill) return;

  steps.forEach((s) => {
    const sn = parseInt(s.getAttribute("data-step"));
    s.classList.remove("active", "completed");
    if (sn < currentStep) s.classList.add("completed");
    else if (sn === currentStep) s.classList.add("active");
  });

  // 填充比例:5 步 → 0% / 25% / 50% / 75% / 100%
  const pct = ((currentStep - 1) / (steps.length - 1)) * 100;
  fill.style.width = pct + "%";
}

// ===== Step 1: 基础信息 =====
function renderStep1() {
  const app = document.getElementById("app");
  app.innerHTML = `
    <div class="step-card">
      <div class="step-header">
        <span class="step-num">1/5</span>
        <h2>📝 学生基础信息</h2>
      </div>
      <div class="form-grid">
        <label>姓名 <input type="text" id="f-name" value="${state.student.name}" placeholder="例如:林小满"></label>
        <label>性别
          <select id="f-gender">
            <option value="男" ${state.student.gender === "男" ? "selected" : ""}>男</option>
            <option value="女" ${state.student.gender === "女" ? "selected" : ""}>女</option>
          </select>
        </label>
        <label>出生年 <input type="number" id="f-year" value="${state.student.birthYear}" min="1990" max="2025"></label>
        <label>出生月 <input type="number" id="f-month" value="${state.student.birthMonth}" min="1" max="12"></label>
        <label>出生日 <input type="number" id="f-day" value="${state.student.birthDay}" min="1" max="31"></label>
        <label>出生时辰(0-23) <input type="number" id="f-hour" value="${state.student.birthHour}" min="0" max="23"></label>
        <label>当前学段
          <select id="f-grade">
            <option ${state.student.grade === "初中" ? "selected" : ""}>初中</option>
            <option ${state.student.grade === "高一" ? "selected" : ""}>高一</option>
            <option ${state.student.grade === "高二" ? "selected" : ""}>高二</option>
            <option ${state.student.grade === "高三" ? "selected" : ""}>高三</option>
            <option ${state.student.grade === "本科" ? "selected" : ""}>本科</option>
            <option ${state.student.grade === "研究生" ? "selected" : ""}>研究生</option>
          </select>
        </label>
      </div>
      <div class="step-actions">
        <button class="btn-primary" onclick="nextStep1()">下一步 →</button>
      </div>
    </div>
  `;
}

function nextStep1() {
  state.student.name = document.getElementById("f-name").value.trim() || "匿名学生";
  state.student.gender = document.getElementById("f-gender").value;
  state.student.birthYear = parseInt(document.getElementById("f-year").value);
  state.student.birthMonth = parseInt(document.getElementById("f-month").value);
  state.student.birthDay = parseInt(document.getElementById("f-day").value);
  state.student.birthHour = parseInt(document.getElementById("f-hour").value);
  state.student.grade = document.getElementById("f-grade").value;
  state.step = 2;
  updateProgress(2);
  renderStep2();
}

// ===== Step 2: 八字 + 紫微展示 =====
function renderStep2() {
  const app = document.getElementById("app");
  app.innerHTML = `<div class="step-card"><div class="loading">🔮 排盘计算中...</div></div>`;

  setTimeout(() => {
    const bazi = window.TianShuBazi.getFourPillars(
      state.student.birthYear,
      state.student.birthMonth,
      state.student.birthDay,
      state.student.birthHour
    );
    if (bazi.error) {
      app.innerHTML = `<div class="step-card"><div class="error">❌ ${bazi.error}</div></div>`;
      return;
    }
    const ziwei = window.TianShuData.getZiweiSummary(
      state.student.birthYear,
      state.student.birthMonth,
      state.student.birthHour
    );

    state._bazi = bazi;
    state._ziwei = ziwei;

    app.innerHTML = `
      <div class="step-card">
        <div class="step-header">
          <span class="step-num">2/5</span>
          <h2>🔮 八字 + ⭐ 紫微排盘</h2>
        </div>

        <h3>📋 八字四柱</h3>
        <table class="data-table">
          <tr><th>项目</th><th>结果</th></tr>
          <tr><td>公历</td><td>${bazi.solar}</td></tr>
          <tr><td>农历</td><td>${bazi.lunar}</td></tr>
          <tr><td>年柱</td><td><strong>${bazi.yearZhu}</strong></td></tr>
          <tr><td>月柱</td><td><strong>${bazi.monthZhu}</strong></td></tr>
          <tr><td>日柱</td><td><strong>${bazi.dayZhu}</strong></td></tr>
          <tr><td>时柱</td><td><strong>${bazi.hourZhu}</strong></td></tr>
          <tr><td>日主</td><td>${bazi.dayMaster}(${bazi.dayMasterWx})</td></tr>
          <tr><td>五行统计</td><td>${Object.entries(bazi.wuxingCount).map(([k,v]) => `${k}:${v}`).join(" · ")}</td></tr>
          <tr><td>喜用神</td><td><span class="tag tag-primary">${bazi.xiZhong.join(" + ")}</span></td></tr>
          <tr><td>忌神</td><td><span class="tag tag-warning">${bazi.jiZhong.join(" + ")}</span></td></tr>
        </table>

        <div class="info-block">
          <strong>核心性格:</strong>${bazi.personality}<br>
          <strong>学业事业适配:</strong>${bazi.careerFit}
        </div>

        <h3>⭐ 紫微简版</h3>
        ${renderZiwei(ziwei)}

        <div class="step-actions">
          <button class="btn-secondary" onclick="goBack()">← 上一步</button>
          <button class="btn-primary" onclick="nextStep2()">下一步 →</button>
        </div>
      </div>
    `;
  }, 200);
}

function renderZiwei(z) {
  const gong = (g) => `
    <div class="gong-card">
      <div class="gong-title">${g.name}:<span class="tag tag-primary">${g.star}</span></div>
      <div><strong>特质:</strong>${g.trait}</div>
      <div><strong>适配:</strong>${g.fit}</div>
      ${g.hourEffect ? `<div class="hour-effect">⏰ ${g.hourEffect}</div>` : ""}
    </div>
  `;
  return `
    <div class="gong-grid">
      ${gong(z.mingGong)}${gong(z.shiyeGong)}${gong(z.caiboGong)}
    </div>
    <p class="note">⚠️ ${z.note}</p>
  `;
}

function nextStep2() {
  state.step = 3;
  updateProgress(3);
  renderStep3();
}

// ===== Step 3: MBTI =====
function renderStep3() {
  const mode = state._mbtiMode || "known";
  const app = document.getElementById("app");

  app.innerHTML = `
    <div class="step-card">
      <div class="step-header">
        <span class="step-num">3/5</span>
        <h2>🧠 MBTI 人格类型</h2>
      </div>

      <div class="mode-tabs">
        <button class="mode-tab ${mode === "known" ? "active" : ""}" onclick="switchMbtiMode('known')">✅ 我知道我的类型</button>
        <button class="mode-tab ${mode === "test" ? "active" : ""}" onclick="switchMbtiMode('test')">📝 做 MBTI 测试</button>
      </div>

      <div id="mbti-body">
        ${mode === "known" ? renderMbtiKnown() : renderMbtiTest()}
      </div>

      <div class="step-actions">
        <button class="btn-secondary" onclick="goBack()">← 上一步</button>
        <button class="btn-primary" onclick="nextStep3()">下一步 →</button>
      </div>
    </div>
  `;

  if (mode === "known") {
    document.getElementById("f-mbti-base").addEventListener("change", updateMbtiPreview);
    document.getElementById("f-mbti-at").addEventListener("change", updateMbtiPreview);
    updateMbtiPreview();
  }
}

function switchMbtiMode(mode) {
  state._mbtiMode = mode;
  renderStep3();
}

function renderMbtiKnown() {
  const types = Object.keys(window.TianShuData.MBTI_DATA);
  const options = types.map(t => `<option value="${t}" ${t === state.mbtiType.split("-")[0] ? "selected" : ""}>${t}</option>`).join("");
  return `
    <p class="hint">如果你测过 MBTI,选择对应类型并指定 A/T 倾向。如果没有,可以选一个大致接近的:</p>
    <div class="form-grid">
      <label>MBTI 类型
        <select id="f-mbti-base">${options}</select>
      </label>
      <label>A / T 倾向
        <select id="f-mbti-at">
          <option value="">不指定</option>
          <option value="A">A(Assertive 自信型)</option>
          <option value="T">T(Turbulent 动荡型)</option>
        </select>
      </label>
    </div>
    <div id="mbti-preview"></div>
  `;
}

function renderMbtiTest() {
  const qs = window.TianShuData.MBTI_QUESTIONS;
  return `
    <p class="hint">每题选择更接近你的选项,完成后点击下方按钮计算类型:</p>
    <div class="test-questions">
      ${qs.map((q, i) => `
        <div class="test-q" data-q="${i}">
          <div class="test-q-num">第 ${i+1} 题</div>
          <div class="test-q-stem">${q.stem}</div>
          <label class="test-q-opt ${state._mbtiAnswers?.[i] === 1 ? "selected" : ""}">
            <input type="radio" name="mbti-q${i}" value="1" ${state._mbtiAnswers?.[i] === 1 ? "checked" : ""} onchange="setMbtiAnswer(${i}, 1)">
            ${q.optionA}
          </label>
          <label class="test-q-opt ${state._mbtiAnswers?.[i] === 2 ? "selected" : ""}">
            <input type="radio" name="mbti-q${i}" value="2" ${state._mbtiAnswers?.[i] === 2 ? "checked" : ""} onchange="setMbtiAnswer(${i}, 2)">
            ${q.optionB}
          </label>
        </div>
      `).join("")}
    </div>
    <button class="btn-primary" onclick="calcMbtiResult()" style="margin-top:16px;width:100%">🧮 计算我的 MBTI 类型</button>
    <div id="mbti-test-result" style="margin-top:16px;"></div>
  `;
}

function setMbtiAnswer(idx, score) {
  if (!state._mbtiAnswers) state._mbtiAnswers = [];
  state._mbtiAnswers[idx] = score;
  // 更新选中样式
  const parent = document.querySelector(`.test-q[data-q="${idx}"]`);
  if (parent) {
    parent.querySelectorAll(".test-q-opt").forEach(el => el.classList.remove("selected"));
    parent.querySelector(`input[value="${score}"]`).closest(".test-q-opt").classList.add("selected");
  }
}

function calcMbtiResult() {
  const answers = state._mbtiAnswers || [];
  const unanswered = [];
  for (let i = 0; i < window.TianShuData.MBTI_QUESTIONS.length; i++) {
    if (!answers[i]) unanswered.push(i + 1);
  }
  if (unanswered.length > 0) {
    document.getElementById("mbti-test-result").innerHTML = `<div class="error">❌ 还有 ${unanswered.length} 题未作答(第 ${unanswered.join(", ")} 题),请完成所有题目</div>`;
    return;
  }

  const full = answers.map((s, i) => ({ qIdx: i, score: s }));
  const result = window.TianShuData.calcMbtiFromTest(full);
  state.mbtiType = result.type;
  state._mbtiAnswers = answers;

  const info = window.TianShuData.getMbtiInfo(result.type);
  const pct = (dim) => {
    const total = result.scores[dim] + result.scores[dim === "E" ? "I" : dim === "I" ? "E" : dim === "S" ? "N" : dim === "N" ? "S" : dim === "T" ? "F" : dim === "F" ? "T" : dim === "J" ? "P" : "J"];
    return total > 0 ? Math.round(result.scores[dim] / total * 100) : 50;
  };

  document.getElementById("mbti-test-result").innerHTML = `
    <div class="mbti-card" style="border:2px solid #4f7cff;">
      <div class="mbti-title">🎉 你的 MBTI 类型: ${info.fullType} · ${info.nick}</div>
      <div class="test-dim-bars">
        <div class="dim-bar"><span>E ${result.scores.E}</span><div class="bar-track"><div class="bar-fill" style="width:${pct("E")}%"></div></div><span>${result.scores.I} I</span></div>
        <div class="dim-bar"><span>S ${result.scores.S}</span><div class="bar-track"><div class="bar-fill" style="width:${pct("S")}%"></div></div><span>${result.scores.N} N</span></div>
        <div class="dim-bar"><span>T ${result.scores.T}</span><div class="bar-track"><div class="bar-fill" style="width:${pct("T")}%"></div></div><span>${result.scores.F} F</span></div>
        <div class="dim-bar"><span>J ${result.scores.J}</span><div class="bar-track"><div class="bar-fill" style="width:${pct("J")}%"></div></div><span>${result.scores.P} P</span></div>
      </div>
      <div style="margin-top:12px"><strong>核心:</strong>${info.core}</div>
      <div><strong>优势:</strong>${info.strength}</div>
      <div><strong>短板:</strong><span style="color:#c53030;">${info.weakness}</span></div>
    </div>
  `;
}

function updateMbtiPreview() {
  const base = document.getElementById("f-mbti-base").value;
  const at = document.getElementById("f-mbti-at").value;
  const type = at ? `${base}-${at}` : base;
  const info = window.TianShuData.getMbtiInfo(type);
  document.getElementById("mbti-preview").innerHTML = `
    <div class="mbti-card">
      <div class="mbti-title">${info.fullType} · ${info.nick}</div>
      <div><strong>核心:</strong>${info.core}</div>
      <div><strong>认知:</strong>${info.cog}</div>
      <div><strong>行为:</strong>${info.beh}</div>
      <div><strong>优势:</strong>${info.strength}</div>
      <div><strong>短板:</strong><span style="color:#c53030;">${info.weakness}</span></div>
      <div><strong>适配专业:</strong>${info.fitMajors}</div>
    </div>
  `;
  state.mbtiType = type;
}

function nextStep3() {
  state.step = 4;
  updateProgress(4);
  renderStep4();
}

// ===== Step 4: 霍兰德 =====
function renderStep4() {
  const mode = state._hollandMode || "known";
  const app = document.getElementById("app");

  app.innerHTML = `
    <div class="step-card">
      <div class="step-header">
        <span class="step-num">4/5</span>
        <h2>🎯 霍兰德职业兴趣</h2>
      </div>

      <div class="mode-tabs">
        <button class="mode-tab ${mode === "known" ? "active" : ""}" onclick="switchHollandMode('known')">✅ 我知道我的分数</button>
        <button class="mode-tab ${mode === "test" ? "active" : ""}" onclick="switchHollandMode('test')">📝 做霍兰德测试</button>
      </div>

      <div id="holland-body">
        ${mode === "known" ? renderHollandKnown() : renderHollandTest()}
      </div>

      <div id="holland-preview-outer" style="margin-top:16px;"></div>

      <div class="step-actions">
        <button class="btn-secondary" onclick="goBack()">← 上一步</button>
        <button class="btn-primary" onclick="nextStep4()">下一步 →</button>
      </div>
    </div>
  `;

  if (mode === "known") {
    updateHollandPreview();
  }
}

function switchHollandMode(mode) {
  state._hollandMode = mode;
  renderStep4();
}

function renderHollandKnown() {
  const sliders = ["R","I","A","S","E","C"].map(code => `
    <div class="slider-row">
      <label class="slider-label">
        <strong>${code}</strong> · ${window.TianShuData.HOLLAND_DIMS[code].name}
        <span class="slider-value" id="v-${code}">${state.hollandScores[code]}</span>
      </label>
      <input type="range" min="0" max="100" value="${state.hollandScores[code]}"
             id="s-${code}" oninput="updateHollandScore('${code}', this.value)">
    </div>
  `).join("");

  return `
    <p class="hint">调整每个维度的得分(0-100),不知道就保留默认。</p>
    <div class="sliders">${sliders}</div>
    <button class="btn-text" onclick="resetHolland()">↺ 重置为示例默认值</button>
    <div id="holland-preview"></div>
  `;
}

function renderHollandTest() {
  const qs = window.TianShuData.HOLLAND_QUESTIONS;
  const ratingLabels = ["非常不喜欢", "不喜欢", "一般", "喜欢", "非常喜欢"];

  return `
    <p class="hint">评价每个活动的喜欢程度(1-5分),完成后计算你的霍兰德分数:</p>
    <div class="test-questions holland-test">
      ${qs.map((q, i) => `
        <div class="test-q test-q-holland" data-q="${i}">
          <div class="test-q-num">${i+1}</div>
          <div class="test-q-text">${q.text}</div>
          <div class="test-q-rating">
            ${ratingLabels.map((label, ri) => `
              <label class="rating-opt ${state._hollandAnswers?.[i] === ri + 1 ? "selected" : ""}">
                <input type="radio" name="holland-q${i}" value="${ri + 1}"
                  ${state._hollandAnswers?.[i] === ri + 1 ? "checked" : ""}
                  onchange="setHollandAnswer(${i}, ${ri + 1}, '${q.dim}')">
                <span class="rating-num">${ri + 1}</span>
                <span class="rating-label">${label}</span>
              </label>
            `).join("")}
          </div>
        </div>
      `).join("")}
    </div>
    <button class="btn-primary" onclick="calcHollandResult()" style="margin-top:16px;width:100%">🧮 计算我的霍兰德分数</button>
    <div id="holland-test-result" style="margin-top:16px;"></div>
  `;
}

function setHollandAnswer(idx, score, dim) {
  if (!state._hollandAnswers) state._hollandAnswers = [];
  if (!state._hollandAnswerDims) state._hollandAnswerDims = [];
  state._hollandAnswers[idx] = score;
  state._hollandAnswerDims[idx] = dim;
  const parent = document.querySelector(`.test-q-holland[data-q="${idx}"]`);
  if (parent) {
    parent.querySelectorAll(".rating-opt").forEach(el => el.classList.remove("selected"));
    parent.querySelector(`input[value="${score}"]`).closest(".rating-opt").classList.add("selected");
  }
}

function calcHollandResult() {
  const answers = state._hollandAnswers || [];
  const unanswered = [];
  for (let i = 0; i < window.TianShuData.HOLLAND_QUESTIONS.length; i++) {
    if (!answers[i]) unanswered.push(i + 1);
  }
  if (unanswered.length > 0) {
    document.getElementById("holland-test-result").innerHTML = `<div class="error">❌ 还有 ${unanswered.length} 题未作答(第 ${unanswered.join(", ")} 题),请完成所有题目</div>`;
    return;
  }

  const full = window.TianShuData.HOLLAND_QUESTIONS.map((q, i) => ({
    dim: q.dim,
    score: answers[i]
  }));
  const scores = window.TianShuData.calcHollandFromTest(full);
  state.hollandScores = scores;

  const info = window.TianShuData.getHollandInfo(scores);
  document.getElementById("holland-test-result").innerHTML = `
    <div class="holland-card" style="border:2px solid #4f7cff;">
      <div class="holland-title">🎉 你的霍兰德代码: <span class="tag tag-primary">${info.top3}</span></div>
      <div>${info.codeExplain}</div>
      <div class="holland-fits">
        <strong>主适配方向:</strong>
        <ul>${info.mainFit.map(f => `<li>${f}</li>`).join("")}</ul>
      </div>
      ${info.riskWarning !== "无明显短板维度" ? `<div class="risk-warning">⚠️ ${info.riskWarning}</div>` : ""}
      <div style="margin-top:12px">
        <strong>各维度得分:</strong>
        <div class="test-dim-bars">
          ${["R","I","A","S","E","C"].map(code => `
            <div class="dim-bar">
              <span>${code}</span>
              <div class="bar-track"><div class="bar-fill" style="width:${scores[code]}%"></div></div>
              <span>${scores[code]}</span>
            </div>
          `).join("")}
        </div>
      </div>
    </div>
  `;
}

function updateHollandScore(code, val) {
  state.hollandScores[code] = parseInt(val);
  document.getElementById("v-" + code).textContent = val;
  updateHollandPreview();
}

function resetHolland() {
  state.hollandScores = {R: 30, I: 85, A: 70, S: 65, E: 40, C: 35};
  ["R","I","A","S","E","C"].forEach(c => {
    document.getElementById("s-" + c).value = state.hollandScores[c];
    document.getElementById("v-" + c).textContent = state.hollandScores[c];
  });
  updateHollandPreview();
}

function updateHollandPreview() {
  const info = window.TianShuData.getHollandInfo(state.hollandScores);
  const el = document.getElementById("holland-preview") || document.getElementById("holland-preview-outer");
  if (!el) return;
  el.innerHTML = `
    <div class="holland-card">
      <div class="holland-title">核心 3 位代码:<span class="tag tag-primary">${info.top3}</span></div>
      <div>${info.codeExplain}</div>
      <div class="holland-fits">
        <strong>主适配方向:</strong>
        <ul>${info.mainFit.map(f => `<li>${f}</li>`).join("")}</ul>
      </div>
      ${info.riskWarning !== "无明显短板维度" ? `<div class="risk-warning">⚠️ ${info.riskWarning}</div>` : ""}
    </div>
  `;
}

function nextStep4() {
  state.step = 5;
  updateProgress(5);
  renderStep5();
}

// ===== Step 5: 综合报告 =====
function renderStep5() {
  const app = document.getElementById("app");
  app.innerHTML = `<div class="step-card"><div class="loading">🔗 交叉验证中,生成完整报告...</div></div>`;

  setTimeout(() => {
    const bazi = state._bazi;
    const ziwei = state._ziwei;
    const mbti = window.TianShuData.getMbtiInfo(state.mbtiType);
    const holland = window.TianShuData.getHollandInfo(state.hollandScores);
    const cross = window.TianShuEngine.crossValidate(bazi, ziwei, mbti, holland);
    const majors = window.TianShuEngine.recommendMajors(cross, bazi, mbti, holland);
    const career = window.TianShuEngine.generateCareerPath(state.student, cross, majors);

    state.results = { bazi, ziwei, mbti, holland, cross, majors, career };

    app.innerHTML = `
      <div class="step-card">
        <div class="step-header">
          <span class="step-num">5/5</span>
          <h2>📊 综合定位</h2>
        </div>
        ${renderFullReport(state.student, state.results)}
        <div class="step-actions">
          <button class="btn-secondary" onclick="goBack()">← 上一步</button>
          <button class="btn-primary" onclick="window.print()">🖨️ 打印 / 保存 PDF</button>
          <button class="btn-primary" onclick="downloadReport()">💾 下载 HTML</button>
        </div>
      </div>
    `;
    window.scrollTo(0, 0);
  }, 300);
}

function renderFullReport(s, r) {
  return `
    <div class="report">
      <!-- 综合定位 -->
      <h2>🎯 一、综合定位</h2>
      <div class="callout">
        <div class="callout-title">${r.cross.positionLabel.label}</div>
        <div><strong>主方向:</strong>${r.cross.positionLabel.mainDir}</div>
      </div>

      <h3>核心竞争力组合</h3>
      <ul>${r.cross.advantages.map(a => `<li>${a}</li>`).join("")}</ul>

      <h3>核心短板</h3>
      <ul>${r.cross.shortcomings.map(s => `<li>${s}</li>`).join("")}</ul>

      <!-- 八字 -->
      <h2>🔮 二、八字命理分析</h2>
      <table class="data-table">
        <tr><th>项目</th><th>结果</th></tr>
        <tr><td>公历</td><td>${r.bazi.solar}</td></tr>
        <tr><td>农历</td><td>${r.bazi.lunar}</td></tr>
        <tr><td>年柱</td><td><strong>${r.bazi.yearZhu}</strong></td></tr>
        <tr><td>月柱</td><td><strong>${r.bazi.monthZhu}</strong></td></tr>
        <tr><td>日柱</td><td><strong>${r.bazi.dayZhu}</strong></td></tr>
        <tr><td>时柱</td><td><strong>${r.bazi.hourZhu}</strong></td></tr>
        <tr><td>日主</td><td>${r.bazi.dayMaster}(${r.bazi.dayMasterWx})</td></tr>
        <tr><td>五行统计</td><td>${Object.entries(r.bazi.wuxingCount).map(([k,v]) => `${k}:${v}`).join(" · ")}</td></tr>
        <tr><td>喜用神</td><td><span class="tag tag-primary">${r.bazi.xiZhong.join(" + ")}</span></td></tr>
        <tr><td>忌神</td><td><span class="tag tag-warning">${r.bazi.jiZhong.join(" + ")}</span></td></tr>
      </table>

      <div class="info-block">
        <strong>核心性格:</strong>${r.bazi.personality}<br>
        <strong>学业事业适配:</strong>${r.bazi.careerFit}
      </div>

      <!-- 紫微 -->
      <h2>⭐ 三、紫微斗数简版</h2>
      ${renderZiwei(r.ziwei)}

      <!-- MBTI -->
      <h2>🧠 四、MBTI 人格类型</h2>
      <div class="callout">
        <div class="callout-title">${r.mbti.fullType} · ${r.mbti.nick}</div>
        <div>${r.mbti.core}</div>
        <div><strong>倾向:</strong>${r.mbti.tendency}</div>
      </div>
      <div class="info-block">
        <strong>认知模式:</strong>${r.mbti.cog}<br>
        <strong>行为风格:</strong>${r.mbti.beh}
      </div>
      <table class="data-table">
        <tr><th>优势</th><td>${r.mbti.strength}</td></tr>
        <tr><th>短板</th><td style="color:#c53030;">${r.mbti.weakness}</td></tr>
      </table>

      <!-- 霍兰德 -->
      <h2>🎯 五、霍兰德职业兴趣</h2>
      <div class="callout">
        <div class="callout-title">核心 3 位代码:<span class="tag tag-primary">${r.holland.top3}</span></div>
        <div>${r.holland.codeExplain}</div>
      </div>
      <table class="data-table">
        <tr><th>维度</th><th>名称</th><th>得分</th><th>适配方向</th></tr>
        ${r.holland.sorted.map(([code, score]) => `
          <tr>
            <td><strong>${code}</strong></td>
            <td>${r.holland.dimensions[code].name}</td>
            <td>${score}</td>
            <td>${r.holland.dimensions[code].fit}</td>
          </tr>
        `).join("")}
      </table>

      <!-- 专业推荐 -->
      <h2>🎓 六、专业选择推荐</h2>

      <h3>第一优先级(核心适配)</h3>
      ${r.majors.firstPriority.map(m => `
        <div class="major-card">
          <div class="major-title">${m.major} <span class="tag tag-primary">匹配分 ${m.score}</span></div>
          <div class="major-meta">细分方向:${m.subs.join(" · ")}</div>
          <div><strong>匹配逻辑:</strong>${m.logic}</div>
          <div><strong>核心课程:</strong>${m.courses.join(" · ")}</div>
          <div><strong>院校梯队:</strong>${m.schools.slice(0, 6).join(" / ")}</div>
        </div>
      `).join("")}

      ${r.majors.secondPriority.length > 0 ? `
        <h3>第二优先级(次优适配)</h3>
        ${r.majors.secondPriority.map(m => `
          <div class="major-card">
            <div class="major-title">${m.major} <span class="tag">匹配分 ${m.score}</span></div>
            <div class="major-meta">细分方向:${m.subs.join(" · ")}</div>
            <div><strong>匹配逻辑:</strong>${m.logic}</div>
            <div><strong>院校梯队:</strong>${m.schools.slice(0, 6).join(" / ")}</div>
          </div>
        `).join("")}
      ` : ""}

      ${r.majors.thirdPriority.length > 0 ? `
        <h3>第三优先级(潜力适配)</h3>
        ${r.majors.thirdPriority.map(m => `
          <div class="major-card-mini">
            <strong>${m.major}</strong> · ${m.logic}
          </div>
        `).join("")}
      ` : ""}

      <h3>⚠️ 风险规避清单</h3>
      ${r.majors.risks.map(rk => `
        <div class="risk-card">
          <strong>${rk.major}</strong><br>
          风险:${rk.reason}<br>
          ${rk.alt ? `<span style="color:#2c5282;">替代方案:</span>${rk.alt}` : ""}
        </div>
      `).join("")}

      <!-- 生涯路径 -->
      <h2>🛤️ 七、生涯发展全路径</h2>
      ${r.career.stages.map((stage, i) => `
        <div class="career-stage">
          <div class="stage-title">阶段 ${i+1}:${stage.name}</div>
          <p><strong>核心目标:</strong>${stage.goal}</p>
          ${stage.actions ? `<h4>关键行动项</h4><ul>${stage.actions.map(a => `<li>${a}</li>`).join("")}</ul>` : ""}
          ${stage.jobs ? `<h4>岗位选择建议</h4><ul>${stage.jobs.map(j => `<li>${j}</li>`).join("")}</ul>` : ""}
          ${stage.industries ? `<h4>行业适配方向</h4><ul>${stage.industries.map(j => `<li>${j}</li>`).join("")}</ul>` : ""}
          ${stage.growth ? `<h4>核心成长重点</h4><ul>${stage.growth.map(j => `<li>${j}</li>`).join("")}</ul>` : ""}
          ${stage.paths ? `<h4>职业角色转型方向</h4>${stage.paths.map(p => `<div class="path-item"><strong>${p.name}</strong>:${p.desc}<br><em>适合:</em>${p.fit}</div>`).join("")}` : ""}
          ${stage.directions ? `<h4>职业发展可选方向</h4>${stage.directions.map(p => `<div class="path-item"><strong>${p.name}</strong>:${p.desc}</div>`).join("")}` : ""}
          ${stage.transitions ? `<h4>职业转型节点</h4><ul>${stage.transitions.map(t => `<li>${t}</li>`).join("")}</ul>` : ""}
          ${stage.abilities ? `<h4>能力提升重点</h4><ul>${stage.abilities.map(t => `<li>${t}</li>`).join("")}</ul>` : ""}
          ${stage.resources ? `<h4>资源积累</h4><ul>${stage.resources.map(t => `<li>${t}</li>`).join("")}</ul>` : ""}
          ${stage.competitive ? `<h4>核心竞争力打造</h4><ul>${stage.competitive.map(t => `<li>${t}</li>`).join("")}</ul>` : ""}
          ${stage.balance ? `<h4>工作生活平衡</h4><ul>${stage.balance.map(t => `<li>${t}</li>`).join("")}</ul>` : ""}
        </div>
      `).join("")}

      <h3>关键节点行动指引</h3>
      <table class="data-table">
        <tr><th>节点</th><th>时间</th><th>核心行动</th><th>注意事项</th></tr>
        ${r.career.keyNodes.map(n => `
          <tr>
            <td><strong>${n.name}</strong></td>
            <td>${n.time}</td>
            <td>${n.actions}</td>
            <td>${n.note}</td>
          </tr>
        `).join("")}
      </table>

      <h3>健康与状态管理</h3>
      <ul>${r.career.health.map(h => `<li>${h}</li>`).join("")}</ul>

      <!-- 总结建议 -->
      <h2>💡 八、核心建议与避坑提醒</h2>
      <h3>核心发展建议</h3>
      <ol>
        <li><strong>充分发挥 ${r.mbti.nick} + ${r.holland.top3} 的核心优势</strong>:在${r.majors.firstPriority[0] ? r.majors.firstPriority[0].major : ""}等适配方向深耕,前 5 年打造扎实核心能力。</li>
        <li><strong>针对性补足短板</strong>:${r.mbti.weakness}是显著风险,需刻意练习。</li>
        <li><strong>长期主义 + 动态调整</strong>:每 2-3 年做一次复盘,根据行业变化调整方向。</li>
        <li><strong>平衡身心</strong>:建立规律运动 + 兴趣释放的稳定机制。</li>
      </ol>

      <h3>核心避坑提醒</h3>
      <ol class="risk-list">
        <li>🚫 避免盲目追求院校排名而忽视专业适配度</li>
        <li>🚫 避免进入高社交强度赛道(纯销售、商务 BD)</li>
        <li>🚫 避免只看短期薪资选择岗位</li>
        <li>🚫 避免孤立学习,需主动建立导师 + 同伴网络</li>
        <li>🚫 避免被行业热点裹挟,持续学习核心能力</li>
      </ol>

      <div class="disclaimer">
        <strong>⚠️ 重要声明</strong><br>
        1. 本报告基于「东方命理(八字、紫微)+ 西方心理测评(MBTI、霍兰德)」交叉生成,命理部分无科学证据支持,仅作为文化参考。<br>
        2. 紫微斗数为简版排盘(仅取核心三宫),完整分析建议使用专业排盘软件。<br>
        3. 测评结果会随时间、经历变化,建议每 2-3 年做一次复盘调整。<br>
        4. 重大人生决策请结合实际能力测试、行业调研、家庭情况综合判断。
      </div>

      <div class="footer">
        天枢 · 综合特质测评与生涯规划系统 ${window.TIANSHU_VERSION || "v?"} (Web 版) · 生成于 ${new Date().toLocaleString("zh-CN")}
      </div>
    </div>
  `;
}

function downloadReport() {
  if (!state.results) return;
  const html = document.documentElement.outerHTML;
  const blob = new Blob([html], {type: "text/html;charset=utf-8"});
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `天枢报告_${state.student.name}_${new Date().toISOString().slice(0,10)}.html`;
  a.click();
  URL.revokeObjectURL(url);
}

function goBack() {
  state.step--;
  updateProgress(state.step);
  const renderers = [null, renderStep1, renderStep2, renderStep3, renderStep4, renderStep5];
  renderers[state.step]();
}

// 启动
document.addEventListener("DOMContentLoaded", init);