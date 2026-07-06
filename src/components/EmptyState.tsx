import type { Scene, SceneId } from "../config/scenes";
import { SCENES } from "../config/scenes";

export interface EmptyStateProps {
  scene: Scene;
  onPick: (t: string) => void;
  onSceneChange: (id: SceneId) => void;
}

export default function EmptyState({
  scene,
  onPick,
  onSceneChange,
}: EmptyStateProps) {
  // 当前场景卡片：先渲染在最前
  const orderedScenes: Scene[] = [
    scene,
    ...SCENES.filter((s) => s.id !== scene.id),
  ];

  return (
    <div className="flex-1 flex flex-col justify-center min-h-0">
      {/* ========== 品牌头部 ========== */}
      <div className="empty-hero">
        <div className="hero-logo">IFF</div>
        <div className="hero-title">{scene.greeting}</div>
        <div className="hero-sub">{scene.intro}</div>
        <div className="hero-stats">
          <span><span className="num">17.6万</span> 真实案例</span>
          <span style={{ color: "#cbd5e1" }}>·</span>
          <span><span className="num">24h</span> 持续更新</span>
          <span style={{ color: "#cbd5e1" }}>·</span>
          <span><span className="num">3维</span> 评分模型</span>
        </div>
      </div>

      {/* ========== 选校原理说明 ========== */}
      {scene.id === "school" && (
        <div className="mx-auto max-w-3xl w-full mb-5 bg-gradient-to-br from-indigo-50/80 to-purple-50/60 border border-indigo-100 rounded-xl px-4 py-3 text-[13px] text-slate-700 leading-relaxed">
          <div className="flex items-center gap-1.5 mb-1.5">
            <span className="text-base">🎯</span>
            <span className="font-semibold text-indigo-800">推荐原理</span>
          </div>
          <ul className="space-y-0.5 list-disc list-inside marker:text-indigo-400">
            <li>基于 <strong>17 万+ 真实录取案例</strong> 的相似背景匹配，不靠 AI 猜</li>
            <li>按 <strong>GPA 容差 + 学校层次 + 专业方向</strong> 三层过滤</li>
            <li>综合 <strong>GPA · 排名 · 案例数</strong> 三维分析，分 <strong>冲刺 / 匹配 / 安全</strong> 三档</li>
          </ul>
        </div>
      )}

      {/* ========== 场景卡片宫格 ========== */}
      <div className="mx-auto max-w-3xl w-full grid grid-cols-1 sm:grid-cols-3 gap-3">
        {orderedScenes.map((s) => {
          const isCurrent = s.id === scene.id;
          return (
            <div
              key={s.id}
              className={`scene-card ${isCurrent ? "ring-1 ring-indigo-200 border-indigo-200" : ""}`}
            >
              <div className="sc-icon">{s.icon}</div>
              <div className="sc-label">
                {s.label}
                {isCurrent && (
                  <span
                    className="ml-1.5 inline-block align-middle text-[10px] font-medium px-1.5 py-0.5 rounded-full"
                    style={{
                      background: "rgba(99,102,241,0.10)",
                      color: "#4f46e5",
                      letterSpacing: "0.04em",
                    }}
                  >
                    当前
                  </span>
                )}
              </div>
              <div className="sc-hint">
                {s.id === "school" && "选校定位 · GPA 匹配"}
                {s.id === "essay" && "PS / CV / 推荐信"}
                {s.id === "visa" && "F-1 / Tier 4 / 材料"}
              </div>
              {!isCurrent && (
                <button
                  onClick={() => onSceneChange(s.id)}
                  className="sc-arrow"
                  aria-label={`切换到${s.label}`}
                  title="切换场景"
                >
                  →
                </button>
              )}

              {/* 快捷问题 - 只在当前场景展开 */}
              {isCurrent && (
                <div className="sc-prompts">
                  {s.quickPrompts.map((p) => (
                    <button
                      key={p.text}
                      onClick={() => onPick(p.text)}
                      className="sc-prompt"
                    >
                      <span className="pi">{p.icon}</span>
                      <span className="flex-1 line-clamp-2">{p.text}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>

      <p className="text-[11px] text-slate-400 text-center mt-4">
        点击快捷问题会填到输入框，可修改后再发送
      </p>
    </div>
  );
}