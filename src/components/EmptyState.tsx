import type { Scene } from "../config/scenes";

export interface EmptyStateProps {
  scene: Scene;
  onPick: (t: string) => void;
  onSceneChange: (id: Scene["id"]) => void;
}

export default function EmptyState({
  scene,
  onPick,
}: EmptyStateProps) {
  return (
    <div className="min-h-full flex flex-col justify-center py-6">
      {/* ========== 品牌头部 ========== */}
      <div className="empty-hero">
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

      {/* ========== 当前场景单卡 ========== */}
      <div className="mx-auto max-w-2xl w-full">
        <div className="scene-card ring-1 ring-indigo-200 border-indigo-200">
          <div className="sc-icon">{scene.icon}</div>
          <div className="sc-label">
            {scene.label}
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
          </div>
          <div className="sc-hint">
            {scene.id === "essay" && "PS / CV / 推荐信"}
            {scene.id === "visa" && "F-1 / Tier 4 / 材料清单"}
          </div>
          <div className="sc-prompts">
            {scene.quickPrompts.map((p) => (
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
        </div>
      </div>

      <p className="text-[11px] text-slate-400 text-center mt-4">
        点击快捷问题会填到输入框，可修改后再发送 · 切换场景用顶部 Tab
      </p>
    </div>
  );
}