/**
 * 天枢 E2E 测试 — Vite 版 Puppeteer 流程测试
 * 用法: node tests/tianshu-e2e.cjs
 */
const puppeteer = require("puppeteer");

const BASE = "http://127.0.0.1:8080/tianshu/";
let passed = 0, failed = 0;
const assert = (label, ok) => {
  if (ok) { passed++; console.log(`  ✅ ${label}`); }
  else { failed++; console.log(`  ❌ ${label}`); }
};
const section = (title) => console.log(`\n📍 ${title}`);

(async () => {
  console.log("=".repeat(56));
  console.log("  天枢 E2E 测试 (Puppeteer) — Vite");
  console.log("=".repeat(56));

  const browser = await puppeteer.launch({
    executablePath: "/usr/bin/google-chrome",
    headless: "new",
    args: ["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"]
  });

  const page = await browser.newPage();
  page.on("pageerror", err => console.log(`  [页面错误] ${err.message}`));

  // ==========================================
  section("Step 0: 页面加载与初始化");
  // ==========================================
  await page.goto(BASE, { waitUntil: "networkidle0", timeout: 15000 });
  await page.waitForSelector("#root", { timeout: 5000 });

  const title = await page.title();
  assert("页面标题含'天枢'", title.includes("天枢"));

  const hasRoot = await page.$("#root") !== null;
  assert("#root 已渲染", hasRoot);

  const step1Active = await page.$eval(".step-pill.active", el => el.textContent);
  assert("初始化时 step 1 高亮", step1Active.includes("1"));

  const stepCount = (await page.$$(".step-pill")).length;
  assert(`进度条有 ${stepCount} 步`, stepCount === 5);

  const hasFormInputs = (await page.$$("input.form-input, select.form-input")).length >= 4;
  assert("基础信息表单输入框 ≥ 4 个", hasFormInputs);

  const hasSubmitBtn = await page.$(".btn-primary") !== null;
  assert("有「下一步」按钮", hasSubmitBtn);

  // ==========================================
  section("导航栏检查");
  // ==========================================
  const navLinks = (await page.$$(".nav-pill")).length;
  assert(`导航链接数 >= 3 (有 ${navLinks})`, navLinks >= 3);

  const brandText = await page.$eval(".nav-brand", el => el.textContent);
  assert("品牌文字含 TIA", brandText.includes("TIA"));

  // ==========================================
  section("Step 1: 填写基础信息 (via evaluate)");
  // ==========================================
  const fieldCount = await page.evaluate(() => {
    const els = document.querySelectorAll("input.form-input, select.form-input");
    return els.length;
  });
  assert(`表单字段数 >= 7 (有 ${fieldCount})`, fieldCount >= 7);

  // Use evaluate to fill form — avoids click/type flakiness
  const filled = await page.evaluate(() => {
    const els = document.querySelectorAll("input.form-input, select.form-input");
    if (els.length < 7) return false;
    // 0: name (text input)
    const inp0 = els[0]; if (inp0.tagName === "INPUT") {
      const nativeSetter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value").set;
      nativeSetter.call(inp0, "测试学生");
      inp0.dispatchEvent(new Event("input", { bubbles: true }));
      inp0.dispatchEvent(new Event("change", { bubbles: true }));
    }
    // 1: gender (select)
    const inp1 = els[1];
    if (inp1.tagName === "SELECT") { inp1.value = "女"; inp1.dispatchEvent(new Event("change", { bubbles: true })); }
    // 2-5: year, month, day, hour
    const vals = ["2006","8","20","6"];
    for (let i = 0; i < 4 && i+2 < els.length; i++) {
      const inp = els[i+2];
      if (inp.tagName === "INPUT") {
        const nativeSetter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value").set;
        nativeSetter.call(inp, vals[i]);
        inp.dispatchEvent(new Event("input", { bubbles: true }));
        inp.dispatchEvent(new Event("change", { bubbles: true }));
      }
    }
    // 6: grade (select)
    if (els.length > 6) {
      const inp6 = els[6];
      if (inp6.tagName === "SELECT") { inp6.value = "高三"; inp6.dispatchEvent(new Event("change", { bubbles: true })); }
    }
    return true;
  });
  assert("表单字段填充成功", filled);

  // 点击下一步
  await page.evaluate(() => {
    const btn = document.querySelector(".btn-primary");
    if (btn) btn.click();
  });
      await new Promise(r => setTimeout(r, 1500));

  // ==========================================
  section("Step 2: 排盘 — 八字 + 紫微");
  // ==========================================
  const step2Active = await page.$eval(".step-pill.active", el => el.textContent.trim());
  assert("Step 2 高亮", step2Active.includes("2"));

  const pageContent = await page.evaluate(() => document.body.textContent);
  assert("八字信息已出现", pageContent.includes("八字") || /[甲乙丙丁戊己庚辛壬癸]/.test(pageContent));
  const hasZiwei = pageContent.includes("命宫") || pageContent.includes("紫微");
  assert("紫微板块已显示", hasZiwei);

  const hasNextBtn2 = await page.$(".btn-primary") !== null;
  assert("Step 2 有下一步按钮", hasNextBtn2);

  // ==========================================
  section("Step 3-5: 快速完成");
  // ==========================================
  // 单击下一步走完流程
  for (let step = 3; step <= 5; step++) {
    await page.evaluate(() => {
      const btn = document.querySelector(".btn-primary");
      if (btn) btn.click();
    });
    await new Promise(r => setTimeout(r, 1200));

    if (step === 3) {
      // select INTJ for MBTI
      await page.evaluate(() => {
        const selects = document.querySelectorAll("select");
        if (selects.length > 0) { selects[0].value = "INTJ"; selects[0].dispatchEvent(new Event("change", { bubbles: true })); }
      });
      await new Promise(r => setTimeout(r, 300));
      const c3 = await page.evaluate(() => document.body.textContent);
      assert("MBTI 页面已展示", c3.includes("MBTI") || c3.includes("INTJ"));
    } else if (step === 4) {
      const c4 = await page.evaluate(() => document.body.textContent);
      assert("霍兰德页面已展示", c4.includes("霍兰德"));
    } else if (step === 5) {
  await new Promise(r => setTimeout(r, 1500));
    }
  }

  // ==========================================
  section("Step 5: 报告检查");
  // ==========================================
  const finalContent = await page.evaluate(() => document.body.textContent);
  assert("报告已生成，长度 > 200", finalContent.length > 200);

  const keywordChecks = {
    "'八字排盘'": "八字排盘",
    "'MBTI'": "MBTI",
    "'霍兰德'": "霍兰德",
    "'推荐专业方向'": "推荐专业方向",
    "'职业方向细分'": "研究生细分赛道",
    "'潜在挑战与建议'": "潜在挑战与建议",
    "'交叉解读'": "交叉解读",
  };
  for (const [label, keyword] of Object.entries(keywordChecks)) {
    assert(`报告含${label}`, finalContent.includes(keyword));
  }

  // ==========================================
  section("控制台无 JS 错误检查");
  // ==========================================
  const consoleErrors = [];
  page.on("console", msg => {
    if (msg.type() === "error") consoleErrors.push(msg.text());
  });
  await page.goto(BASE, { waitUntil: "networkidle0", timeout: 15000 });
  await new Promise(r => setTimeout(r, 2000));

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

  // ===== 汇总 =====
  await browser.close();
  console.log("\n" + "=".repeat(56));
  console.log(`  结果: ${passed} 通过, ${failed} 失败, 总计 ${passed + failed}`);
  console.log("=".repeat(56));
  process.exit(failed > 0 ? 1 : 0);
})().catch(err => {
  console.error("E2E 测试异常:", err);
  console.log(`\n  部分结果: ${passed} 通过, ${failed} 失败`);
  process.exit(1);
});
