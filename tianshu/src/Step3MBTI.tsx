/**
 * Step3MBTI - MBTI 人格类型（sub-3.4）
 *
 * 迁移自 legacy/app.js 的 renderStep3() + renderMbtiKnown()
 *
 * 双模式：
 * - known：选择已知类型（带 A/T 倾向），实时显示该类型信息
 * - test：做 MBTI 测试（12 道题），提交后计算类型
 */

import { useState } from "react";
import { useTianshu } from "./TianshuContext";
import { TianShuData } from "./types";

type Mode = "known" | "test";

export default function Step3MBTI() {
  const { state, goNext, goPrev, setState } = useTianshu();
  const [mode, setMode] = useState<Mode>((state as any)._mbtiMode || "known");

  function switchMode(newMode: Mode) {
    setMode(newMode);
    setState({ _mbtiMode: newMode } as any);
  }

  return (
    <div className="step-card-placeholder">
      <div className="step-header">
        <span className="step-num">3/5</span>
        <h2>🧠 MBTI 人格类型</h2>
      </div>

      <div className="mode-tabs">
        <button
          className={`mode-tab ${mode === "known" ? "active" : ""}`}
          onClick={() => switchMode("known")}
        >
          ✅ 我知道我的类型
        </button>
        <button
          className={`mode-tab ${mode === "test" ? "active" : ""}`}
          onClick={() => switchMode("test")}
        >
          📝 做 MBTI 测试
        </button>
      </div>

      <div className="mbti-body">
        {mode === "known" ? <MbtiKnown /> : <MbtiTest />}
      </div>

      <div className="step-actions">
        <button onClick={goPrev} className="btn-secondary">← 上一步</button>
        <button onClick={goNext} className="btn-primary">下一步 →</button>
      </div>
    </div>
  );
}

function MbtiKnown() {
  const { state, setState } = useTianshu();
  const MBTI_TYPES = Object.keys((window as any).TianShuData.MBTI_DATA);
  const currentBase = state.mbtiType.split("-")[0];

  const [base, setBase] = useState(currentBase);
  const [at, setAt] = useState(state.mbtiType.split("-")[1] || "");

  function handleBaseChange(newBase: string) {
    setBase(newBase);
    const type = at ? `${newBase}-${at}` : newBase;
    setState({ mbtiType: type });
  }

  function handleAtChange(newAt: string) {
    setAt(newAt);
    const type = newAt ? `${base}-${newAt}` : base;
    setState({ mbtiType: type });
  }

  const type = at ? `${base}-${at}` : base;
  const info = (window as any).TianShuData.getMbtiInfo(type);

  return (
    <>
      <p className="hint">如果你测过 MBTI,选择对应类型并指定 A/T 倾向。如果没有,可以选一个大致接近的:</p>
      <div className="form-grid">
        <label className="form-field">
          <span className="form-label">MBTI 类型</span>
          <select className="form-input" value={base} onChange={(e) => handleBaseChange(e.target.value)}>
            {MBTI_TYPES.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </label>
        <label className="form-field">
          <span className="form-label">A / T 倾向</span>
          <select className="form-input" value={at} onChange={(e) => handleAtChange(e.target.value)}>
            <option value="">不指定</option>
            <option value="A">A (Assertive 自信型)</option>
            <option value="T">T (Turbulent 动荡型)</option>
          </select>
        </label>
      </div>
      {info && <MbtiPreviewCard info={info} />}
    </>
  );
}

function MbtiPreviewCard({ info }: { info: any }) {
  return (
    <div className="mbti-card">
      <div className="mbti-title">{info.fullType} · {info.nick}</div>
      <div><strong>核心:</strong>{info.core}</div>
      <div><strong>认知:</strong>{info.cog}</div>
      <div><strong>行为:</strong>{info.beh}</div>
      <div><strong>优势:</strong>{info.strength}</div>
      <div><strong>短板:</strong><span style={{ color: "#c53030" }}>{info.weakness}</span></div>
      <div><strong>适配专业:</strong>{info.fitMajors}</div>
    </div>
  );
}

function MbtiTest() {
  const { state, setState } = useTianshu();
  const QUESTIONS = (window as any).TianShuData.MBTI_QUESTIONS;
  const [answers, setAnswers] = useState<number[]>(state._mbtiAnswers || []);
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
    const full = answers.map((s, i) => ({ qIdx: i, score: s }));
    const r = (window as any).TianShuData.calcMbtiFromTest(full);
    setResult(r);
    setState({ mbtiType: r.type, _mbtiAnswers: answers });
  }

  function pct(dim: string, scores: any) {
    const opp: any = { E: "I", I: "E", S: "N", N: "S", T: "F", F: "T", J: "P", P: "J" };
    const total = scores[dim] + scores[opp[dim]];
    return total > 0 ? Math.round((scores[dim] / total) * 100) : 50;
  }

  return (
    <>
      <p className="hint">每题选择更接近你的选项,完成后点击下方按钮计算类型:</p>
      <div className="test-questions">
        {QUESTIONS.map((q: any, i: number) => (
          <div key={i} className="test-q">
            <div className="test-q-num">第 {i + 1} 题</div>
            <div className="test-q-stem">{q.stem}</div>
            <label className={`test-q-opt ${answers[i] === 1 ? "selected" : ""}`}>
              <input
                type="radio"
                name={`mbti-q${i}`}
                value="1"
                checked={answers[i] === 1}
                onChange={() => setAnswer(i, 1)}
              />
              {q.optionA}
            </label>
            <label className={`test-q-opt ${answers[i] === 2 ? "selected" : ""}`}>
              <input
                type="radio"
                name={`mbti-q${i}`}
                value="2"
                checked={answers[i] === 2}
                onChange={() => setAnswer(i, 2)}
              />
              {q.optionB}
            </label>
          </div>
        ))}
      </div>
      <button
        onClick={calculate}
        className="btn-primary"
        style={{ marginTop: 16, width: "100%", justifyContent: "center" }}
      >
        🧮 计算我的 MBTI 类型
      </button>
      {result && (
        <div className="mbti-card" style={{ border: "2px solid #4f7cff", marginTop: 16 }}>
          <div className="mbti-title">🎉 你的 MBTI 类型: {result.info?.fullType || result.type} · {result.info?.nick}</div>
          <div className="test-dim-bars">
            {["E", "S", "T", "J"].map((dim) => (
              <div key={dim} className="dim-bar">
                <span>{dim} {result.scores[dim]}</span>
                <div className="bar-track">
                  <div className="bar-fill" style={{ width: `${pct(dim, result.scores)}%` }} />
                </div>
                <span>{result.scores[dim === "E" ? "I" : dim === "S" ? "N" : dim === "T" ? "F" : "P"]} {dim === "E" ? "I" : dim === "S" ? "N" : dim === "T" ? "F" : "P"}</span>
              </div>
            ))}
          </div>
          {result.info && (
            <>
              <div style={{ marginTop: 12 }}><strong>核心:</strong>{result.info.core}</div>
              <div><strong>优势:</strong>{result.info.strength}</div>
              <div><strong>短板:</strong><span style={{ color: "#c53030" }}>{result.info.weakness}</span></div>
            </>
          )}
        </div>
      )}
    </>
  );
}