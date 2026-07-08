/**
 * Step4Holland - 霍兰德职业兴趣（sub-3.5）
 *
 * 迁移自 legacy/app.js 的 renderStep4() + renderHollandKnown() + renderHollandTest()
 *
 * 双模式：
 * - known：6 维滑块（RIASEC），实时显示代码解释
 * - test：6 维题目（每维多题），提交后计算分数
 */

import { useState } from "react";
import { useTianshu } from "./TianshuContext";
import type { HollandScores } from "./types";

const CODES = ["R", "I", "A", "S", "E", "C"] as const;
type Mode = "known" | "test";

export default function Step4Holland() {
  const { state, goNext, goPrev, setState } = useTianshu();
  const [mode, setMode] = useState<Mode>((state as any)._hollandMode || "known");

  function switchMode(newMode: Mode) {
    setMode(newMode);
    setState({ _hollandMode: newMode } as any);
  }

  return (
    <div className="step-card-placeholder">
      <div className="step-header">
        <span className="step-num">4/5</span>
        <h2>🎯 霍兰德职业兴趣</h2>
      </div>

      <div className="mode-tabs">
        <button
          className={`mode-tab ${mode === "known" ? "active" : ""}`}
          onClick={() => switchMode("known")}
        >
          ✅ 我知道我的分数
        </button>
        <button
          className={`mode-tab ${mode === "test" ? "active" : ""}`}
          onClick={() => switchMode("test")}
        >
          📝 做霍兰德测试
        </button>
      </div>

      <div className="holland-body">
        {mode === "known" ? <HollandKnown /> : <HollandTest />}
      </div>

      <div className="step-actions">
        <button onClick={goPrev} className="btn-secondary">← 上一步</button>
        <button onClick={goNext} className="btn-primary">下一步 →</button>
      </div>
    </div>
  );
}

function HollandKnown() {
  const { state, setState } = useTianshu();
  const [scores, setScores] = useState<HollandScores>(state.hollandScores);

  function updateScore(code: keyof HollandScores, val: number) {
    const next = { ...scores, [code]: val };
    setScores(next);
    setState({ hollandScores: next });
  }

  function reset() {
    const def: HollandScores = { R: 30, I: 85, A: 70, S: 65, E: 40, C: 35 };
    setScores(def);
    setState({ hollandScores: def });
  }

  const info = (window as any).TianShuData.getHollandInfo(scores);

  return (
    <>
      <p className="hint">调整每个维度的得分(0-100),不知道就保留默认。</p>
      <div className="sliders">
        {CODES.map((code) => (
          <div key={code} className="slider-row">
            <label className="slider-label">
              <strong>{code}</strong> · {(window as any).TianShuData.HOLLAND_DIMS[code].name}
              <span className="slider-value">{scores[code]}</span>
            </label>
            <input
              type="range"
              min={0}
              max={100}
              value={scores[code]}
              onChange={(e) => updateScore(code, parseInt(e.target.value))}
            />
          </div>
        ))}
      </div>
      <button onClick={reset} className="btn-text">↺ 重置为示例默认值</button>
      {info && <HollandPreviewCard info={info} scores={scores} />}
    </>
  );
}

function HollandPreviewCard({ info, scores }: { info: any; scores: HollandScores }) {
  return (
    <div className="holland-card">
      <div className="holland-title">
        🎯 你的霍兰德代码: <span className="tag tag-primary">{info.top3}</span>
      </div>
      <div>{info.codeExplain}</div>
      <div className="holland-fits">
        <strong>主适配方向:</strong>
        <ul>
          {info.mainFit?.map((f: string, i: number) => <li key={i}>{f}</li>)}
        </ul>
      </div>
      {info.riskWarning && info.riskWarning !== "无明显短板维度" && (
        <div className="risk-warning">⚠️ {info.riskWarning}</div>
      )}
      <div style={{ marginTop: 12 }}>
        <strong>各维度得分:</strong>
        <div className="test-dim-bars">
          {CODES.map((code) => (
            <div key={code} className="dim-bar">
              <span>{code}</span>
              <div className="bar-track">
                <div className="bar-fill" style={{ width: `${scores[code]}%` }} />
              </div>
              <span>{scores[code]}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function HollandTest() {
  const { state, setState } = useTianshu();
  const QUESTIONS = (window as any).TianShuData.HOLLAND_QUESTIONS;
  const RATING_LABELS = ["非常不喜欢", "不喜欢", "一般", "喜欢", "非常喜欢"];
  const [answers, setAnswers] = useState<number[]>((state as any)._hollandAnswers || []);
  const [result, setResult] = useState<any>(null);

  function setAnswer(idx: number, score: number) {
    const next = [...answers];
    next[idx] = score;
    setAnswers(next);
  }

  function calculate() {
    const unanswered: number[] = [];
    for (let i = 0; i < QUESTIONS.length; i++) {
      if (!answers[i]) unanswered.push(i + 1);
    }
    if (unanswered.length > 0) {
      alert(`还有 ${unanswered.length} 题未作答(第 ${unanswered.join(", ")} 题),请完成所有题目`);
      return;
    }
    const full = QUESTIONS.map((q: any, i: number) => ({ dim: q.dim, score: answers[i] }));
    const scores = (window as any).TianShuData.calcHollandFromTest(full);
    const info = (window as any).TianShuData.getHollandInfo(scores);
    setResult({ scores, info });
    setState({ hollandScores: scores, _hollandAnswers: answers });
  }

  return (
    <>
      <p className="hint">评价每个活动的喜欢程度(1-5分),完成后计算你的霍兰德分数:</p>
      <div className="test-questions holland-test">
        {QUESTIONS.map((q: any, i: number) => (
          <div key={i} className="test-q test-q-holland">
            <div className="test-q-num">{i + 1}</div>
            <div className="test-q-text">{q.text}</div>
            <div className="test-q-rating">
              {RATING_LABELS.map((label, ri) => (
                <label key={ri} className={`rating-opt ${answers[i] === ri + 1 ? "selected" : ""}`}>
                  <input
                    type="radio"
                    name={`holland-q${i}`}
                    value={ri + 1}
                    checked={answers[i] === ri + 1}
                    onChange={() => setAnswer(i, ri + 1)}
                  />
                  <span className="rating-num">{ri + 1}</span>
                  <span className="rating-label">{label}</span>
                </label>
              ))}
            </div>
          </div>
        ))}
      </div>
      <button
        onClick={calculate}
        className="btn-primary"
        style={{ marginTop: 16, width: "100%", justifyContent: "center" }}
      >
        🧮 计算我的霍兰德分数
      </button>
      {result && <HollandPreviewCard info={result.info} scores={result.scores} />}
    </>
  );
}