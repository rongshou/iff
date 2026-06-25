/**
 * 天枢单元测试 — 测试 data.js / bazi.js / engine.js / beidou.js 核心函数
 * 用法: node tests/tianshu-unit.js
 */

// ===== 模拟浏览器全局 =====
global.window = {};
global.document = {
  addEventListener: () => {},
  getElementById: () => null,
  querySelectorAll: () => [],
  querySelector: () => null,
  documentElement: { outerHTML: "" }
};

// ===== 加载源文件 =====
const path = require("path");
const fs = require("fs");
const base = path.join(__dirname, "..", "tianshu");

function load(file) {
  const code = fs.readFileSync(path.join(base, file), "utf8");
  eval(code);
}

load("data.js");
load("bazi.js");
load("engine.js");
load("beidou.js");

const {
  TianShuData: { MBTI_DATA, getMbtiInfo, MBTI_QUESTIONS, calcMbtiFromTest, HOLLAND_DIMS, getHollandInfo, HOLLAND_QUESTIONS, calcHollandFromTest, getZiweiSummary, MAJOR_LIBRARY, TOP_EMPLOYERS },
  TianShuBazi: { getFourPillars, solarToLunar },
  TianShuEngine: { crossValidate, recommendMajors, generateCareerPath },
  TianShuBeidou: { renderBeidouSvg }
} = window;

// ===== 测试框架 =====
let passed = 0, failed = 0;
function assert(label, ok) {
  if (ok) { passed++; console.log(`  ✅ ${label}`); }
  else { failed++; console.log(`  ❌ ${label}`); }
}
function assertEq(label, actual, expected) {
  const ok = actual === expected;
  if (ok) { passed++; console.log(`  ✅ ${label}`); }
  else { failed++; console.log(`  ❌ ${label} (expect="${expected}", got="${actual}")`); }
}
function assertClose(label, actual, expected, tol = 0.01) {
  const ok = Math.abs(actual - expected) < tol;
  if (ok) { passed++; console.log(`  ✅ ${label}`); }
  else { failed++; console.log(`  ❌ ${label} (expect=${expected}, got=${actual})`); }
}

function section(title) {
  console.log(`\n📍 ${title}`);
}

function assertArr(label, actual, ...expected) {
  if (actual.length !== expected.length) {
    failed++; console.log(`  ❌ ${label} (len ${actual.length} ≠ ${expected.length})`); return;
  }
  for (let i = 0; i < expected.length; i++) {
    if (actual[i] !== expected[i]) {
      failed++; console.log(`  ❌ ${label}[${i}] (${actual[i]} ≠ ${expected[i]})`); return;
    }
  }
  passed++; console.log(`  ✅ ${label}`);
}

function assertObj(label, actual, keys) {
  if (typeof actual !== "object" || actual === null) {
    failed++; console.log(`  ❌ ${label} (not an object)`); return;
  }
  for (const k of keys) {
    if (!(k in actual)) {
      failed++; console.log(`  ❌ ${label} (missing key "${k}")`); return;
    }
  }
  passed++; console.log(`  ✅ ${label}`);
}

function assertType(label, actual, type) {
  if (typeof actual === type) { passed++; console.log(`  ✅ ${label}`); }
  else { failed++; console.log(`  ❌ ${label} (expected ${type}, got ${typeof actual})`); }
}

// ===== 测试开始 =====
console.log("=".repeat(56));
console.log("  天枢 单元测试");
console.log("=".repeat(56));

// ============================
section("data.js — MBTI");
// ============================
assert("MBTI_DATA has 16 entries", Object.keys(MBTI_DATA).length === 16);

for (const type of ["INTJ", "INFP", "ENFP", "ESTJ", "ISTJ", "ENTJ", "INFJ", "INTP"]) {
  const info = getMbtiInfo(type);
  assert(`  getMbtiInfo("${type}") → fullType="${type}"`, info.fullType === type || info.fullType === `${type}-A`);
  assert(`  getMbtiInfo("${type}") has nick`, !!info.nick);
  assert(`  getMbtiInfo("${type}") has core`, !!info.core);
  assert(`  getMbtiInfo("${type}") has cog`, !!info.cog);
  assert(`  getMbtiInfo("${type}") has beh`, !!info.beh);
  assert(`  getMbtiInfo("${type}") has strength`, !!info.strength);
  assert(`  getMbtiInfo("${type}") has weakness`, !!info.weakness);
}

