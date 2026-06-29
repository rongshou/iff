import { useState } from "react";
import { Link } from "react-router-dom";
import type { MBTIMajorResult, TimelinePhase } from "../types";
import { MBTI_QUESTIONS, calculateMBTI, fetchMBTIMajors, fetchTimeline } from "../services/explore";
import { saveProfile, addHistoryItem, createMBTIHistoryItem, loadProfile } from "../services/profile";

const MBTI_EMOJI: Record<string, string> = {
  INTJ: "🏗️", INTP: "🔬", ENTJ: "👑", ENTP: "💡",
  INFJ: "🌿", INFP: "🎨", ENFJ: "🌟", ENFP: "🔥",
  ISTJ: "📋", ISFJ: "🛡️", ESTJ: "⚙️", ESFJ: "🤝",
  ISTP: "🔧", ISFP: "🎵", ESTP: "🏄", ESFP: "🎭",
};

export default function ExplorePage() {
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [mbtiResult, setMbtiResult] = useState<MBTIMajorResult | null>(null);
  const [timeline, setTimeline] = useState<TimelinePhase[]>([]);
  const [studyLevel, setStudyLevel] = useState("硕士");
  const [loading, setLoading] = useState(false);

  const handleAnswer = (qId: number, value: string) => {
    if (mbtiResult) return;
    const newAnswers = { ...answers, [qId]: value };
    setAnswers(newAnswers);
    if (Object.keys(newAnswers).length === MBTI_QUESTIONS.length) {
      submitMBTI(newAnswers);
    }
  };

  const submitMBTI = async (ans: Record<number, string>) => {
    setLoading(true);
    const mbti = calculateMBTI(ans);
    try {
      const result = await fetchMBTIMajors(mbti);
      setMbtiResult(result);
      // 自动保存 MBTI 到 profile + history
      saveProfile({ tianshu: { ...(loadProfile()?.tianshu || {} as any), mbti: { type: result.type, name: result.name, top_majors: result.top_majors }, updated_at: new Date().toISOString() } as any });
      addHistoryItem(createMBTIHistoryItem(result, answers));
    } catch { /* ignore */ }
    setLoading(false);
  };

  const loadTimeline = async (level: string) => {
    setStudyLevel(level);
    try {
      const phases = await fetchTimeline(level);
      setTimeline(phases);
    } catch { /* ignore */ }
  };

  const progress = Object.keys(answers).length;
  const total = MBTI_QUESTIONS.length;

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-8">
        <header className="text-center mb-8">
          <div className="flex items-center justify-center gap-3 mb-2">
            <h1 className="text-3xl font-bold text-gray-900">留学工具箱</h1>
            <Link
              to="/"
              className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium text-indigo-600 bg-indigo-50 border border-indigo-200 hover:bg-indigo-100 transition-all"
              title="首页"
            ><span>🏠</span>首页</Link>
            <Link
              to="/profile"
              className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium text-slate-400 border border-slate-200 hover:text-indigo-600 hover:border-indigo-300 hover:bg-indigo-50 transition-all"
              title="我的档案"
            ><span>📁</span>档案</Link>
            <a
              href="../tianshu/"
              className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium text-slate-400 border border-slate-200 hover:text-indigo-600 hover:border-indigo-300 hover:bg-indigo-50 transition-all"
              title="切换到天枢测评"
            ><span>🧭</span>天枢</a>
          </div>
          <p className="text-gray-500 mt-1">MBTI性格选专业 · 申请时间线</p>
        </header>

        {/* MBTI Section */}
        <section className="bg-white rounded-xl shadow-sm border p-6 mb-6">
          <h2 className="text-xl font-bold mb-2">🧠 MBTI 性格选专业</h2>
          <p className="text-sm text-gray-500 mb-4">回答 8 道题，找到最适合你性格的留学专业方向</p>

          {!mbtiResult ? (
            <>
              <div className="mb-4 bg-gray-100 rounded-full h-2">
                <div className="bg-indigo-600 h-2 rounded-full transition-all" style={{ width: `${(progress / total) * 100}%` }} />
              </div>
              <div className="space-y-4">
                {MBTI_QUESTIONS.map((q) => (
                  <div key={q.id} className={`p-4 rounded-lg border ${answers[q.id] ? "border-indigo-300 bg-indigo-50" : "border-gray-200"}`}>
                    <p className="font-medium text-gray-800 mb-2">{q.id}. {q.text}</p>
                    <div className="flex gap-2">
                      {q.options.map((opt) => (
                        <button
                          key={opt.value}
                          onClick={() => handleAnswer(q.id, opt.value)}
                          className={`flex-1 p-2 rounded-lg text-sm font-medium transition-colors ${answers[q.id] === opt.value ? "bg-indigo-600 text-white" : "bg-gray-100 text-gray-600 hover:bg-gray-200"}`}
                        >
                          {opt.label}
                        </button>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="animate-fadeIn">
              {loading ? (
                <div className="text-center py-8">
                  <div className="inline-block w-8 h-8 border-3 border-indigo-600 border-t-transparent rounded-full animate-spin" />
                </div>
              ) : (
                <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-xl p-6">
                  <div className="flex items-center gap-3 mb-4">
                    <span className="text-4xl">{MBTI_EMOJI[mbtiResult.type] || "🎓"}</span>
                    <div>
                      <h3 className="text-2xl font-bold">{mbtiResult.type} — {mbtiResult.name}</h3>
                      <p className="text-sm text-gray-500">{mbtiResult.learning_style}</p>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <h4 className="font-semibold text-green-700 mb-1">✅ 推荐专业</h4>
                      <div className="flex flex-wrap gap-1">
                        {mbtiResult.top_majors.map((m, i) => (
                          <span key={i} className="px-2 py-1 bg-green-100 text-green-800 rounded text-sm">{m}</span>
                        ))}
                      </div>
                    </div>
                    <div>
                      <h4 className="font-semibold text-red-700 mb-1">⚠️ 慎重考虑</h4>
                      <div className="flex flex-wrap gap-1">
                        {mbtiResult.avoid_majors.map((m, i) => (
                          <span key={i} className="px-2 py-1 bg-red-50 text-red-600 rounded text-sm">{m}</span>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="mt-4 pt-4 border-t border-indigo-200 space-y-2">
                    <p className="text-sm"><strong>💼 适合职业：</strong>{mbtiResult.career_path}</p>
                    <p className="text-sm"><strong>💡 学习建议：</strong>{mbtiResult.study_tips}</p>
                  </div>

                  <button
                    onClick={() => { setMbtiResult(null); setAnswers({}); }}
                    className="mt-4 text-sm text-indigo-600 hover:underline"
                  >
                    🔄 重新测试
                  </button>
                </div>
              )}
            </div>
          )}
        </section>

        {/* Timeline Section */}
        <section className="bg-white rounded-xl shadow-sm border p-6">
          <h2 className="text-xl font-bold mb-2">📅 申请时间线</h2>
          <p className="text-sm text-gray-500 mb-4">按学位阶段查看留学申请全程时间规划</p>

          <div className="flex gap-2 mb-4">
            {["本科", "硕士", "博士"].map((l) => (
              <button
                key={l}
                onClick={() => loadTimeline(l)}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${studyLevel === l ? "bg-indigo-600 text-white" : "bg-gray-100 text-gray-600 hover:bg-gray-200"}`}
              >
                {l}
              </button>
            ))}
          </div>

          {timeline.length > 0 && (
            <div className="relative">
              <div className="absolute left-5 top-0 bottom-0 w-0.5 bg-indigo-200" />
              <div className="space-y-4">
                {timeline.map((phase, i) => (
                  <div key={i} className="relative pl-12">
                    <div className="absolute left-3 top-1.5 w-4 h-4 rounded-full bg-indigo-600 border-2 border-white shadow" />
                    <div className="bg-gray-50 rounded-lg p-4 border border-gray-100">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-xs bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded-full font-medium">
                          {phase.month}
                        </span>
                        <h4 className="font-semibold text-gray-900">{phase.phase}</h4>
                      </div>
                      <ul className="space-y-1">
                        {phase.tasks.map((t, j) => (
                          <li key={j} className="text-sm text-gray-600 flex items-start gap-1">
                            <span className="text-indigo-400 mt-0.5">•</span>
                            {t}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
          {timeline.length === 0 && (
            <p className="text-gray-400 text-center py-4">点击上方学位阶段查看时间规划</p>
          )}
        </section>
      </div>
    </div>
  );
}
