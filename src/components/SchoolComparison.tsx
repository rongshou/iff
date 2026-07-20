import { useMemo, useState } from "react";
import { useAppStore } from "../store/appStore";
import type { FavoriteSchool } from "../types";

/* =====================================================================
 * SchoolComparison — 收藏学校对比表
 * ---------------------------------------------------------------------
 * Reads favorites from appStore. Renders a sortable table; click a
 * column header to toggle asc/desc. Default order is add-order (none).
 * Empty state nudges the user to favorite schools from 选校推荐.
 * ===================================================================== */

type MatchLevel = "冲刺" | "匹配" | "保底";

const LEVEL_ORDER: Record<MatchLevel, number> = {
  冲刺: 0,
  匹配: 1,
  保底: 2,
};

const LEVEL_STYLES: Record<MatchLevel, string> = {
  冲刺: "bg-emerald-50 text-emerald-700 border-emerald-200",
  匹配: "bg-blue-50 text-blue-700 border-blue-200",
  保底: "bg-amber-50 text-amber-700 border-amber-200",
};

function normalizeLevel(raw: string): MatchLevel {
  if (raw === "冲刺" || raw === "匹配" || raw === "保底") return raw;
  if (/冲|reach/i.test(raw)) return "冲刺";
  if (/保|safe/i.test(raw)) return "保底";
  return "匹配";
}

type SortKey =
  | "name"
  | "country"
  | "rank"
  | "match_level"
  | "gpa_median"
  | "matched_cases"
  | "toefl";

type SortDir = "asc" | "desc";

interface ColumnDef {
  key: SortKey;
  label: string;
  className: string;
}

const COLUMNS: ColumnDef[] = [
  { key: "name", label: "学校名称", className: "text-left" },
  { key: "country", label: "国家", className: "text-left" },
  { key: "rank", label: "排名", className: "text-left" },
  { key: "match_level", label: "匹配档位", className: "text-left" },
  { key: "gpa_median", label: "GPA中位数", className: "text-right" },
  { key: "matched_cases", label: "案例数", className: "text-right" },
  { key: "toefl", label: "TOEFL要求", className: "text-left" },
];

function rankValue(s: FavoriteSchool): number {
  // Prefer QS, fall back to USNews. Treat missing as +Infinity so unranked
  // schools sort to the bottom in asc order.
  if (typeof s.qs_rank === "number") return s.qs_rank;
  if (typeof s.usnews_rank === "number") return s.usnews_rank;
  return Number.POSITIVE_INFINITY;
}

function rankLabel(s: FavoriteSchool): string {
  if (s.qs_rank && s.usnews_rank) return `QS#${s.qs_rank} · USNews#${s.usnews_rank}`;
  if (s.qs_rank) return `QS#${s.qs_rank}`;
  if (s.usnews_rank) return `USNews#${s.usnews_rank}`;
  return "—";
}

function toeflLabel(s: FavoriteSchool): string {
  if (s.toefl_display?.label) return s.toefl_display.label;
  if (s.toefl_display) return `TOEFL ${s.toefl_display.value}`;
  return "—";
}

function compareValues(a: FavoriteSchool, b: FavoriteSchool, key: SortKey): number {
  switch (key) {
    case "name":
      return a.name.localeCompare(b.name, "zh-Hans-CN");
    case "country":
      return a.country.localeCompare(b.country, "zh-Hans-CN");
    case "rank":
      return rankValue(a) - rankValue(b);
    case "match_level":
      return (
        LEVEL_ORDER[normalizeLevel(a.match_level)] -
        LEVEL_ORDER[normalizeLevel(b.match_level)]
      );
    case "gpa_median":
      return (a.gpa_median ?? -Infinity) - (b.gpa_median ?? -Infinity);
    case "matched_cases":
      return a.matched_cases - b.matched_cases;
    case "toefl":
      return (a.toefl_display?.value ?? -Infinity) - (b.toefl_display?.value ?? -Infinity);
  }
}