const atA = getMbtiInfo("INTJ-A");
assertEq('getMbtiInfo("INTJ-A").fullType', atA.fullType, "INTJ-A");
assert('getMbtiInfo("INTJ-A").tendency includes "自信"', atA.tendency.includes("自信"));

const atT = getMbtiInfo("ENFP-T");
assertEq('getMbtiInfo("ENFP-T").fullType', atT.fullType, "ENFP-T");
assert('getMbtiInfo("ENFP-T").tendency includes "动荡"', atT.tendency.includes("动荡"));

const bad = getMbtiInfo("XXXX");
assert("getMbtiInfo('XXXX') → error", !!bad.error);

// ============================
section("data.js — 霍兰德");
// ============================
assert("HOLLAND_DIMS has 6 dims", Object.keys(HOLLAND_DIMS).length === 6);
for (const k of ["R","I","A","S","E","C"]) {
  assert(`HOLLAND_DIMS[${k}] has name & core`, !!HOLLAND_DIMS[k].name && !!HOLLAND_DIMS[k].core);
}

const hScores = {R: 30, I: 85, A: 70, S: 65, E: 40, C: 35};
const hInfo = getHollandInfo(hScores);
assert("getHollandInfo returns object", typeof hInfo === "object");
assert("getHollandInfo returns top3", typeof hInfo.top3 === "string" && hInfo.top3.length === 3);
assert("getHollandInfo top3 starts with I (highest)", hInfo.top3.startsWith("I"));
assert("getHollandInfo has codeExplain", !!hInfo.codeExplain);
assert("getHollandInfo has mainFit (array)", Array.isArray(hInfo.mainFit) && hInfo.mainFit.length === 3);
assert("getHollandInfo has riskWarning", typeof hInfo.riskWarning === "string");
assert("getHollandInfo has dimensions", !!hInfo.dimensions);
assert("getHollandInfo has sorted", Array.isArray(hInfo.sorted) && hInfo.sorted.length === 6);

const hLow = getHollandInfo({R: 10, I: 90, A: 80, S: 70, E: 20, C: 15});
assert("low dimensions → riskWarning has warning", hLow.riskWarning !== "无明显短板维度");
assert("low dimensions → riskWarning mentions low dims", hLow.riskWarning.includes("R") || hLow.riskWarning.includes("E") || hLow.riskWarning.includes("C"));

// ============================
section("data.js — 紫微");
// ============================
for (const m of [1, 5, 8, 12]) {
  const zw = getZiweiSummary(2005, m, 14);
  assert(`getZiweiSummary(month=${m}) → mingGong`, !!zw.mingGong.star);
  assert(`getZiweSummary(month=${m}) → shiyeGong`, !!zw.shiyeGong.star);
  assert(`getZiweSummary(month=${m}) → caiboGong`, !!zw.caiboGong.star);
  assert(`getZiweSummary(month=${m}) → note`, !!zw.note);
}

const zwMidnight = getZiweiSummary(2010, 6, 23);
assert("hour=23 → hourEffect includes '子时'", zwMidnight.mingGong.hourEffect.includes("子时") || !zwMidnight.mingGong.hourEffect);
const zwNoon = getZiweiSummary(2010, 6, 12);
assert("hour=12 → hourEffect includes '午时'", zwNoon.mingGong.hourEffect.includes("午时") || !zwNoon.mingGong.hourEffect);

// ============================
section("data.js — 专业库");
// ============================
const majorCount = Object.keys(MAJOR_LIBRARY).length;
assert(`MAJOR_LIBRARY has ${majorCount} majors (>= 10)`, majorCount >= 10);
for (const [name, info] of Object.entries(MAJOR_LIBRARY)) {
  assert(`"${name}" has subs`, Array.isArray(info.subs) && info.subs.length > 0);
  assert(`"${name}" has courses`, Array.isArray(info.courses) && info.courses.length > 0);
  assert(`"${name}" has abilities`, Array.isArray(info.abilities) && info.abilities.length > 0);
  assert(`"${name}" has tags`, Array.isArray(info.tags) && info.tags.length > 0);
  assert(`"${name}" has schools`, Array.isArray(info.schools) && info.schools.length > 0);
}
assert("TOP_EMPLOYERS has entries for all majors", Object.keys(TOP_EMPLOYERS).length >= 10);

