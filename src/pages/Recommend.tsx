import { useState } from "react";
import type { RecommendRequest, RecommendResult, ViewMode } from "../types";
import { fetchRecommend } from "../services/api";
import RecommendForm from "../components/RecommendForm";
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
        <header className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">天权</h1>
          <p className="text-gray-500 mt-1">
            基于 18.9 万真实案例的留学选校匹配
          </p>
        </header>

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