export default function SchoolComparison() {
  const favorites = useAppStore((s) => s.favorites);
  const removeFavorite = useAppStore((s) => s.removeFavorite);

  const [sortKey, setSortKey] = useState<SortKey | null>(null);
  const [sortDir, setSortDir] = useState<SortDir>("asc");

  const handleExport = () => {
    window.print();
  };

  const sorted = useMemo(() => {
    if (sortKey === null) return favorites;
    const copy = [...favorites];
    copy.sort((a, b) => {
      const cmp = compareValues(a, b, sortKey);
      return sortDir === "asc" ? cmp : -cmp;
    });
    return copy;
  }, [favorites, sortKey, sortDir]);

  const handleHeaderClick = (key: SortKey) => {
    if (sortKey === null || sortKey !== key) {
      setSortKey(key);
      setSortDir("asc");
    } else if (sortDir === "asc") {
      setSortDir("desc");
    } else {
      // third click resets to add-order
      setSortKey(null);
      setSortDir("asc");
    }
  };

  if (favorites.length === 0) {
    return (
      <section className="bg-white rounded-2xl shadow-sm border border-slate-200 p-5 sm:p-6 mb-5">
        <h2 className="text-base font-semibold text-slate-800 mb-4">⭐ 收藏学校对比</h2>
        <div className="text-center py-10 text-slate-400">
          <p className="text-3xl mb-2">⭐</p>
          <p className="text-sm">还没有收藏学校，在选校推荐中点击 ⭐ 即可收藏</p>
        </div>
      </section>
    );
  }

  return (
    <section className="bg-white rounded-2xl shadow-sm border border-slate-200 p-5 sm:p-6 mb-5 comparison-table-print">
      {/* 打印专用头部（屏幕隐藏，打印时显示） */}
      <div className="print-header" aria-hidden="true">
        <h1>院校对比表</h1>
        <div className="print-date">
          生成日期：{new Date().toLocaleDateString("zh-CN")}
        </div>
      </div>

      <div className="flex items-center justify-between mb-4">
        <h2 className="text-base font-semibold text-slate-800">⭐ 收藏学校对比</h2>
        <div className="flex items-center gap-3">
          <span className="text-xs text-slate-400">{favorites.length} 所学校</span>
          <button
            type="button"
            onClick={handleExport}
            data-no-print
            className="text-xs text-slate-500 hover:text-indigo-600 transition-colors"
            aria-label="导出对比表为 PDF"
          >
            📄 导出对比表
          </button>
        </div>
      </div>

      <div className="overflow-x-auto -mx-1 px-1">
        <table className="w-full text-sm border-collapse min-w-[720px]">
          <thead>
            <tr className="border-b border-slate-200">
              {COLUMNS.map((col) => (
                <th
                  key={col.key}
                  onClick={() => handleHeaderClick(col.key)}
                  className={`px-3 py-2 text-xs font-semibold text-slate-500 cursor-pointer select-none whitespace-nowrap transition-colors hover:text-indigo-600 ${col.className}`}
                >
                  <span className="inline-flex items-center gap-1">
                    {col.label}
                    {sortKey === col.key && (
                      <span className="text-indigo-500" style={{ color: "#6366f1" }}>
                        {sortDir === "asc" ? "▲" : "▼"}
                      </span>
                    )}
                  </span>
                </th>
              ))}
              <th className="px-3 py-2 text-xs font-semibold text-slate-500 text-left">
                操作
              </th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((school) => {
              const level = normalizeLevel(school.match_level);
              const meets = school.meets_toefl === true;
              return (
                <tr
                  key={school.name}
                  className="border-b border-slate-100 hover:bg-slate-50/60 transition-colors"
                >
                  <td className="px-3 py-2 text-slate-800 font-medium whitespace-nowrap">
                    {school.name}
                  </td>
                  <td className="px-3 py-2 whitespace-nowrap" style={{ color: "#475569" }}>
                    {school.country}
                  </td>
                  <td className="px-3 py-2 whitespace-nowrap" style={{ color: "#475569" }}>
                    {rankLabel(school)}
                  </td>
                  <td className="px-3 py-2 whitespace-nowrap">
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium border ${LEVEL_STYLES[level]}`}
                    >
                      {level}
                    </span>
                  </td>
                  <td className="px-3 py-2 text-right whitespace-nowrap" style={{ color: "#475569" }}>
                    {typeof school.gpa_median === "number"
                      ? school.gpa_median.toFixed(2)
                      : "—"}
                  </td>
                  <td className="px-3 py-2 text-right whitespace-nowrap" style={{ color: "#475569" }}>
                    {school.matched_cases}
                  </td>
                  <td className="px-3 py-2 whitespace-nowrap">
                    <span className="inline-flex items-center gap-1.5">
                      <span style={{ color: "#475569" }}>{toeflLabel(school)}</span>
                      <span
                        className={`inline-flex items-center justify-center w-4 h-4 rounded-full text-[10px] font-bold ${
                          meets
                            ? "bg-emerald-100 text-emerald-700"
                            : "bg-rose-100 text-rose-700"
                        }`}
                        aria-label={meets ? "满足" : "未满足"}
                      >
                        {meets ? "✓" : "✗"}
                      </span>
                    </span>
                  </td>
                  <td className="px-3 py-2 whitespace-nowrap">
                    <button
                      onClick={() => removeFavorite(school.name)}
                      className="text-xs text-red-500 hover:text-red-700 hover:underline transition-colors"
                      aria-label={`移除 ${school.name}`}
                    >
                      删除
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-slate-400 mt-3">
        点击表头可排序，再次点击切换升序/降序，第三次点击恢复收藏顺序
      </p>
    </section>
  );
}