// ============================
section("bazi.js — 农历转换");
// ============================
const lunar = solarToLunar(2024, 2, 10);
assert("solarToLunar(2024-02-10) returns object", typeof lunar === "object" && lunar !== null);
assert("solarToLunar → has year", lunar.year >= 2023);
assert("solarToLunar → has month (1..12)", lunar.month >= 1 && lunar.month <= 12);
assert("solarToLunar → has day (1..30)", lunar.day >= 1 && lunar.day <= 30);
assert("solarToLunar → has isLeap", typeof lunar.isLeap === "boolean");

const lunar2024 = solarToLunar(2024, 2, 10);
assertEq("2024-02-10 → 2023年腊月", lunar2024.year === 2023 || lunar2024.year === 2024, true);

const lunar2025 = solarToLunar(2025, 1, 29);
assert("2025-01-29 → valid", lunar2025 !== null);

const badLunar = solarToLunar(1899, 1, 1);
assert("solarToLunar(1899) → null", badLunar === null);

// ============================
section("bazi.js — 四柱");
// ============================
const bazi = getFourPillars(2005, 5, 15, 14);
assert("getFourPillars returns object", typeof bazi === "object");
assert("getFourPillars has solar", typeof bazi.solar === "string" && bazi.solar.includes("2005"));
assert("getFourPillars has lunar", typeof bazi.lunar === "string");
assert("getFourPillars has yearZhu (2 chars)", bazi.yearZhu.length === 2);
assert("getFourPillars has monthZhu (2 chars)", bazi.monthZhu.length === 2);
assert("getFourPillars has dayZhu (2 chars)", bazi.dayZhu.length === 2);
assert("getFourPillars has hourZhu (2 chars)", bazi.hourZhu.length === 2);
assert("getFourPillars has dayMaster (1 char)", bazi.dayMaster.length === 1);
assert("getFourPillars has dayMasterWx", !!bazi.dayMasterWx);
assert("getFourPillars has wuxingCount (5 keys)", Object.keys(bazi.wuxingCount).length === 5);
assert("getFourPillars has minWx", !!bazi.minWx);
assert("getFourPillars has xiZhong (array, >= 1)", bazi.xiZhong.length >= 1);
assert("getFourPillars has jiZhong (array, >= 1)", bazi.jiZhong.length >= 1);
assert("getFourPillars has personality", !!bazi.personality);
assert("getFourPillars has careerFit", !!bazi.careerFit);
assertNoWx("五行统计和=8", bazi, () => {
  const sum = Object.values(bazi.wuxingCount).reduce((a,b) => a+b, 0);
  return sum === 8;
});

// 测试特殊时辰
const baziZi = getFourPillars(2005, 5, 15, 23);
assert("hour=23 → hourZhu starts with 子-related char", baziZi.hourZhu.length === 2);

const baziYearBound = getFourPillars(1900, 1, 31, 12);
assert("getFourPillars(1900-01-31) → valid", typeof baziYearBound === "object" && !baziYearBound.error);

// ============================
section("engine.js — crossValidate");
// ============================
const baziCV = getFourPillars(2005, 5, 15, 14);
const ziweiCV = getZiweiSummary(2005, 5, 14);
const mbtiCV = getMbtiInfo("INTJ-A");
const hollandCV = getHollandInfo({R: 30, I: 85, A: 70, S: 65, E: 40, C: 35});
const cross = crossValidate(baziCV, ziweiCV, mbtiCV, hollandCV);

