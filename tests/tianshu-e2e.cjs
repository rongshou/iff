/**
 * 天枢 E2E 测试 — 使用 Puppeteer 模拟完整 5 步操作流程
 * 用法: node tests/tianshu-e2e.cjs
 */
const puppeteer = require("puppeteer");
const { execSync } = require("child_process");
const path = require("path");

const BASE = "http://127.0.0.1/tianshu/";
let passed = 0, failed = 0;
const assert = (label, ok) => {
  if (ok) { passed++; console.log(`  ✅ ${label}`); }
  else { failed++; console.log(`  ❌ ${label}`); }
};
const section = (title) => console.log(`\n📍 ${title}`);

(async () => {
  console.log("=".repeat(56));
  console.log("  天枢 E2E 测试 (Puppeteer)");
  console.log("=".repeat(56));

  const browser = await puppeteer.launch({
    executablePath: "/usr/bin/google-chrome",
    headless: "new",
    args: ["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"]
  });

  const page = await browser.newPage();
  page.on("console", msg => {
    if (msg.type() === "error") console.log(`  [浏览器错误] ${msg.text()}`);
  });
  page.on("pageerror", err => {
    console.log(`  [页面错误] ${err.message}`);
  });

  // ==========================================
  section("Step 0: 页面加载与初始化");
  // ==========================================
  await page.goto(BASE, { waitUntil: "networkidle0", timeout: 15000 });
  await page.waitForSelector("#app", { timeout: 5000 });
  await page.waitForSelector("#progress-bar", { timeout: 5000 });

  const title = await page.title();
  assert("页面标题含'天枢'", title.includes("天枢"));

  const step1Active = await page.$eval(".progress-step.active", el => el.textContent);
  assert("初始化时 step 1 高亮", step1Active.includes("1"));

  const hasForm = await page.$("#f-name") !== null;
  assert("基础信息表单已渲染", hasForm);

  // 检查北斗七星 SVG
  const beidouSvg = await page.$("#beidou-container svg");
  assert("北斗七星 SVG 已渲染", beidouSvg !== null);

  const hasNums = (await page.$$(".progress-step")).length === 5;
  assert("进度条有 5 步", hasNums);

  // ==========================================
  section("Step 1: 填写基础信息");
  // ==========================================
  await page.type("#f-name", "测试学生");
  await page.select("#f-gender", "女");
  await page.$eval("#f-year", el => { el.value = "2006"; el.dispatchEvent(new Event("input")); });
  await page.$eval("#f-month", el => { el.value = "8"; el.dispatchEvent(new Event("input")); });
  await page.$eval("#f-day", el => { el.value = "20"; el.dispatchEvent(new Event("input")); });
  await page.$eval("#f-hour", el => { el.value = "6"; el.dispatchEvent(new Event("input")); });
  await page.type("#f-place", "上海");
  await page.select("#f-grade", "高三");

  await page.click(".btn-primary");
  await new Promise(r => setTimeout(r, 500));

  // ==========================================
  section("Step 2: 排盘 — 八字 + 紫微");
  // ==========================================
  await page.waitForSelector(".data-table", { timeout: 5000 });
  const step2Active = await page.$eval(".progress-step.active", el => el.textContent.trim());
  assert("Step 2 高亮", step2Active.includes("2"));

  const hasYearZhu = await page.$eval(".data-table", tbl => tbl.textContent.includes("年柱"));
  assert("八字年柱已显示", hasYearZhu);

  const hasZiwei = await page.$eval("#app", el => el.textContent.includes("紫微"));
  assert("紫微板块已显示", hasZiwei);

  const hasNext2 = await page.$(".btn-primary") !== null;
  assert("Step 2 有下一步按钮", hasNext2);

  // ==========================================
  section("Step 3: MBTI 选择");
  // ==========================================
  await page.click(".btn-primary");
  await new Promise(r => setTimeout(r, 300));

  const step3Active = await page.$eval(".progress-step.active", el => el.textContent.trim());
  assert("Step 3 高亮", step3Active.includes("3"));

  const hasMbtiSelect = await page.$("#f-mbti-base") !== null;
  assert("MBTI 下拉框存在", hasMbtiSelect);

  // 选择一个类型
  await page.select("#f-mbti-base", "INTJ");
  await new Promise(r => setTimeout(r, 200));

  const mbtiPreview = await page.$eval("#mbti-preview", el => el.textContent);
  assert("MBTI 预览已更新", mbtiPreview.includes("建筑师") || mbtiPreview.includes("INTJ"));

  // ==========================================
  section("Step 4: 霍兰德调整");
  // ==========================================
  await page.click(".btn-primary");
  await new Promise(r => setTimeout(r, 300));

  const step4Active = await page.$eval(".progress-step.active", el => el.textContent.trim());
  assert("Step 4 高亮", step4Active.includes("4"));

  const hasSliders = (await page.$$(".slider-row")).length === 6;
  assert("6 个霍兰德维度滑块", hasSliders);

  // 调整滑块
  await page.$eval("#s-I", el => { el.value = "90"; el.dispatchEvent(new Event("input")); });
  await new Promise(r => setTimeout(r, 100));
  const hollandVal = await page.$eval("#v-I", el => el.textContent);
  assert("研究型(I)滑块值已更新为 90", hollandVal === "90");

  // 检查预览
  const hollandPreview = await page.$eval("#holland-preview", el => el.textContent);
  assert("霍兰德预览已更新", hollandPreview.length > 10);

  // ==========================================
  section("Step 5: 生成报告");
  // ==========================================
  await page.click(".btn-primary");
  await new Promise(r => setTimeout(r, 800));

  const step5Active = await page.$eval(".progress-step.active", el => el.textContent.trim());
  assert("Step 5 高亮", step5Active.includes("5"));

  // 检查报告内容
  await page.waitForFunction(() => {
    const el = document.querySelector(".report");
    return el && el.textContent.length > 100;
  }, { timeout: 5000 });

  const reportText = await page.$eval(".report", el => el.textContent);

  const checks = {
    "报告含'综合定位'": "综合定位",
    "报告含'八字命理'": "八字命理",
    "报告含'MBTI 人格'": "MBTI",
    "报告含'霍兰德'": "霍兰德",
    "报告含'专业选择推荐'": "专业选择推荐",
    "报告含'生涯发展'": "生涯发展",
    "报告含'核心建议'": "核心建议",
    "报告含'重要声明'": "重要声明",
  };
  for (const [label, keyword] of Object.entries(checks)) {
    assert(label, reportText.includes(keyword));
  }

  // 检查定位标签
  const posLabel = await page.$eval(".callout-title", el => el.textContent);
  assert("定位标签 > 0 字符", posLabel.length > 0);

  // 检查第一优先级专业
  const hasFirstMajor = await page.$(".major-card") !== null;
  assert("专业推荐卡片已渲染", hasFirstMajor);

  // 检查生涯阶段
  const stageCount = (await page.$$(".career-stage")).length;
  assert(`生涯阶段数 ≥ 3 (有 ${stageCount})`, stageCount >= 3);

  // ==========================================
  section("回退测试");
  // ==========================================
  // 点"上一步"回到 step 4
  const backBtns = await page.$$(".btn-secondary");
  if (backBtns.length > 0) {
    await backBtns[0].click();
    await new Promise(r => setTimeout(r, 300));
    const backStep = await page.$eval(".progress-step.active", el => el.textContent.trim());
    assert("回退后 step 4 高亮", backStep.includes("4"));

    // 再回退到 step 3
    const backBtns2 = await page.$$(".btn-secondary");
    if (backBtns2.length > 0) {
      await backBtns2[0].click();
      await new Promise(r => setTimeout(r, 300));
      const backStep2 = await page.$eval(".progress-step.active", el => el.textContent.trim());
      assert("再回退后 step 3 高亮", backStep2.includes("3"));
    }
  }

  // ==========================================
  section("进度条填充验证");
  // ==========================================
  // 回到 step 5 验证
  await page.goto(BASE, { waitUntil: "networkidle0", timeout: 15000 });
  // 快速完成流程检验满进度
  await page.type("#f-name", "快速测试");
  await page.click(".btn-primary");
  await new Promise(r => setTimeout(r, 500));

  // 检查第 2 步进度条
  const progressFill = await page.$("#progress-fill");
  const fillWidth = await page.evaluate(el => el.style.width, progressFill);
  assert("Step 2 进度条宽度 > 0%", parseFloat(fillWidth) > 0);

  // ==========================================
  section("控制台无 JS 错误检查");
  // ==========================================
  const consoleErrors = [];
  page.on("console", msg => {
    if (msg.type() === "error") consoleErrors.push(msg.text());
  });
  await page.goto(BASE, { waitUntil: "networkidle0", timeout: 15000 });
  await new Promise(r => setTimeout(r, 500));

  const fatalErrors = consoleErrors.filter(e =>
    !e.includes("Failed to load resource") &&
    !e.includes("ERR_BLOCKED") &&
    !e.includes("favicon")
  );
  if (fatalErrors.length === 0) {
    assert("初次加载无 JS 错误", true);
  } else {
    console.log(`  [JS 错误] ${fatalErrors.join("; ")}`);
    assert("初次加载无 JS 错误", false);
  }

  // ==========================================
  section("下载报告按钮存在");
  // ==========================================
  // 快速走完流程到 step 5
  await page.type("#f-name", "下载测试");
  await page.click(".btn-primary");
  await new Promise(r => setTimeout(r, 300));
  await page.click(".btn-primary");
  await new Promise(r => setTimeout(r, 300));
  await page.select("#f-mbti-base", "INTJ");
  await page.click(".btn-primary");
  await new Promise(r => setTimeout(r, 300));
  await page.click(".btn-primary");
  await new Promise(r => setTimeout(r, 800));

  const hasDownloadBtn = await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll("button"));
    return buttons.some(b => b.textContent.includes("下载"));
  });
  assert("Step 5 有下载报告按钮", hasDownloadBtn);

  const hasPrintBtn = await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll("button"));
    return buttons.some(b => b.textContent.includes("打印") || b.textContent.includes("PDF"));
  });
  assert("Step 5 有打印/PDF 按钮", hasPrintBtn);

  // ===== 汇总 =====
  await browser.close();
  console.log("\n" + "=".repeat(56));
  console.log(`  结果: ${passed} 通过, ${failed} 失败, 总计 ${passed + failed}`);
  console.log("=".repeat(56));
  process.exit(failed > 0 ? 1 : 0);
})().catch(err => {
  console.error("E2E 测试异常:", err);
  process.exit(1);
});
