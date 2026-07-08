/**
 * Step5Report - 综合测评报告（sub-3.6）
 *
 * 迁移自 legacy/app.js 的 renderStep5() + renderFullReport()
 * 调用 window.TianShuEngine 全套计算函数。
 *
 * 功能：
 * - 调 engine 计算交叉验证 / 专业推荐 / 生涯路径 / 挑战 / 年度预测
 * - 渲染报告核心内容
 * - 自动保存到 localStorage（iff_profile / iff_history）
 * - 打印 / 下载 HTML 按钮
 */

import { useEffect, useState } from "react";
import { useTianshu } from "./TianshuContext";
import { TianShuData, TianShuEngine } from "./types";

export default function Step5Report() {
  const { state, goPrev, setState } = useTianshu();
  const [loading, setLoading] = useState(true);
  const [results, setResults] = useState<any>(null);

  useEffect(() => {
    const timer = setTimeout(() => {
      try {
        const bazi = state._bazi;
        const ziwei = state._ziwei;
        const mbti = TianShuData.getMbtiInfo(state.mbtiType);
        const holland = TianShuData.getHollandInfo(state.hollandScores);
        const cross = TianShuEngine.crossValidate(bazi, ziwei, mbti, holland);
        const majors = TianShuEngine.recommendMajors(cross, bazi, mbti, holland);
        const gradRecs = TianShuEngine.recommendGradPrograms(cross, bazi, mbti, holland);
        const career = TianShuEngine.generateCareerPath(state.student, cross, majors, gradRecs);
        const challenges = TianShuEngine.generateChallenges(bazi, mbti, holland, cross);
        const yearlyForecast = TianShuEngine.generateYearlyForecast(2026, bazi, mbti);
        const summary = TianShuEngine.generateReportSummary(bazi, ziwei, mbti, holland, cross);
        const sunSign = TianShuData.getSunSign(state.student.birthMonth, state.student.birthDay);

        const fullResults = { bazi, ziwei, mbti, holland, cross, majors, gradRecs, career, challenges, yearlyForecast, summary, sunSign };

        setResults(fullResults);
        setState({ results: fullResults });

        // 自动保存到 localStorage（与旧版行为一致）
        try {
          const existingProfile = JSON.parse(localStorage.getItem("iff_profile") || "{}");
          existingProfile.tianshu = {
            student: state.student,
            bazi,
            mbti: mbti ? {
              type: state.mbtiType, nick: mbti.nick, core: mbti.core,
              strength: mbti.strength, weakness: mbti.weakness, fitMajors: mbti.fitMajors,
            } : null,
            holland: holland ? {
              scores: state.hollandScores,
              top3: holland.top3 || "",
              codeExplain: holland.codeExplain || "",
              dimensions: holland.dimensions || {},
              sorted: holland.sorted || [],
            } : null,
            sunSign,
            summary: summary ? { tags: summary.tags || [], summary: summary.summary || "" } : null,
            updated_at: new Date().toISOString(),
          };
          existingProfile.updated_at = new Date().toISOString();
          localStorage.setItem("iff_profile", JSON.stringify(existingProfile));

          const history = JSON.parse(localStorage.getItem("iff_history") || "[]");
          history.unshift({
            id: Date.now().toString(36) + Math.random().toString(36).slice(2, 8),
            type: "tianshu_report",
            system: "tianshu",
            data: { student: state.student, results: fullResults },
            summary: summary?.summary?.slice(0, 60) || "综合测评报告",
            subtitle: `${state.student.name || "匿名"} · ${state.student.grade || ""}`,
            created_at: new Date().toISOString(),
          });
          if (history.length > 200) history.length = 200;
          localStorage.setItem("iff_history", JSON.stringify(history));
        } catch (e) {
          console.warn("保存档案失败:", e);
        }

        // 滚到顶部
        window.scrollTo(0, 0);
      } catch (e: any) {
        console.error("报告生成失败:", e);
      } finally {
        setLoading(false);
      }
    }, 300);
    return () => clearTimeout(timer);
  }, []);

  function handlePrint() {
    window.print();
  }

  function handleDownload() {
    // 简化版：把当前页面 HTML 转成 blob 下载
    const html = `<!DOCTYPE html><html><head><meta charset="UTF-8"><title>${state.student.name || "学生"} · 天枢综合报告</title></head><body>${document.querySelector(".tianshu-main")?.innerHTML || ""}</body></html>`;
    const blob = new Blob([html], { type: "text/html;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `天枢报告_${state.student.name || "匿名"}_${new Date().toISOString().slice(0, 10)}.html`;
    a.click();
    URL.revokeObjectURL(url);
  }

  if (loading) {
    return (
      <div className="step-card-placeholder">
        <div className="loading-state">🔗 交叉验证中,生成完整报告...</div>
      </div>
    );
  }

  if (!results) {
    return (
      <div className="step-card-placeholder">
        <div className="error-state">报告生成失败,请重试</div>
        <div className="step-actions">
          <button onClick={goPrev} className="btn-secondary">← 上一步</button>
        </div>
      </div>
    );
  }

  return (
    <div className="step-card-placeholder">
      <div className="step-header">
        <span className="step-num">5/5</span>
        <h2>📊 综合测评报告</h2>
      </div>

      {/* 报告头部 */}
      <div className="report-header">
        <div className="report-title">{state.student.name || "学生"} · 综合特质测评与生涯规划报告</div>
        <div className="report-tags">
          <span className="tag tag-primary">{state.student.grade}</span>
          {results.summary?.tags?.map((t: string, i: number) => (
            <span key={i} className="tag tag-primary">{t}</span>
          ))}
        </div>
        <div className="report-quote">{results.summary?.summary}</div>
      </div>

      {/* 一、核心命理与心理特质整合 */}
      <section className="report-section">
        <h2>一、核心命理与心理特质整合</h2>
        <p className="report-desc">
          将东方命理（八字、紫微斗数）、西方占星、现代心理学（MBTI、霍兰德）交叉验证,勾勒更立体的天赋图谱。
        </p>

        {/* 八字 */}
        <h3>1. 八字排盘</h3>
        <table className="data-table">
          <thead><tr><th>项目</th><th>结果</th></tr></thead>
          <tbody>
            <tr><td>公历</td><td>{results.bazi.solar}</td></tr>
            <tr><td>农历</td><td>{results.bazi.lunar}</td></tr>
            <tr><td>日主</td><td>{results.bazi.dayMaster}（{results.bazi.dayMasterWx}）</td></tr>
            <tr><td>喜用神</td><td><span className="tag tag-primary">{results.bazi.xiZhong?.join(" + ")}</span></td></tr>
            <tr><td>忌神</td><td><span className="tag tag-warning">{results.bazi.jiZhong?.join(" + ")}</span></td></tr>
          </tbody>
        </table>

        {/* 紫微 */}
        <h3>2. 紫微斗数</h3>
        <div className="gong-grid">
          <ZiweiCard title="命宫" gong={results.ziwei.mingGong} />
          <ZiweiCard title="事业宫" gong={results.ziwei.shiyeGong} />
          <ZiweiCard title="财帛宫" gong={results.ziwei.caiboGong} />
        </div>

        {/* 星座 */}
        {results.sunSign && (
          <>
            <h3>3. 太阳星座</h3>
            <div className="info-block">
              <strong>{results.sunSign.nameCN} ({results.sunSign.eng})</strong> · {results.sunSign.symbol}<br />
              元素:{results.sunSign.element} · 特质:{results.sunSign.quality} · 守护星:{results.sunSign.ruler}<br />
              <strong>性格:</strong>{results.sunSign.trait}<br />
              <strong>优势:</strong>{results.sunSign.strength}<br />
              <strong>短板:</strong>{results.sunSign.weakness}<br />
              <strong>职业:</strong>{results.sunSign.career}
            </div>
          </>
        )}

        {/* MBTI + 霍兰德 交叉 */}
        <h3>4. MBTI + 霍兰德 交叉解读</h3>
        <div className="cross-grid">
          <div className="cross-card">
            <div className="cross-card-title">🧠 MBTI · {results.mbti?.fullType}</div>
            <div className="cross-card-sub">{results.mbti?.nick}</div>
            <div>{results.mbti?.core}</div>
            <div style={{ marginTop: 8 }}><strong>优势:</strong>{results.mbti?.strength}</div>
            <div><strong>短板:</strong><span style={{ color: "#c53030" }}>{results.mbti?.weakness}</span></div>
            <div><strong>适配专业:</strong>{results.mbti?.fitMajors}</div>
          </div>
          <div className="cross-card">
            <div className="cross-card-title">🎯 霍兰德 · {results.holland?.top3}</div>
            <div className="cross-card-sub">{results.holland?.codeExplain}</div>
            <div style={{ marginTop: 8 }}><strong>主适配方向:</strong></div>
            <ul>
              {results.holland?.mainFit?.map((f: string, i: number) => <li key={i}>{f}</li>)}
            </ul>
            {results.holland?.riskWarning && results.holland.riskWarning !== "无明显短板维度" && (
              <div className="risk-warning">⚠️ {results.holland.riskWarning}</div>
            )}
          </div>
        </div>
      </section>

      {/* 二、专业与方向建议 */}
      <section className="report-section">
        <h2>二、专业与发展方向建议</h2>
        <p className="report-desc">当前学段:{state.student.grade} —— 重点推荐本科/研究生方向,作为未来深耕参考。</p>
        {results.majors && (
          <div className="info-block">
            <strong>推荐专业方向:</strong>
            <ul>
              {results.majors.slice(0, 6).map((m: any, i: number) => (
                <li key={i}>{typeof m === "string" ? m : m.name || JSON.stringify(m)}</li>
              ))}
            </ul>
          </div>
        )}
        {results.gradRecs && (
          <div className="info-block">
            <strong>研究生细分赛道:</strong>
            <ul>
              {results.gradRecs.slice(0, 5).map((g: any, i: number) => (
                <li key={i}>{typeof g === "string" ? g : g.name || JSON.stringify(g)}</li>
              ))}
            </ul>
          </div>
        )}
      </section>

      {/* 三、生涯路径 */}
      {results.career && (
        <section className="report-section">
          <h2>三、生涯路径</h2>
          <div className="info-block">
            {typeof results.career === "string" ? (
              <p>{results.career}</p>
            ) : (
              <>
                {results.career.shortTerm && (
                  <div style={{ marginBottom: 12 }}>
                    <strong>短期(0-3 年):</strong>
                    <p>{results.career.shortTerm}</p>
                  </div>
                )}
                {results.career.midTerm && (
                  <div style={{ marginBottom: 12 }}>
                    <strong>中期(3-7 年):</strong>
                    <p>{results.career.midTerm}</p>
                  </div>
                )}
                {results.career.longTerm && (
                  <div style={{ marginBottom: 12 }}>
                    <strong>长期(7+ 年):</strong>
                    <p>{results.career.longTerm}</p>
                  </div>
                )}
              </>
            )}
          </div>
        </section>
      )}

      {/* 四、潜在挑战 */}
      {results.challenges && (
        <section className="report-section">
          <h2>四、潜在挑战与建议</h2>
          <div className="info-block">
            {Array.isArray(results.challenges) ? (
              <ul>
                {results.challenges.map((c: any, i: number) => (
                  <li key={i}>{typeof c === "string" ? c : c.description || c.text || JSON.stringify(c)}</li>
                ))}
              </ul>
            ) : (
              <p>{JSON.stringify(results.challenges)}</p>
            )}
          </div>
        </section>
      )}

      <div className="step-actions">
        <button onClick={goPrev} className="btn-secondary">← 上一步</button>
        <button onClick={handlePrint} className="btn-primary">🖨️ 打印 / 保存 PDF</button>
        <button onClick={handleDownload} className="btn-primary">💾 下载 HTML</button>
      </div>
    </div>
  );
}

function ZiweiCard({ title, gong }: { title: string; gong: any }) {
  return (
    <div className="gong-card">
      <div className="gong-title">
        {title}:<span className="tag tag-primary">{gong.star}</span>
      </div>
      <div><strong>特质:</strong>{gong.trait}</div>
      <div><strong>适配:</strong>{gong.fit}</div>
      {gong.hourEffect && <div className="hour-effect">⏰ {gong.hourEffect}</div>}
    </div>
  );
}