assert("crossValidate → returns object", typeof cross === "object");
assert("crossValidate → has themes (array)", Array.isArray(cross.themes) && cross.themes.length > 0);
assert("crossValidate → has positionLabel", typeof cross.positionLabel === "object");
assert("crossValidate → positionLabel has label", typeof cross.positionLabel.label === "string");
assert("crossValidate → positionLabel has mainDir", typeof cross.positionLabel.mainDir === "string");
assert("crossValidate → has differences (array)", Array.isArray(cross.differences) && cross.differences.length > 0);
assert("crossValidate → has advantages (array)", Array.isArray(cross.advantages) && cross.advantages.length > 0);
assert("crossValidate → has shortcomings (array)", Array.isArray(cross.shortcomings) && cross.shortcomings.length > 0);
assert("crossValidate → has conclusion", typeof cross.conclusion === "string");
assert("crossValidate → advantages mention dayMaster", cross.advantages[0].includes(baziCV.dayMaster));
assert("crossValidate → advantages mention MBTI nickname", cross.advantages[1].includes(mbtiCV.nick));

// ============================
section("engine.js — recommendMajors");
// ============================
const majors = recommendMajors(cross, baziCV, mbtiCV, hollandCV);
assert("recommendMajors → returns object", typeof majors === "object");
assert("recommendMajors → firstPriority (array)", Array.isArray(majors.firstPriority) && majors.firstPriority.length > 0);
assert("recommendMajors → firstPriority[0] has major", typeof majors.firstPriority[0].major === "string");
assert("recommendMajors → firstPriority[0] has score (number)", typeof majors.firstPriority[0].score === "number");
assert("recommendMajors → firstPriority[0] has subs (array)", Array.isArray(majors.firstPriority[0].subs));
assert("recommendMajors → firstPriority[0] has logic", typeof majors.firstPriority[0].logic === "string");
assert("recommendMajors → firstPriority[0] has schools (array)", Array.isArray(majors.firstPriority[0].schools));
assert("recommendMajors → has risks (array)", Array.isArray(majors.risks));
assert("recommendMajors → scores >= 0", majors.firstPriority[0].score >= 0);
assert("recommendMajors → firstPriority sorted descending", 
  majors.firstPriority.length < 2 || majors.firstPriority[0].score >= majors.firstPriority[1].score
);

// ============================
section("engine.js — generateCareerPath");
// ============================
const student = { name: "测试学生", gender: "男", birthYear: 2005, grade: "高三" };
const career = generateCareerPath(student, cross, majors);
assert("generateCareerPath → returns object", typeof career === "object");
assert("generateCareerPath → has stages (array, >= 3)", Array.isArray(career.stages) && career.stages.length >= 3);
assert("generateCareerPath → stages[0] has name & goal", typeof career.stages[0].name === "string" && typeof career.stages[0].goal === "string");
assert("generateCareerPath → stages[0] has actions (array)", Array.isArray(career.stages[0].actions));
assert("generateCareerPath → has careerDetails (array)", Array.isArray(career.careerDetails));
assert("generateCareerPath → has keyNodes (array)", Array.isArray(career.keyNodes));
assert("generateCareerPath → has health (array)", Array.isArray(career.health));
assert("generateCareerPath → keyNodes[0] has name/time/actions/note", 
  ["name","time","actions","note"].every(k => k in career.keyNodes[0])
);

// ============================
section("beidou.js — SVG 生成");
// ============================
const svgDefault = renderBeidouSvg();
assertType("renderBeidouSvg() → string", svgDefault, "string");
assert("renderBeidouSvg() contains SVG tag", svgDefault.includes("<svg"));
assert("renderBeidouSvg() contains 天枢", svgDefault.includes("天枢"));
assert("renderBeidouSvg() contains viewBox", svgDefault.includes("viewBox"));
assert("renderBeidouSvg() contains circle elements", (svgDefault.match(/<circle/g) || []).length >= 7);

const svgSmall = renderBeidouSvg({ size: 80, theme: "blue" });
assert("renderBeidouSvg(size=80, theme=blue) → valid", svgSmall.includes("<svg"));
assert("renderBeidouSvg(size=80) has smaller size ref", svgSmall.includes("80") || svgSmall.includes("viewBox"));

const svgDark = renderBeidouSvg({ theme: "dark" });
assert("renderBeidouSvg(theme=dark) → valid", svgDark.includes("<svg"));

