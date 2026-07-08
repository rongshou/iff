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
    <div className="min-h-full flex flex-col justify-center py-4 sm:py-6">
      {/* ========== 当前场景单卡 ========== */}
      <div className="mx-auto max-w-xl w-full px-3 sm:px-0">
        <div className="scene-card">
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