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
  return (
    <div className="flex-1 flex flex-col justify-center">
      {/* Hero */}
      <div className="text-center mb-6 sm:mb-8">
        <div className="inline-flex items-center justify-center w-16 h-16 sm:w-20 sm:h-20 rounded-2xl bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 text-white text-2xl sm:text-3xl font-bold shadow-lg shadow-indigo-200 mb-4">
          {scene.icon}
        </div>
        <h2 className="text-xl sm:text-2xl font-bold text-slate-900 mb-2">
          {scene.greeting}
        </h2>
        <p className="text-slate-500 text-sm sm:text-base max-w-md mx-auto leading-relaxed">
          {scene.intro}
        </p>
      </div>

      {/* 使用说明 */}
      {scene.id === "school" && (
        <div className="mx-auto max-w-xl w-full mb-5 bg-indigo-50/70 border border-indigo-100 rounded-xl px-4 py-3 text-sm text-slate-700 leading-relaxed">
          <div className="font-semibold text-indigo-800 mb-1">🎯 推荐原理</div>
          <ul className="space-y-1 list-disc list-inside marker:text-indigo-400">
            <li><strong>基于 17 万+ 真实录取案例</strong>的相似背景匹配引擎，不靠 AI 猜</li>
            <li>按 <strong>GPA容差 + 学校层次 + 专业方向</strong> 三层过滤，找到和你最像的往届申请者</li>
            <li>综合 <strong>GPA 匹配 · 学校排名 · 案例数量</strong> 三维评分，分 <strong>冲刺 / 匹配 / 安全</strong> 三档</li>
            <li>每所学校都显示匹配案例数和录取 GPA 中位数，数据透明可验证</li>
          </ul>
          <p className="mt-2 text-indigo-600/80 text-xs">告诉我你的 GPA、学校、专业和目标国家即可开始。也可以直接点击下方快捷问题 👇</p>
        </div>
      )}

      {/* 场景入口提示 */}
      <div className="text-center mb-5">
        <div className="inline-flex flex-wrap items-center justify-center gap-1 text-xs text-slate-400">
          <span>也可以聊聊</span>
          {SCENES.filter((s) => s.id !== scene.id).map((s, i, arr) => (
            <span key={s.id}>
              <button
                onClick={() => onSceneChange(s.id)}
                className="text-indigo-600 hover:underline font-medium"
              >
                {s.label}
              </button>
              {i < arr.length - 1 && <span className="mx-0.5">·</span>}
            </span>
          ))}
        </div>
      </div>

      {/* 快捷问题 —— 点击填到输入框（不直接发送），让用户自己修改后再发 */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-xl mx-auto w-full">
        {scene.quickPrompts.map((p) => (
          <button
            key={p.text}
            onClick={() => onPick(p.text)}
            className="lift text-left px-4 py-3 bg-white border border-slate-200 rounded-xl text-sm text-slate-700 flex items-start gap-2 group"
          >
            <span className="text-lg shrink-0">{p.icon}</span>
            <span className="leading-relaxed flex-1">{p.text}</span>
            <span className="text-xs text-slate-400 group-hover:text-indigo-500 transition-colors shrink-0 mt-0.5">
              →
            </span>
          </button>
        ))}
      </div>
      <p className="text-[11px] text-slate-400 text-center mt-3 max-w-xl mx-auto">
        点击上方问题会填到输入框，可修改后再发送
      </p>
    </div>
  );
}