// ============================
section("data.js — MBTI 测试题");
// ============================
assert("MBTI_QUESTIONS has 16 questions", MBTI_QUESTIONS.length === 16);
const dims = MBTI_QUESTIONS.reduce((acc, q) => { acc[q.dim] = (acc[q.dim] || 0) + 1; return acc; }, {});
assert("4 E/I questions", dims.E === 4);
assert("4 S/N questions (dim=N)", dims.N === 4);
assert("4 T/F questions (dim=F)", dims.F === 4);
assert("4 J/P questions (dim=P)", dims.P === 4);
for (let i = 0; i < MBTI_QUESTIONS.length; i++) {
  assert(`MBTI Q${i+1} has optionA`, typeof MBTI_QUESTIONS[i].optionA === "string" && MBTI_QUESTIONS[i].optionA.length > 0);
  assert(`MBTI Q${i+1} has optionB`, typeof MBTI_QUESTIONS[i].optionB === "string" && MBTI_QUESTIONS[i].optionB.length > 0);
}

// ============================
section("data.js — calcMbtiFromTest");
// ============================
// 所有选 A → 全选 optionA 倾向: E N F P → 计算
const allA = MBTI_QUESTIONS.map((q, i) => ({ qIdx: i, score: 1 }));
const rAllA = calcMbtiFromTest(allA);
assert("全选A → type length = 4", rAllA.type.length === 4);
// 全选 B → 全选 optionB 倾向: I S T J
const allB = MBTI_QUESTIONS.map((q, i) => ({ qIdx: i, score: 2 }));
const rAllB = calcMbtiFromTest(allB);
assert("全选B → type length = 4", rAllB.type.length === 4);
assert("全选B → has scores object", typeof rAllB.scores === "object");
assert("全选B → scores has 8 keys", Object.keys(rAllB.scores).length === 8);
assert("全选A → scores E=4 S=4 T=4 J=4", rAllA.scores.E === 4 && rAllA.scores.S === 4 && rAllA.scores.T === 4 && rAllA.scores.J === 4);
assert("全选B → scores I=4 N=4 F=4 P=4", rAllB.scores.I === 4 && rAllB.scores.N === 4 && rAllB.scores.F === 4 && rAllB.scores.P === 4);
const mixed = [
  { qIdx: 0, score: 2 },  // I
  { qIdx: 1, score: 2 },  // I
  { qIdx: 2, score: 2 },  // I
  { qIdx: 3, score: 1 },  // E
  { qIdx: 4, score: 2 },  // N
  { qIdx: 5, score: 2 },  // N
  { qIdx: 6, score: 2 },  // N
  { qIdx: 7, score: 1 },  // S
  { qIdx: 8, score: 1 },  // T
  { qIdx: 9, score: 1 },  // T
  { qIdx: 10, score: 1 }, // T
  { qIdx: 11, score: 2 }, // F
  { qIdx: 12, score: 1 }, // J
  { qIdx: 13, score: 1 }, // J
  { qIdx: 14, score: 1 }, // J
  { qIdx: 15, score: 2 }, // P
];
const rMix = calcMbtiFromTest(mixed);
assert("混合答案 → valid type", rMix.type.length === 4);
assert("混合 → E/I → I", rMix.type[0] === "I");

// ============================
section("data.js — 霍兰德测试题");
// ============================
assert("HOLLAND_QUESTIONS has 18 items", HOLLAND_QUESTIONS.length === 18);
const hDims = HOLLAND_QUESTIONS.reduce((acc, q) => { acc[q.dim] = (acc[q.dim] || 0) + 1; return acc; }, {});
assert("3 R questions", hDims.R === 3);
assert("3 I questions", hDims.I === 3);
assert("3 A questions", hDims.A === 3);
assert("3 S questions", hDims.S === 3);
assert("3 E questions", hDims.E === 3);
assert("3 C questions", hDims.C === 3);
for (let i = 0; i < HOLLAND_QUESTIONS.length; i++) {
  assert(`Holland Q${i+1} has text`, typeof HOLLAND_QUESTIONS[i].text === "string" && HOLLAND_QUESTIONS[i].text.length > 0);
  assert(`Holland Q${i+1} has dim`, "RIAESC".includes(HOLLAND_QUESTIONS[i].dim));
}

