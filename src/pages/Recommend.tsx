import { useState } from "react";
import { Link } from "react-router-dom";
import type { RecommendRequest, RecommendResult, ViewMode } from "../types";
import { fetchRecommend } from "../services/api";
import RecommendForm from "../components/RecommendForm";
import { loadProfile, addHistoryItem, createRecommendHistoryItem } from "../services/profile";
import SchoolCard from "../components/SchoolCard";
import SchoolTable from "../components/SchoolTable";
import PathwaySection from "../components/PathwaySection";

const RANK_LABELS: Record<string, string> = {
  英国: "QS", 美国: "USNews",
};

function getRankLabel(country: string): string {
  return RANK_LABELS[country] ?? "QS";
}

export default function RecommendPage() {
  const [result, setResult] = useState<RecommendResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>("cards");
  const [expandedCountries, setExpandedCountries] = useState<Set<string>>(new Set(["英国"]));

  const handleSubmit = async (data: RecommendRequest) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchRecommend(data);
      setResult(res);
      // 保存推荐结果到历史
      const profile = loadProfile() || {};
      addHistoryItem(createRecommendHistoryItem(
        { ...profile, ...data, target_countries: data.target_countries },
        res,
      ));
      const firstCountry = res.by_country[0]?.country;
      if (firstCountry) {
        setExpandedCountries(new Set([firstCountry]));
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "请求失败");
    } finally {
      setLoading(false);
    }
  };

  const toggleCountry = (c: string) => {
    setExpandedCountries((prev) => {
      const next = new Set(prev);
      if (next.has(c)) next.delete(c);
      else next.add(c);
      return next;
    });
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-8">
        <header className="text-center mb-6">
          <div className="flex items-center justify-center gap-3">
            <h1 className="text-3xl font-bold text-gray-900">天权</h1>
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
          </div>
          <p className="text-gray-500 mt-1">
            基于 17 万+ 真实录取案例的相似背景匹配
          </p>
        </header>

        {/* 推荐原理说明 */}
        <details className="group mb-6 bg-white rounded-xl shadow-sm border border-indigo-100 overflow-hidden">
          <summary className="flex items-center gap-2 px-5 py-3 cursor-pointer text-sm font-medium text-indigo-700 hover:bg-indigo-50/50 transition-colors select-none">
            <span className="text-indigo-500 text-base">ⓘ</span>
            <span>推荐原理：系统是如何匹配学校的？</span>
            <span className="ml-auto text-xs text-gray-400 group-open:rotate-180 transition-transform">▾</span>
          </summary>
          <div className="px-5 pb-4 pt-1 text-sm text-gray-600 border-t border-indigo-100 leading-relaxed space-y-2">
            <p>
              <strong>第一步 — 案例筛选</strong>：从 17.6 万条真实录取案例中，按目标国家/地区、学位层级、专业方向筛选出相关案例。
            </p>
            <p>
              <strong>第二步 — 背景匹配</strong>：基于你的 GPA（±0.45 容差）、本科学校层次（C9/985/211/双非）、专业方向进行相似度过滤，找到与你背景最接近的往届申请者。
            </p>
            <p>
              <strong>第三步 — 概率估算</strong>：对匹配到的每所学校，提取该校同层次申请者的 GPA 百分位数据（p25/p50/p75），对比你的 GPA 位置，判断录取概率：
            </p>
            <p>
              <strong>第三步 — 三维评分</strong>：综合 <strong>GPA 匹配分（40%）+ 学校排名分（30%）+ 案例证据分（30%）</strong> 进行打分，分三档输出：
            </p>
            <div className="flex flex-wrap gap-2 ml-2 my-1">
              <span className="px-2.5 py-1 bg-amber-50 text-amber-700 rounded-full text-xs font-medium">总分 &lt; 55 → 冲刺（需补强软背景）</span>
              <span className="px-2.5 py-1 bg-blue-50 text-blue-700 rounded-full text-xs font-medium">55 ≤ 总分 &lt; 75 → 匹配（大概率可录）</span>
              <span className="px-2.5 py-1 bg-green-50 text-green-700 rounded-full text-xs font-medium">总分 ≥ 75 → 安全（稳拿）</span>
            </div>
            <p>
              <strong>第四步 — 档内排序</strong>：每档最多 6 所，档内按 QS 排名升序排列。冲刺校附带提分建议（需提升多少百分点可进匹配档）。
            </p>
            <p className="text-xs text-gray-400 mt-1">
              💡 每所学校都标注了"同背景匹配案例 N 例"和"录取 GPA 中位数"，数据均来自真实录取案例，不是黑箱估算。
            </p>
          </div>
        </details>

        <RecommendForm onSubmit={handleSubmit} loading={loading} />

        {error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {error}
          </div>
        )}

        {result && (
          <>
            {/* Pathway suggestions */}
            <PathwaySection suggestions={result.pathway_suggestions} />

            <div className="mt-6 space-y-4">
            {/* Summary */}
            <div className="bg-white rounded-xl shadow-sm border p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-4 text-sm">
                  <span className="text-gray-500">
                    背景:{" "}
                    <strong>{result.background.school_tier_label}</strong>
                    {" "}GPA{" "}
                    <strong>{result.background.gpa4}</strong>
                    {" "}({result.background.gpa_percent}分)
                  </span>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => setViewMode("cards")}
                    className={`px-3 py-1 rounded text-sm ${
                      viewMode === "cards"
                        ? "bg-indigo-600 text-white"
                        : "bg-gray-100 text-gray-600"
                    }`}
                  >
                    卡片
                  </button>
                  <button
                    onClick={() => setViewMode("table")}
                    className={`px-3 py-1 rounded text-sm ${
                      viewMode === "table"
                        ? "bg-indigo-600 text-white"
                        : "bg-gray-100 text-gray-600"
                    }`}
                  >
                    表格
                  </button>
                </div>
              </div>
              <p className="text-2xl font-bold text-indigo-600">
                {result.match_summary.total_cases}
                <span className="text-base text-gray-400 font-normal"> 例匹配</span>
                {" · "}
                {result.match_summary.total_schools}
                <span className="text-base text-gray-400 font-normal"> 所学校</span>
              </p>
            </div>

            {/* Results by country */}
            {result.by_country.map((c) => (
              <div key={c.country} className="bg-white rounded-xl shadow-sm border">
                <button
                  onClick={() => toggleCountry(c.country)}
                  className="w-full flex items-center justify-between p-4 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-lg font-semibold">{c.country}</span>
                    <span className="text-sm text-gray-500">
                      {c.matched_cases} 例 · {c.matched_schools} 校
                    </span>
                  </div>
                  <span className="text-gray-400">
                    {expandedCountries.has(c.country) ? "▾" : "▸"}
                  </span>
                </button>

                {expandedCountries.has(c.country) && c.schools.length > 0 && (
                  <div className="p-4 pt-0">
                    {viewMode === "cards" ? (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {c.schools.map((s, i) => (
                          <SchoolCard
                            key={i}
                            school={s}
                            rankLabel={getRankLabel(c.country)}
                          />
                        ))}
                      </div>
                    ) : (
                      <SchoolTable data={c} rankLabel={getRankLabel(c.country)} />
                    )}
                  </div>
                )}

                {expandedCountries.has(c.country) && c.schools.length === 0 && (
                  <div className="p-4 pt-0 text-gray-400 text-center">
                    暂无匹配案例
                  </div>
                )}
              </div>
            ))}
          </div>
          </>
        )}

        {loading && (
          <div className="mt-6 text-center">
            <div className="inline-block w-8 h-8 border-3 border-indigo-600 border-t-transparent rounded-full animate-spin" />
            <p className="text-gray-500 mt-2">正在查询案例库...</p>
          </div>
        )}
      </div>
    </div>
  );
}
