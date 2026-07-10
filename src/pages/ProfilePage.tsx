import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import type { HistoryItem, ProfileData } from "../services/profile";
import {
  loadHistory,
  deleteHistoryItem,
  clearHistory,
} from "../services/profile";
import { logout } from "../services/auth";
import { viewDetail } from "../utils/profile-utils";
import HistoryRow from "../components/HistoryRow";
import { useProfileStore } from "../store/profileStore";

/* =====================================================================
 * 我的档案 — 个人信息 + 天枢测评结果 + 查询历史
 * ===================================================================== */

const COUNTRIES = ["英国", "美国", "澳洲", "加拿大", "香港", "新加坡", "欧洲", "日本", "韩国"];
const STUDY_LEVELS = ["高中", "本科", "硕士", "博士", "预科", "其他"];
const GPA_FORMATS = ["百分制", "4分制", "5分制", "7分制", "9分制", "英制百分制"];


export default function ProfilePage() {
  const profile = useProfileStore((s) => s.profile) as ProfileData | null;
  const loaded = useProfileStore((s) => s.loaded);
  const loadProfileFromStore = useProfileStore((s) => s.load);
  const update = useProfileStore((s) => s.update);
  const setProfileField = useProfileStore((s) => s.setProfileField);

  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [saved, setSaved] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    loadProfileFromStore();
    setHistory(loadHistory());
  }, []);

  /* profile 尚未加载完成时显示占位 */
  if (!loaded) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <p className="text-slate-400 text-sm">加载中…</p>
      </div>
    );
  }

  /* profile 为空时使用空对象兜底，避免 null.tianshu 崩溃 */
  const safeProfile = (profile ?? {
    username: "",
    email: "",
    auth_code: "",
    school: "",
    original_major: "",
    gpa_score: null,
    gpa_format: "",
    target_countries: [],
    study_level: "",
    target_major: "",
    ielts: null,
    toefl: null,
    gre: null,
    updated_at: "",
  }) as ProfileData;

  const handleSave = () => {
    update(safeProfile);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const handleField = (key: keyof ProfileData, value: unknown) => {
    setProfileField(key, value);
  };

  const handleCountry = (c: string) => {
    const current = safeProfile.target_countries || [];
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

  const tianshu = safeProfile.tianshu;
  const hasHistory = history.length > 0;
  const historyCounts = {
    mbti: history.filter((h) => h.type === "mbti").length,
    chat: history.filter((h) => h.type === "chat_session").length,
    tianshu: history.filter((h) => h.type === "tianshu_report").length,
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-3xl mx-auto px-4 py-6 sm:py-8">

        {/* ======== 头部 ======== */}
        <header className="flex items-center gap-3 mb-6">
          <div className="flex items-center gap-1">
            <Link
              to="/"
              className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium text-indigo-600 bg-indigo-50 border border-indigo-200 hover:bg-indigo-100 transition-all"
              title="首页"
            ><span>🏠</span>首页</Link>
          </div>
          <span className="w-px h-4 bg-slate-200" />
          <h1 className="text-xl font-bold text-slate-900 flex-1">📁 我的档案</h1>
          <button
            onClick={() => { logout(); navigate("/login", { replace: true }); }}
            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium text-slate-400 border border-slate-200 hover:text-red-600 hover:border-red-300 hover:bg-red-50 transition-all"
          >
            <span>🚪</span>退出
          </button>
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
            {/* 用户名 */}
            <label className="flex flex-col text-sm text-slate-600">
              用户名
              <input
                value={safeProfile.username || ""}
                onChange={(e) => handleField("username", e.target.value)}
                placeholder="你的昵称"
                className="mt-1 px-3 py-2 border border-slate-200 rounded-lg text-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400"
              />
            </label>
            {/* 邮箱 */}
            <label className="flex flex-col text-sm text-slate-600">
              邮箱
              <input
                value={safeProfile.email || ""}
                onChange={(e) => handleField("email", e.target.value)}
                placeholder="your@email.com"
                type="email"
                className="mt-1 px-3 py-2 border border-slate-200 rounded-lg text-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400"
              />
            </label>
            {/* 授权码（只读，由系统分配） */}
            <label className="flex flex-col text-sm text-slate-600">
              授权码
              <div className="mt-1 px-3 py-2 border border-slate-200 rounded-lg text-slate-800 text-sm bg-slate-50 select-all">
                {safeProfile.auth_code || "（未设置）"}
              </div>
            </label>
            {/* 学校 */}
            <label className="flex flex-col text-sm text-slate-600">
              学校
              <input
                value={safeProfile.school || ""}
                onChange={(e) => handleField("school", e.target.value)}
                placeholder="例如 北京邮电大学"
                className="mt-1 px-3 py-2 border border-slate-200 rounded-lg text-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400"
              />
            </label>
            {/* 专业 */}
            <label className="flex flex-col text-sm text-slate-600">
              专业
              <input
                value={safeProfile.original_major || ""}
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
                value={safeProfile.gpa_score ?? ""}
                onChange={(e) => handleField("gpa_score", e.target.value ? parseFloat(e.target.value) : null)}
                placeholder="例如 82"
                className="mt-1 px-3 py-2 border border-slate-200 rounded-lg text-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400"
              />
            </label>
            {/* GPA 格式 */}
            <label className="flex flex-col text-sm text-slate-600">
              GPA 格式
              <select
                value={safeProfile.gpa_format || ""}
                onChange={(e) => handleField("gpa_format", e.target.value)}
                className="mt-1 px-3 py-2 border border-slate-200 rounded-lg text-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400 bg-white"
              >
                <option value="">选择</option>
                {GPA_FORMATS.map((f) => (
                  <option key={f} value={f}>{f}</option>
                ))}
              </select>
            </label>
            {/* 申请阶段 */}
            <label className="flex flex-col text-sm text-slate-600">
              申请阶段
              <select
                value={safeProfile.study_level || ""}
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
                value={safeProfile.target_major || ""}
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
                  const active = (safeProfile.target_countries || []).includes(c);
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
                value={safeProfile.ielts ?? ""}
                onChange={(e) => handleField("ielts", e.target.value ? parseFloat(e.target.value) : null)}
                placeholder="例如 7.0"
                className="mt-1 px-3 py-2 border border-slate-200 rounded-lg text-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400"
              />
            </label>
            <label className="flex flex-col text-sm text-slate-600">
              TOEFL 成绩
              <input
                type="number"
                value={safeProfile.toefl ?? ""}
                onChange={(e) => handleField("toefl", e.target.value ? parseInt(e.target.value) : null)}
                placeholder="例如 100"
                className="mt-1 px-3 py-2 border border-slate-200 rounded-lg text-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400"
              />
            </label>

            {/* MBTI（从天枢同步，只读） */}
            {tianshu?.mbti && (
              <div className="border border-indigo-100 rounded-xl p-4 bg-indigo-50/30 sm:col-span-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-lg">🧠</span>
                  <span className="font-semibold text-sm text-slate-700">MBTI</span>
                  <span className="text-sm font-bold text-indigo-600 ml-auto">{tianshu.mbti.type}</span>
                </div>
                <p className="text-xs text-slate-500">{tianshu.mbti.core || tianshu.mbti.nick}</p>
                {tianshu.mbti.fitMajors && (
                  <p className="text-xs text-slate-500 mt-1">🎯 {tianshu.mbti.fitMajors}</p>
                )}
              </div>
            )}

            {/* 霍兰德（从天枢同步，只读） */}
            {tianshu?.holland && (
              <div className="border border-amber-100 rounded-xl p-4 bg-amber-50/30 sm:col-span-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-lg">🎯</span>
                  <span className="font-semibold text-sm text-slate-700">霍兰德</span>
                  <span className="text-sm font-bold text-amber-600 ml-auto">{tianshu.holland.top3}</span>
                </div>
                <p className="text-xs text-slate-500">{tianshu.holland.codeExplain}</p>
                <div className="flex flex-wrap gap-1 mt-1.5">
                  {(tianshu.holland.sorted || []).slice(0, 3).map(([code, score]) => (
                    <span key={code} className="text-xs px-1.5 py-0.5 bg-amber-100 text-amber-700 rounded-full">
                      {code} {score}
                    </span>
                  ))}
                </div>
              </div>
            )}
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
                      <p>四柱: {tianshu.bazi.yearZhu || ""} · {tianshu.bazi.monthZhu || ""} · {tianshu.bazi.dayZhu || ""} · {tianshu.bazi.hourZhu || ""}</p>
                      <p>日主: {tianshu.bazi.dayMaster || ""}（{tianshu.bazi.dayMasterWx || ""}）</p>
                      <p>喜用: {(tianshu.bazi.xiZhong || []).join(" + ")}</p>
                    </div>
                  </div>
                )}

                {/* 星座 */}
                {tianshu.sunSign && (
                  (() => {
                    const ss = typeof tianshu.sunSign === "string"
                      ? tianshu.sunSign
                      : tianshu.sunSign.nameCN || tianshu.sunSign.name || "";
                    return (
                      <div className="border border-purple-100 rounded-xl p-4 bg-purple-50/30">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-lg">📅</span>
                          <span className="font-semibold text-slate-800">星座</span>
                          <span className="text-sm font-bold text-purple-600 ml-auto">{ss}</span>
                        </div>
                      </div>
                    );
                  })()
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
                {historyCounts.mbti} MBTI · {historyCounts.chat} 对话 · {historyCounts.tianshu} 天枢
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
                <HistoryRow key={item.id} item={item} onDelete={handleDelete} onViewDetail={viewDetail} />
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

