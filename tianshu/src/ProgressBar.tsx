/**
 * ProgressBar - 5 步测评进度条
 *
 * 仿照旧 app.js 的 updateProgress() 函数。
 */

import { useTianshu } from "./TianshuContext";

const STEPS = [
  { num: 1, label: "基础信息", emoji: "📝" },
  { num: 2, label: "八字排盘", emoji: "🌙" },
  { num: 3, label: "MBTI 测评", emoji: "🧠" },
  { num: 4, label: "霍兰德测评", emoji: "🎯" },
  { num: 5, label: "综合报告", emoji: "📊" },
] as const;

export default function ProgressBar() {
  const { state, goTo } = useTianshu();
  return (
    <ol className="step-progress">
      {STEPS.map((s) => (
        <li
          key={s.num}
          className={`step-pill ${state.step === s.num ? "active" : ""} ${
            state.step > s.num ? "done" : ""
          }`}
          onClick={() => state.step >= s.num && goTo(s.num as any)}
        >
          <span className="step-emoji">{s.emoji}</span>
          <span className="step-label">
            {s.num}. {s.label}
          </span>
        </li>
      ))}
    </ol>
  );
}