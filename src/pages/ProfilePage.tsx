import { useState, useEffect } from "react";
import type { HistoryItem, ProfileData } from "../services/profile";
import {
  loadProfile,
  saveProfile,
  loadHistory,
  deleteHistoryItem,
  clearHistory,
} from "../services/profile";
import type { RecommendResult, MBTIMajorResult, ChatMessage } from "../types";

/* =====================================================================
 * 我的档案 — 个人信息 + 天枢测评结果 + 查询历史
 * ===================================================================== */

const COUNTRIES = ["英国", "美国", "澳洲", "加拿大", "香港", "新加坡", "欧洲", "日本", "韩国"];
const STUDY_LEVELS = ["本科", "硕士", "博士", "预科"];
const GPA_FORMATS = ["100分制", "4分制", "5分制"];

const TYPE_ICONS: Record<string, string> = {
  recommend: "📌",
  mbti: "🧠",
  chat_session: "💬",
  tianshu_report: "🧭",
};

export default function ProfilePage() {
  const [profile, setProfile] = useState<ProfileData>({ updated_at: "" });
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    setProfile(loadProfile() || { updated_at: "" });
    setHistory(loadHistory());
  }, []);

  const handleSave = () => {
    saveProfile(profile);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const handleField = (key: keyof ProfileData, value: any) => {
    setProfile((prev) => ({ ...prev, [key]: value }));
  };

  const handleCountry = (c: string) => {
    const current = profile.target_countries || [];
    const next = current.includes(c)
      ? current.filter((x) => x !== c)
      : [...current, c];
    handleField("target_countries", next);
  };

  const handleDelete = (id: string) => {
    deleteHistoryItem(id);
    setHistory(loadHistory());
  };

  const handleClearAll = () => {
    if (!window.confirm("确定清空所有查询历史？此操作不可恢复。")) return;
    clearHistory();
    setHistory([]);
  };

  const tianshu = profile.tianshu;
  const hasHistory = history.length > 0;
  const historyCounts = {
    recommend: history.filter((h) => h.type === "recommend").length,
    mbti: history.filter((h) => h.type === "mbti").length,
    chat: history.filter((h) => h.type === "chat_session").length,
    tianshu: history.filter((h) => h.type === "tianshu_report").length,
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-3xl mx-auto px-4 py-6 sm:py-8">

        {/* ======== 头部 ======== */}
        <header className="flex items-center gap-3 mb-6">
          <a
            href="./"
            className="inline-flex items-center gap-1 text-sm text-slate-400 hover:text-indigo-600 transition-colors"
          >
            ← 返回
          </a>
          <span className="w-px h-4 bg-slate-200" />
          <h1 className="text-xl font-bold text-slate-900">📁 我的档案</h1>
        </header>

        {/* ======== ① 基本信息 ======== */}
        <section className="bg-white rounded-xl shadow-sm border border-slate-200 p-5 sm:p-6 mb-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-semibold text-slate-800">✏️ 基本信息</h2>
            <button
              onClick={handleSave}
              className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-all ${
                saved
                  ? "bg-green-100 text-green-700"
                  : "bg-indigo-600 text-white hover:bg-indigo-700"
              }`}
            >
              {saved ? "✓ 已保存" : "💾 保存"}
            </button>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-5 gap-y-3.5">
            {/* 本科学校 */}
            <label className="flex flex-col text-sm text-slate-600">
              本科学校
              <input
                value={profile.school || ""}
                onChange={(e) => handleField("school", e.target.value)}
                placeholder="例如 北京邮电大学"
                className="mt-1 px-3 py-2 border border-slate-200 rounded-lg text-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400"
              />
            </label>
            {/* 本科专业 */}
            <label className="flex flex-col text-sm text-slate-600">
              本科专业
              <input
                value={profile.original_major || ""}
                onChange={(e) => handleField("original_major", e.target.value)}
                placeholder="例如 通信工程"
                className="mt-1 px-3 py-2 border border-slate-200 rounded-lg text-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400"
              />
            </label>
            {/* GPA */}
            <label className="flex flex-col text-sm text-slate-600">
              GPA 分数
              <input
                type="number"
                step="0.01"
                value={profile.gpa_score ?? ""}
                onChange={(e) => handleField("gpa_score", e.target.value ? parseFloat(e.target.value) : null)}
                placeholder="例如 82"
                className="mt-1 px-3 py-2 border border-slate-200 rounded-lg text-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400"
              />
            </label>
            {/* GPA 格式 */}
            <label className="flex flex-col text-sm text-slate-600">
              GPA 格式
              <select
                value={profile.gpa_format || ""}
                onChange={(e) => handleField("gpa_format", e.target.value)}
                className="mt-1 px-3 py-2 border border-slate-200 rounded-lg text-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400 bg-white"
              >
                <option value="">选择</option>
                {GPA_FORMATS.map((f) => (
                  <option key={f} value={f}>{f}</option>
                ))}
              </select>
            </label>
            {/* 学位阶段 */}
            <label className="flex flex-col text-sm text-slate-600">
              学位阶段
              <select
                value={profile.study_level || ""}
                onChange={(e) => handleField("study_level", e.target.value)}
                className="mt-1 px-3 py-2 border border-slate-200 rounded-lg text-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400 bg-white"
              >
                <option value="">选择</option>
                {STUDY_LEVELS.map((l) => (
                  <option key={l} value={l}>{l}</option>
                ))}
              </select>
            </label>
            {/* 目标专业 */}
            <label className="flex flex-col text-sm text-slate-600">
              目标专业
              <input
                value={profile.target_major || ""}
                onChange={(e) => handleField("target_major", e.target.value)}
                placeholder="例如 计算机 / 金融"
                className="mt-1 px-3 py-2 border border-slate-200 rounded-lg text-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400"
              />
            </label>
            {/* 目标国家 */}
            <div className="flex flex-col text-sm text-slate-600 sm:col-span-2">
              <span className="mb-1.5">目标国家/地区</span>
              <div className="flex flex-wrap gap-1.5">
                {COUNTRIES.map((c) => {
                  const active = (profile.target_countries || []).includes(c);
                  return (
                    <button
                      key={c}
                      onClick={() => handleCountry(c)}
                      className={`px-3 py-1 rounded-lg text-xs font-medium transition-all ${
                        active
                          ? "bg-indigo-100 text-indigo-700 border border-indigo-200"
                          : "bg-slate-50 text-slate-500 border border-slate-200 hover:border-indigo-200 hover:text-indigo-600"
                      }`}
                    >
                      {c}
                    </button>
                  );
                })}
              </div>
            </div>
            {/* 语言成绩 */}
            <label className="flex flex-col text-sm text-slate-600">
              IELTS 成绩
              <input
                type="number"
                step="0.5"
                value={profile.ielts ?? ""}
                onChange={(e) => handleField("ielts", e.target.value ? parseFloat(e.target.value) : null)}
                placeholder="例如 7.0"
                className="mt-1 px-3 py-2 border border-slate-200 rounded-lg text-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400"
              />
            </label>
            <label className="flex flex-col text-sm text-slate-600">
              TOEFL 成绩
              <input
                type="number"
                value={profile.toefl ?? ""}
                onChange={(e) => handleField("toefl", e.target.value ? parseInt(e.target.value) : null)}
                placeholder="例如 100"
                className="mt-1 px-3 py-2 border border-slate-200 rounded-lg text-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400"
              />
            </label>
          </div>
        </section>

        {/* ======== ② 天枢测评结果（只读） ======== */}
        {tianshu && (
          <section className="bg-white rounded-xl shadow-sm border border-slate-200 p-5 sm:p-6 mb-5">
            <h2 className="text-base font-semibold text-slate-800 mb-4">🧭 天枢 · 综合测评结果</h2>
            <div className="space-y-4">
              {/* 基本信息 */}
              {tianshu.student && (
                <div className="flex flex-wrap gap-x-6 gap-y-1 text-sm text-slate-600 bg-slate-50 rounded-lg px-4 py-3">
                  <span>👤 {tianshu.student.name || "匿名"}</span>
                  <span>{tianshu.student.gender}</span>
                  <span>📅 {tianshu.student.birthYear}-{String(tianshu.student.birthMonth).padStart(2,'0')}-{String(tianshu.student.birthDay).padStart(2,'0')}</span>
                  <span>🎓 {tianshu.student.grade || ""}</span>
                </div>
              )}

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* MBTI */}
                {tianshu.mbti && (
                  <div className="border border-indigo-100 rounded-xl p-4 bg-indigo-50/30">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-lg">🧠</span>
                      <span className="font-semibold text-slate-800">MBTI</span>
                      <span className="text-sm font-bold text-indigo-600 ml-auto">{tianshu.mbti.type}</span>
                    </div>
                    <p className="text-sm text-slate-600">{tianshu.mbti.core || tianshu.mbti.nick}</p>
                    {tianshu.mbti.strength && (
                      <p className="text-xs text-green-600 mt-1">✓ {tianshu.mbti.strength}</p>
                    )}
                    {tianshu.mbti.fitMajors && (
                      <p className="text-xs text-slate-500 mt-1">🎯 {tianshu.mbti.fitMajors}</p>
                    )}
                  </div>
                )}

                {/* 霍兰德 */}
                {tianshu.holland && (
                  <div className="border border-amber-100 rounded-xl p-4 bg-amber-50/30">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-lg">🎯</span>
                      <span className="font-semibold text-slate-800">霍兰德</span>
                      <span className="text-sm font-bold text-amber-600 ml-auto">{tianshu.holland.top3}</span>
                    </div>
                    <p className="text-sm text-slate-600">{tianshu.holland.codeExplain}</p>
                    <div className="flex flex-wrap gap-1 mt-2">
                      {(tianshu.holland.sorted || []).slice(0, 3).map(([code, score]) => (
                        <span key={code} className="text-xs px-2 py-0.5 bg-amber-100 text-amber-700 rounded-full">
                          {code} {score}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* 八字 */}
                {tianshu.bazi && (
                  <div className="border border-emerald-100 rounded-xl p-4 bg-emerald-50/30">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-lg">🔮</span>
                      <span className="font-semibold text-slate-800">八字</span>
                    </div>
                    <div className="text-sm text-slate-600 space-y-0.5">
                      <p>四柱: {(tianshu.bazi as any).yearZhu || ""} · {(tianshu.bazi as any).monthZhu || ""} · {(tianshu.bazi as any).dayZhu || ""} · {(tianshu.bazi as any).hourZhu || ""}</p>
                      <p>日主: {(tianshu.bazi as any).dayMaster || ""}（{(tianshu.bazi as any).dayMasterWx || ""}）</p>
                      <p>喜用: {((tianshu.bazi as any).xiZhong || []).join(" + ")}</p>
                    </div>
                  </div>
                )}

                {/* 星座 */}
                {tianshu.sunSign && (
                  <div className="border border-purple-100 rounded-xl p-4 bg-purple-50/30">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-lg">📅</span>
                      <span className="font-semibold text-slate-800">星座</span>
                      <span className="text-sm font-bold text-purple-600 ml-auto">{tianshu.sunSign}</span>
                    </div>
                  </div>
                )}
              </div>

              {/* 综合报告摘要 */}
              {tianshu.summary && (
                <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-xl p-4 text-sm text-slate-700">
                  <div className="flex gap-2 mb-2 flex-wrap">
                    {(tianshu.summary.tags || []).map((t: string, i: number) => (
                      <span key={i} className="text-xs px-2 py-0.5 bg-indigo-100 text-indigo-700 rounded-full">{t}</span>
                    ))}
                  </div>
                  <p>{tianshu.summary.summary}</p>
                </div>
              )}
            </div>
            <p className="text-xs text-slate-400 mt-3">数据来自天枢测评，在天枢中重新测评后可更新</p>
          </section>
        )}

        {/* ======== ③ 查询历史 ======== */}
        <section className="bg-white rounded-xl shadow-sm border border-slate-200 p-5 sm:p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-semibold text-slate-800">📋 查询历史</h2>
            <div className="flex items-center gap-3">
              <span className="text-xs text-slate-400">
                {historyCounts.recommend} 推荐 · {historyCounts.mbti} MBTI · {historyCounts.chat} 对话 · {historyCounts.tianshu} 天枢
              </span>
              {hasHistory && (
                <button
                  onClick={handleClearAll}
                  className="text-xs text-red-500 hover:text-red-700 hover:underline"
                >
                  清空
                </button>
              )}
            </div>
          </div>

          {!hasHistory ? (
            <div className="text-center py-10 text-slate-400">
              <p className="text-3xl mb-2">📭</p>
              <p className="text-sm">暂无查询记录</p>
              <p className="text-xs mt-1">使用天权（选校推荐 / MBTI / AI 对话）或天枢测评后，记录会自动出现在这里</p>
            </div>
          ) : (
            <div className="space-y-2">
              {history.map((item) => (
                <HistoryRow key={item.id} item={item} onDelete={handleDelete} />
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}

/* =====================================================================
 * 历史记录行
 * ===================================================================== */

function HistoryRow({
  item,
  onDelete,
}: {
  item: HistoryItem;
  onDelete: (id: string) => void;
}) {
  const icon = TYPE_ICONS[item.type] || "📄";
  const date = formatDate(item.created_at);

  return (
    <div className="flex items-start gap-3 p-3 rounded-xl hover:bg-slate-50 transition-colors group">
      <span className="text-xl mt-0.5 shrink-0">{icon}</span>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-slate-700 truncate">
            {typeLabel(item.type, item.system)}
          </span>
          <span className="text-xs text-slate-400 shrink-0">{date}</span>
        </div>
        <p className="text-sm text-slate-600 truncate">{item.summary}</p>
        {item.subtitle && (
          <p className="text-xs text-slate-400 truncate">{item.subtitle}</p>
        )}
      </div>
      <div className="flex items-center gap-1 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
        <button
          onClick={() => viewDetail(item)}
          className="text-xs px-2 py-1 rounded text-indigo-600 hover:bg-indigo-50"
        >
          查看
        </button>
        <button
          onClick={() => onDelete(item.id)}
          className="text-xs px-2 py-1 rounded text-red-500 hover:bg-red-50"
        >
          删除
        </button>
      </div>
    </div>
  );
}

/* =====================================================================
 * 工具函数
 * ===================================================================== */

function typeLabel(type: string, system: string): string {
  if (type === "recommend") return "📌 选校推荐";
  if (type === "mbti") return "🧠 MBTI 测评";
  if (type === "chat_session") return "💬 AI 对话";
  if (type === "tianshu_report") return system === "tianshu" ? "🧭 天枢测评" : "📄 测评报告";
  return "📄 记录";
}

export function formatDate(iso: string): string {
  try {
    const d = new Date(iso);
    const month = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    const hour = String(d.getHours()).padStart(2, "0");
    const min = String(d.getMinutes()).padStart(2, "0");
    return `${month}/${day} ${hour}:${min}`;
  } catch {
    return iso;
  }
}

function viewDetail(item: HistoryItem) {
  const data = item.data as Record<string, unknown>;

  if (item.type === "recommend") {
    const r = data as unknown as RecommendResult;
    const lines = [
      `背景: ${r.background?.school_tier_label || "?"} · GPA ${r.background?.gpa4 || "?"}`,
      `匹配: ${r.match_summary?.total_cases || 0} 例 · ${r.match_summary?.total_schools || 0} 所学校`,
      "",
    ];
    for (const c of r.by_country || []) {
      lines.push(`【${c.country}】${c.matched_schools} 校 · ${c.matched_cases} 例`);
      for (const s of (c.schools || []).slice(0, 5)) {
        const chance = s.admission_chance || "";
        const gpa = s.p50_reference ? `p50=${s.p50_reference}` : "";
        lines.push(`  ${chance === "安全" ? "✅" : chance === "主申" ? "📌" : chance === "冲刺" ? "⚡" : chance === "彩票" ? "🎲" : "•"} ${s.name} ${gpa}`);
      }
      if ((c.schools || []).length > 5) {
        lines.push(`  ...还有 ${c.schools.length - 5} 所`);
      }
    }
    window.alert(lines.join("\n"));
  } else if (item.type === "mbti") {
    const m = data.result as MBTIMajorResult || data as unknown as MBTIMajorResult;
    window.alert(
      `🧠 ${m.type} · ${m.name}\n\n` +
      `✅ 推荐: ${(m.top_majors || []).join("、")}\n` +
      `⚠️ 慎重: ${(m.avoid_majors || []).join("、")}\n\n` +
      `💼 职业: ${m.career_path || ""}\n` +
      `💡 建议: ${m.study_tips || ""}`
    );
  } else if (item.type === "chat_session") {
    const msgs = (data.messages || []) as ChatMessage[];
    const sceneLabels: Record<string, string> = { school: "选校", essay: "文书", visa: "签证" };
    const sceneLabel = sceneLabels[data.scene as string] || data.scene as string;
    const text = msgs.map((m) =>
      `${m.role === "user" ? "🧑" : "🤖"}: ${m.content.slice(0, 120)}`
    ).join("\n\n");
    window.alert(`💬 ${sceneLabel} · ${msgs.length} 轮\n\n${text}`);
  } else if (item.type === "tianshu_report") {
    window.alert("🧭 天枢综合测评报告\n\n完整报告请在天枢中查看。\n测评结果已保存在档案的「天枢测评结果」区块。");
  }
}