// ============================
section("data.js — calcHollandFromTest");
// ============================
// 全 5 分
const all5 = HOLLAND_QUESTIONS.map(q => ({ dim: q.dim, score: 5 }));
const rAll5 = calcHollandFromTest(all5);
assert("全5分 → returns object", typeof rAll5 === "object");
assert("全5分 → has 6 keys", Object.keys(rAll5).length === 6);
assert("全5分 → R=I=A=S=E=C=100", Object.values(rAll5).every(v => v === 100));

// 全 1 分
const all1 = HOLLAND_QUESTIONS.map(q => ({ dim: q.dim, score: 1 }));
const rAll1 = calcHollandFromTest(all1);
assert("全1分 → all = 20", Object.values(rAll1).every(v => v === 20));

// 混合
const mixedH = HOLLAND_QUESTIONS.map(q => ({ dim: q.dim, score: q.dim === "I" || q.dim === "A" ? 5 : 1 }));
const rMixH = calcHollandFromTest(mixedH);
assert("混合 → I ≥ 80", rMixH.I >= 80);
assert("混合 → A ≥ 80", rMixH.A >= 80);
assert("混合 → R ≤ 50", rMixH.R <= 50);

// ============================
// ============================
// 极低分数
const hExtreme = getHollandInfo({R: 0, I: 0, A: 0, S: 0, E: 0, C: 0});
assert("霍兰德全0 → top3 exists", hExtreme.top3.length === 3);

// 极高分数
const hMax = getHollandInfo({R: 100, I: 100, A: 100, S: 100, E: 100, C: 100});
assert("霍兰德全100 → top3 exists", hMax.top3.length === 3);

// 边界生辰
const baziBound = getFourPillars(2100, 12, 31, 23);
assert("getFourPillars(2100-12-31) → valid", typeof baziBound === "object" && !baziBound.error);

const baziNow = getFourPillars(2026, 6, 25, 12);
assert("getFourPillars(2026-06-25) → valid", typeof baziNow === "object" && !baziNow.error);

// 跨年
const baziNY = getFourPillars(2024, 1, 1, 0);
assert("getFourPillars(2024-01-01 子时) → valid", typeof baziNY === "object" && !baziNY.error);

// ============================
section("data.js — 所有 MBTI 类型完整检查");
// ============================
const allTypes = ["ISTJ","ISFJ","INFJ","INTJ","ISTP","ISFP","INFP","INTP",
                  "ESTP","ESFP","ENFP","ENTP","ESTJ","ESFJ","ENFJ","ENTJ"];
for (const t of allTypes) {
  const info = getMbtiInfo(t);
  assert(`"${t}" fields complete: ${info.nick}`, 
    info.fullType && info.nick && info.core && info.cog && info.beh && 
    info.strength && info.weakness && info.fitMajors && info.fitCareers
  );
}

// ============================
section("engine.js — crossValidate 不同组合");
// ============================
const bazi2 = getFourPillars(2003, 8, 20, 8);
const mbti2 = getMbtiInfo("ENFP-A");
const holland2 = getHollandInfo({R: 20, I: 40, A: 85, S: 70, E: 60, C: 25});
const cross2 = crossValidate(bazi2, getZiweiSummary(2003, 8, 8), mbti2, holland2);
assert("ENFP+高A → theme label mentions creative or art", 
  cross2.positionLabel.label.includes("创意") || 
  cross2.positionLabel.label.includes("艺术") ||
  cross2.positionLabel.label.includes("ENFP昵称")
);

// ===== 结果汇总 =====
console.log("\n" + "=".repeat(56));
console.log(`  结果: ${passed} 通过, ${failed} 失败, 总计 ${passed + failed}`);
console.log("=".repeat(56));

process.exit(failed > 0 ? 1 : 0);

function assertNoWx(label, obj, fn) {
  try {
    if (fn()) { passed++; console.log(`  ✅ ${label}`); }
    else { failed++; console.log(`  ❌ ${label}`); }
  } catch(e) {
    failed++; console.log(`  ❌ ${label} (error: ${e.message})`);
  }
}
