import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import type { HistoryItem, ProfileData } from "../services/profile";
import {
  loadHistory,
  deleteHistoryItem,
  clearHistory,
} from "../services/profile";
import { logout } from "../services/auth";
import { viewDetail } from "../utils/profile-utils";
import { fetchChatHistory, deleteChatHistory } from "../services/chat";
import { generateId } from "../services/chat-helpers";
import HistoryRow from "../components/HistoryRow";
import BrandNav from "../components/BrandNav";
import SchoolComparison from "../components/SchoolComparison";
import { useProfileStore } from "../store/profileStore";

const SCENE_LABELS: Record<string, string> = {
  school: "选校", essay: "文书", visa: "签证",
};

/* =====================================================================
 * 我的档案 — Dashboard 布局：个人卡片 + 历史时间线 + 天枢测评摘要
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
  const [editing, setEditing] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    loadProfileFromStore();

    // 合并本地历史 + 远端对话历史
    const localHistory = loadHistory();

    fetchChatHistory(200, 0).then((remote) => {
      const remoteItems: HistoryItem[] = (remote.sessions || []).map((s: any) => {
        const messages = (s.messages || []).map((m: any) => ({
          id: generateId(),
          role: m.role,
          content: m.content,
          timestamp: m.created_at || Date.now(),
        }));
        const sceneLabel = SCENE_LABELS[s.scene] || s.scene || "对话";
        return {
          id: `remote_${s.session_id}`,
          type: "chat_session" as const,
          system: "tianquan" as const,
          data: { scene: s.scene, messages },
          summary: `${sceneLabel} · ${s.message_count} 条消息`,
          subtitle: messages[messages.length - 1]?.content?.slice(0, 40) || "",
          created_at: s.last_time || "",
        };
      });

      // 合并：远端对话 + 本地历史（远端排前面，避免覆盖本地非对话历史）
      const seenIds = new Set(remoteItems.map((i) => i.id));
      const merged = [...remoteItems, ...localHistory.filter((h) => !seenIds.has(`remote_${h.id}`))];
      setHistory(merged);
    }).catch(() => {
      // 远端不可用时回退到本地
      setHistory(localHistory);
    });
  }, []);

  /* profile 尚未加载完成时显示骨架占位 */
  if (!loaded) {
    return (
      <div className="min-h-screen bg-slate-50">
        <div className="max-w-7xl mx-auto px-4 py-6 sm:py-8">
          <div className="h-14 rounded-2xl bg-slate-200/60 animate-pulse mb-4" />
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
            <div className="lg:col-span-3 h-64 rounded-2xl bg-white border border-slate-200 animate-pulse" />
            <div className="lg:col-span-5 h-96 rounded-2xl bg-white border border-slate-200 animate-pulse" />
            <div className="lg:col-span-4 h-72 rounded-2xl bg-white border border-slate-200 animate-pulse" />
          </div>
        </div>
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
    setEditing(false);
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
    // 远端条目清理
    if (id.startsWith("remote_")) {
      const sessionId = id.slice(7);
      deleteChatHistory(sessionId);
    }
    deleteHistoryItem(id);
    setHistory((prev) => prev.filter((h) => h.id !== id));
  };

  const handleClearAll = async () => {
    if (!window.confirm("确定清空所有查询历史？此操作不可恢复。")) return;
    // 清空远端所有对话历史
    await deleteChatHistory();
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

  const countries = safeProfile.target_countries || [];
  const gpaText = safeProfile.gpa_score != null
    ? `${safeProfile.gpa_score}${safeProfile.gpa_format ? ` (${safeProfile.gpa_format})` : ""}`
    : null;

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="max-w-7xl mx-auto px-4 py-6 sm:py-8">

        {/* ======== 浮岛导航（统一 IFF 品牌）======= */}
        <BrandNav
          brandName="Iff"
          brandSubtitle="我的档案"
          links={[
            { label: "首页", icon: "home", href: "/" },
            { label: "档案", icon: "user", to: "/profile", active: true },
            { label: "天枢", icon: "compass", href: "../tianshu/", variant: "accent" },
          ]}
          actions={[
            {
              label: "退出",
              icon: "logout",
              onClick: () => { logout(); navigate("/login", { replace: true }); },
              title: "退出登录",
              hideTextOnMobile: true,
            },
          ]}
        />
        <div className="h-3" />

        {/* ======== Dashboard 三栏布局 ======== */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">

          {/* ======== ① 个人信息摘要卡片（左栏） ======== */}
          <section className="lg:col-span-3 bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
            {/* 渐变顶边：indigo → purple */}
            <div className="h-1.5 bg-gradient-to-r from-indigo-500 via-violet-500 to-purple-500" />

            <div className="p-5">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-base font-semibold text-slate-800">个人档案</h2>
                <button
                  onClick={() => setEditing((v) => !v)}
                  className="px-3 py-1 rounded-lg text-xs font-medium bg-indigo-50 text-indigo-700 border border-indigo-100 hover:bg-indigo-100 transition-colors"
                >
                  {editing ? "收起" : "编辑"}
                </button>
              </div>

              {/* 摘要视图 */}
              {!editing && (
                <div className="space-y-3">
                  <div>
                    <p className="text-xs text-slate-400 mb-0.5">用户名</p>
                    <p className="text-sm font-medium text-slate-800">{safeProfile.username || "未设置"}</p>
                  </div>
                  <div>
                    <p className="text-xs text-slate-400 mb-0.5">学校</p>
                    <p className="text-sm text-slate-700">{safeProfile.school || "未设置"}</p>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <p className="text-xs text-slate-400 mb-0.5">GPA</p>
                      <p className="text-sm text-slate-700">{gpaText || "未设置"}</p>
                    </div>
                    <div>
                      <p className="text-xs text-slate-400 mb-0.5">申请阶段</p>
                      <p className="text-sm text-slate-700">{safeProfile.study_level || "未设置"}</p>
                    </div>
                  </div>
                  <div>
                    <p className="text-xs text-slate-400 mb-0.5">目标专业</p>
                    <p className="text-sm text-slate-700">{safeProfile.target_major || "未设置"}</p>
                  </div>
                  <div>
                    <p className="text-xs text-slate-400 mb-1.5">目标国家/地区</p>
                    {countries.length > 0 ? (
                      <div className="flex flex-wrap gap-1.5">
                        {countries.map((c) => (
                          <span key={c} className="px-2 py-0.5 rounded-md text-xs font-medium bg-indigo-50 text-indigo-700 border border-indigo-100">
                            {c}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-slate-400">未设置</p>
                    )}
                  </div>
                  {(safeProfile.ielts != null || safeProfile.toefl != null) && (
                    <div className="grid grid-cols-2 gap-3 pt-2 border-t border-slate-100">
                      {safeProfile.ielts != null && (
                        <div>
                          <p className="text-xs text-slate-400 mb-0.5">IELTS</p>
                          <p className="text-sm text-slate-700">{safeProfile.ielts}</p>
                        </div>
                      )}
                      {safeProfile.toefl != null && (
                        <div>
                          <p className="text-xs text-slate-400 mb-0.5">TOEFL</p>
                          <p className="text-sm text-slate-700">{safeProfile.toefl}</p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* 编辑表单（折叠展开） */}
              {editing && (
                <div className="space-y-3">
                  <div className="flex justify-end">
                    <button
                      onClick={handleSave}
                      className={`px-3 py-1 rounded-lg text-xs font-medium transition-all ${
                        saved
                          ? "bg-green-100 text-green-700"
                          : "bg-indigo-600 text-white hover:bg-indigo-700"
                      }`}
                    >
                      {saved ? "✓ 已保存" : "保存"}
                    </button>
                  </div>
                  <label className="flex flex-col text-xs text-slate-600">
                    用户名
                    <input
                      value={safeProfile.username || ""}
                      onChange={(e) => handleField("username", e.target.value)}
                      placeholder="你的昵称"
                      className="mt-1 px-2.5 py-1.5 border border-slate-200 rounded-lg text-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400"
                    />
                  </label>
                  <label className="flex flex-col text-xs text-slate-600">
                    邮箱
                    <input
                      value={safeProfile.email || ""}
                      onChange={(e) => handleField("email", e.target.value)}
                      placeholder="your@email.com"
                      type="email"
                      className="mt-1 px-2.5 py-1.5 border border-slate-200 rounded-lg text-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400"
                    />
                  </label>
                  <label className="flex flex-col text-xs text-slate-600">
                    授权码
                    <div className="mt-1 px-2.5 py-1.5 border border-slate-200 rounded-lg text-slate-800 text-sm bg-slate-50 select-all">
                      {safeProfile.auth_code || "（未设置）"}
                    </div>
                  </label>
                  <label className="flex flex-col text-xs text-slate-600">
                    学校
                    <input
                      value={safeProfile.school || ""}
                      onChange={(e) => handleField("school", e.target.value)}
                      placeholder="例如 北京邮电大学"
                      className="mt-1 px-2.5 py-1.5 border border-slate-200 rounded-lg text-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400"
                    />
                  </label>
                  <label className="flex flex-col text-xs text-slate-600">
                    专业
                    <input
                      value={safeProfile.original_major || ""}
                      onChange={(e) => handleField("original_major", e.target.value)}
                      placeholder="例如 通信工程"
                      className="mt-1 px-2.5 py-1.5 border border-slate-200 rounded-lg text-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400"
                    />
                  </label>
                  <div className="grid grid-cols-2 gap-2">
                    <label className="flex flex-col text-xs text-slate-600">
                      GPA 分数
                      <input
                        type="number"
                        step="0.01"
                        value={safeProfile.gpa_score ?? ""}
                        onChange={(e) => handleField("gpa_score", e.target.value ? parseFloat(e.target.value) : null)}
                        placeholder="例如 82"
                        className="mt-1 px-2.5 py-1.5 border border-slate-200 rounded-lg text-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400"
                      />
                    </label>
                    <label className="flex flex-col text-xs text-slate-600">
                      GPA 格式
                      <select
                        value={safeProfile.gpa_format || ""}
                        onChange={(e) => handleField("gpa_format", e.target.value)}
                        className="mt-1 px-2.5 py-1.5 border border-slate-200 rounded-lg text-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400 bg-white"
                      >
                        <option value="">选择</option>
                        {GPA_FORMATS.map((f) => (
                          <option key={f} value={f}>{f}</option>
                        ))}
                      </select>
                    </label>
                  </div>
                  <label className="flex flex-col text-xs text-slate-600">
                    申请阶段
                    <select
                      value={safeProfile.study_level || ""}
                      onChange={(e) => handleField("study_level", e.target.value)}
                      className="mt-1 px-2.5 py-1.5 border border-slate-200 rounded-lg text-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400 bg-white"
                    >
                      <option value="">选择</option>
                      {STUDY_LEVELS.map((l) => (
                        <option key={l} value={l}>{l}</option>
                      ))}
                    </select>
                  </label>
                  <label className="flex flex-col text-xs text-slate-600">
                    目标专业
                    <input
                      value={safeProfile.target_major || ""}
                      onChange={(e) => handleField("target_major", e.target.value)}
                      placeholder="例如 计算机 / 金融"
                      className="mt-1 px-2.5 py-1.5 border border-slate-200 rounded-lg text-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400"
                    />
                  </label>
                  <div className="flex flex-col text-xs text-slate-600">
                    <span className="mb-1.5">目标国家/地区</span>
                    <div className="flex flex-wrap gap-1.5">
                      {COUNTRIES.map((c) => {
                        const active = countries.includes(c);
                        return (
                          <button
                            key={c}
                            onClick={() => handleCountry(c)}
                            className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all ${
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
                  <div className="grid grid-cols-2 gap-2">
                    <label className="flex flex-col text-xs text-slate-600">
                      IELTS
                      <input
                        type="number"
                        step="0.5"
                        value={safeProfile.ielts ?? ""}
                        onChange={(e) => handleField("ielts", e.target.value ? parseFloat(e.target.value) : null)}
                        placeholder="例如 7.0"
                        className="mt-1 px-2.5 py-1.5 border border-slate-200 rounded-lg text-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400"
                      />
                    </label>
                    <label className="flex flex-col text-xs text-slate-600">
                      TOEFL
                      <input
                        type="number"
                        value={safeProfile.toefl ?? ""}
                        onChange={(e) => handleField("toefl", e.target.value ? parseInt(e.target.value) : null)}
                        placeholder="例如 100"
                        className="mt-1 px-2.5 py-1.5 border border-slate-200 rounded-lg text-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400"
                      />
                    </label>
                  </div>
                </div>
              )}
            </div>
          </section>

          {/* ======== ② 查询历史时间线（中栏） ======== */}
          <section className="lg:col-span-5 bg-white rounded-2xl shadow-sm border border-slate-200 p-5 sm:p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-semibold text-slate-800">查询历史</h2>
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
              <div className="relative pl-1 sm:pl-4">
                {/* 时间线左侧轴线 */}
                <div className="hidden sm:block absolute left-1.5 top-2 bottom-2 w-px bg-gradient-to-b from-indigo-200 via-slate-200 to-slate-100" />
                <div className="space-y-1">
                  {history.map((item) => (
                    <div key={item.id} className="relative">
                      {/* 时间线节点 */}
                      <span className="hidden sm:block absolute -left-3.5 top-3.5 w-2 h-2 rounded-full bg-indigo-400 ring-2 ring-white shadow-sm" />
                      <HistoryRow item={item} onDelete={handleDelete} onViewDetail={viewDetail} />
                    </div>
                  ))}
                </div>
              </div>
            )}
          </section>

          {/* ======== ③ 天枢测评摘要（右栏） ======== */}
          <section className="lg:col-span-4 bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
            {/* 渐变顶边：violet → amber（天枢配色） */}
            <div className="h-1.5 bg-gradient-to-r from-violet-500 via-purple-500 to-amber-400" />

            <div className="p-5 sm:p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-base font-semibold text-slate-800">天枢测评</h2>
                <a
                  href="../tianshu/"
                  className="text-xs text-violet-600 hover:text-violet-700 hover:underline"
                >
                  前往天枢 →
                </a>
              </div>

              {!tianshu ? (
                /* 无测评结果：空状态引导 */
                <div className="text-center py-8 px-4">
                  <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-gradient-to-br from-violet-100 to-amber-50 mb-3">
                    <span className="text-2xl">🧭</span>
                  </div>
                  <p className="text-sm font-medium text-slate-700 mb-1">暂无测评结果</p>
                  <p className="text-xs text-slate-500 mb-4">完成天枢综合测评后，MBTI、霍兰德、八字等结果将自动同步到这里</p>
                  <a
                    href="../tianshu/"
                    className="inline-block px-4 py-2 rounded-lg text-sm font-medium bg-gradient-to-r from-violet-500 to-amber-400 text-white hover:opacity-90 transition-opacity"
                  >
                    去天枢完成测评
                  </a>
                </div>
              ) : (
                <div className="space-y-4">
                  {/* MBTI 类型徽章 */}
                  {tianshu.mbti && (
                    <div className="rounded-xl border border-indigo-100 bg-indigo-50/30 p-4">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-lg">🧠</span>
                        <span className="text-xs font-medium text-slate-500">MBTI</span>
                        <span className="ml-auto inline-flex items-center px-2.5 py-1 rounded-md text-sm font-bold text-indigo-700 bg-indigo-100 border border-indigo-200 tracking-wider">
                          {tianshu.mbti.type}
                        </span>
                      </div>
                      <p className="text-sm text-slate-700">{tianshu.mbti.core || tianshu.mbti.nick}</p>
                      {tianshu.mbti.fitMajors && (
                        <p className="text-xs text-slate-500 mt-1.5">🎯 {tianshu.mbti.fitMajors}</p>
                      )}
                    </div>
                  )}

                  {/* 霍兰德 Top3 */}
                  {tianshu.holland && (
                    <div className="rounded-xl border border-amber-100 bg-amber-50/30 p-4">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-lg">🎯</span>
                        <span className="text-xs font-medium text-slate-500">霍兰德</span>
                        <span className="ml-auto text-sm font-bold text-amber-600 tracking-wider">
                          {tianshu.holland.top3}
                        </span>
                      </div>
                      <p className="text-xs text-slate-500 mb-2">{tianshu.holland.codeExplain}</p>
                      <div className="flex flex-wrap gap-1.5">
                        {(tianshu.holland.sorted || []).slice(0, 3).map(([code, score]) => (
                          <span key={code} className="text-xs px-2 py-0.5 bg-amber-100 text-amber-700 rounded-full font-medium">
                            {code} {score}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* 综合标签 */}
                  {tianshu.summary && (tianshu.summary.tags || []).length > 0 && (
                    <div className="rounded-xl border border-violet-100 bg-gradient-to-br from-violet-50/50 to-amber-50/30 p-4">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-lg">✨</span>
                        <span className="text-xs font-medium text-slate-500">综合标签</span>
                      </div>
                      <div className="flex flex-wrap gap-1.5 mb-2">
                        {tianshu.summary.tags.map((t: string, i: number) => (
                          <span key={i} className="text-xs px-2 py-0.5 bg-violet-100 text-violet-700 rounded-full font-medium">
                            {t}
                          </span>
                        ))}
                      </div>
                      {tianshu.summary.summary && (
                        <p className="text-xs text-slate-600 leading-relaxed">{tianshu.summary.summary}</p>
                      )}
                    </div>
                  )}

                  {/* 八字简摘（如有） */}
                  {tianshu.bazi && (
                    <div className="rounded-xl border border-emerald-100 bg-emerald-50/30 p-3">
                      <div className="flex items-center gap-2 mb-1.5">
                        <span className="text-base">🔮</span>
                        <span className="text-xs font-medium text-slate-500">八字</span>
                      </div>
                      <p className="text-xs text-slate-600">
                        四柱: {tianshu.bazi.yearZhu || ""} · {tianshu.bazi.monthZhu || ""} · {tianshu.bazi.dayZhu || ""} · {tianshu.bazi.hourZhu || ""}
                      </p>
                      {tianshu.bazi.dayMaster && (
                        <p className="text-xs text-slate-500 mt-0.5">
                          日主: {tianshu.bazi.dayMaster}{tianshu.bazi.dayMasterWx ? `（${tianshu.bazi.dayMasterWx}）` : ""}
                        </p>
                      )}
                    </div>
                  )}

                  <p className="text-xs text-slate-400 pt-1">数据来自天枢测评，在天枢中重新测评后可更新</p>
                </div>
              )}
            </div>
          </section>
        </div>

        {/* ======== 收藏学校对比表（全宽） ======== */}
        <SchoolComparison />
      </div>
    </div>
  );
}