import { useMemo, useState } from "react";
import { useAppStore } from "../store/appStore";
import { useProfileStore } from "../store/profileStore";
import type { FavoriteSchool } from "../types";

/* ---------- types (boundary) ---------- */

interface RecommendSchool {
  name: string;
  qs_rank?: number;
  usnews_rank?: number;
  match_level: string;
  matched_cases: number;
  gpa_median?: number;
  toefl_display?: { type: string; value: number; label: string };
  meets_toefl?: boolean;
  tianshu_boost?: string;
  mbti_type?: string;
}

interface CountryEntry {
  country: string;
  schools: RecommendSchool[];
}

interface RecommendPayload {
  background?: Record<string, unknown>;
  match_summary?: { total_cases?: number; total_schools?: number };
  by_country?: CountryEntry[];
  pathway_suggestions?: Array<{ title?: string; description?: string } | string>;
  application_strategy?: string;
  major_recommendations?: Array<{ name?: string; reason?: string } | string>;
}

type MatchLevel = "冲刺" | "匹配" | "保底";

const LEVEL_ORDER: MatchLevel[] = ["冲刺", "匹配", "保底"];

const LEVEL_STYLES: Record<MatchLevel, { pill: string; ring: string; dot: string }> = {
  冲刺: {
    pill: "bg-emerald-50 text-emerald-700 border-emerald-200",
    ring: "ring-emerald-200",
    dot: "bg-emerald-500",
  },
  匹配: {
    pill: "bg-blue-50 text-blue-700 border-blue-200",
    ring: "ring-blue-200",
    dot: "bg-blue-500",
  },
  保底: {
    pill: "bg-amber-50 text-amber-700 border-amber-200",
    ring: "ring-amber-200",
    dot: "bg-amber-500",
  },
};

function normalizeLevel(raw: string): MatchLevel {
  if (raw === "冲刺" || raw === "匹配" || raw === "保底") return raw;
  // fallback heuristics for variant backend spellings
  if (/冲|reach|reach/i.test(raw)) return "冲刺";
  if (/保|safe|safety/i.test(raw)) return "保底";
  return "匹配";
}

/* ---------- school card ---------- */

function RankBadge({ school }: { school: RecommendSchool }) {
  if (school.qs_rank && school.usnews_rank) {
    return (
      <div className="flex flex-wrap gap-1.5">
        <span className="inline-flex items-center px-2 py-0.5 rounded-md bg-indigo-100 text-indigo-700 text-[11px] font-semibold border border-indigo-200">
          QS#{school.qs_rank}
        </span>
        <span className="inline-flex items-center px-2 py-0.5 rounded-md bg-indigo-100 text-indigo-700 text-[11px] font-semibold border border-indigo-200">
          USNews#{school.usnews_rank}
        </span>
      </div>
    );
  }
  if (school.qs_rank) {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded-md bg-indigo-100 text-indigo-700 text-[11px] font-semibold border border-indigo-200">
        QS#{school.qs_rank}
      </span>
    );
  }
  if (school.usnews_rank) {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded-md bg-indigo-100 text-indigo-700 text-[11px] font-semibold border border-indigo-200">
        USNews#{school.usnews_rank}
      </span>
    );
  }
  return null;
}

function ToeflIndicator({ school }: { school: RecommendSchool }) {
  const meets = school.meets_toefl === true;
  const label = school.toefl_display?.label
    ?? (school.toefl_display ? `TOEFL ${school.toefl_display.value}` : "TOEFL —");
  return (
    <div className="flex items-center gap-1.5 text-[12px]">
      <span className="text-slate-500">{label}</span>
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
    </div>
  );
}

function SchoolCard({ school, country, mbtiType }: { school: RecommendSchool; country: string; mbtiType?: string }) {
  const isFavorite = useAppStore((s) => s.isFavorite(school.name));
  const addFavorite = useAppStore((s) => s.addFavorite);
  const removeFavorite = useAppStore((s) => s.removeFavorite);

  const level = normalizeLevel(school.match_level);
  const styles = LEVEL_STYLES[level];

  const toggleFavorite = () => {
    if (isFavorite) {
      removeFavorite(school.name);
      return;
    }
    const fav: FavoriteSchool = {
      name: school.name,
      country,
      qs_rank: school.qs_rank,
      usnews_rank: school.usnews_rank,
      match_level: level,
      gpa_median: school.gpa_median,
      matched_cases: school.matched_cases,
      toefl_display: school.toefl_display,
      meets_toefl: school.meets_toefl,
    };
    addFavorite(fav);
  };

  return (
    <div
      className={`relative flex flex-col gap-2 p-3.5 rounded-xl bg-white border border-slate-200 shadow-sm lift ring-1 ${styles.ring}`}
    >
      {/* favorite */}
      <button
        type="button"
        onClick={toggleFavorite}
        aria-label={isFavorite ? "取消收藏" : "收藏"}
        aria-pressed={isFavorite}
        className={`absolute top-2.5 right-2.5 w-7 h-7 grid place-items-center rounded-full text-base transition-colors ${
          isFavorite
            ? "text-amber-500 hover:bg-amber-50"
            : "text-slate-300 hover:text-amber-400 hover:bg-amber-50"
        }`}
      >
        ⭐
      </button>

      {/* name + level pill */}
      <div className="flex items-start gap-2 pr-8">
        <h4 className="text-[14.5px] font-semibold text-slate-900 leading-snug">
          {school.name}
        </h4>
      </div>
      <span
        className={`self-start inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium border ${styles.pill}`}
      >
        <span className={`w-1.5 h-1.5 rounded-full ${styles.dot}`} />
        {level}
      </span>

      {/* ranks */}
      <RankBadge school={school} />

      {/* tianshu MBTI boost indicator */}
      {school.tianshu_boost && (
        <span className="self-start inline-flex items-center text-xs text-purple-600 bg-purple-50 rounded-full px-2 py-0.5">
          🌟 {mbtiType ? `与你的 MBTI (${mbtiType}) 匹配` : "MBTI 匹配"}
        </span>
      )}

      {/* meta */}
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-[12px] text-slate-500">
        <span>{school.matched_cases} 例</span>
        {school.gpa_median !== undefined && (
          <span>GPA 中位数 {school.gpa_median}</span>
        )}
      </div>

      {/* toefl */}
      <ToeflIndicator school={school} />

      {school.tianshu_boost && (
        <div className="mt-1 px-2 py-1 rounded-md bg-gradient-to-r from-indigo-50 to-violet-50 border border-indigo-100 text-[11.5px] text-indigo-700">
          天枢加成：{school.tianshu_boost}
        </div>
      )}
    </div>
  );
}

/* ---------- pathway accordion ---------- */

function PathwayAccordion({
  suggestions,
}: {
  suggestions: NonNullable<RecommendPayload["pathway_suggestions"]>;
}) {
  const [open, setOpen] = useState(false);
  if (!suggestions || suggestions.length === 0) return null;

  const items = suggestions.map((s) => {
    if (typeof s === "string") return { title: s, description: "" };
    return {
      title: s.title ?? "Pathway 方案",
      description: s.description ?? "",
    };
  });

  return (
    <div className="mt-4 rounded-xl border border-slate-200 bg-white overflow-hidden">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-slate-50 transition-colors"
      >
        <span className="flex items-center gap-2 text-[14px] font-semibold text-slate-900">
          <span>🎓</span>
          Pathway 预科方案
          <span className="text-[11px] font-normal text-slate-400">
            ({items.length})
          </span>
        </span>
        <span
          className={`text-slate-400 transition-transform duration-200 ${
            open ? "rotate-180" : ""
          }`}
        >
          ▾
        </span>
      </button>
      {open && (
        <ul className="px-4 pb-3 flex flex-col gap-2">
          {items.map((item, i) => (
            <li
              key={i}
              className="px-3 py-2 rounded-lg bg-slate-50 border border-slate-100"
            >
              <div className="text-[13px] font-medium text-slate-800">
                {item.title}
              </div>
              {item.description && (
                <div className="mt-1 text-[12px] text-slate-500 leading-relaxed">
                  {item.description}
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

/* ---------- main card ---------- */

export default function RecommendCard({ payload }: { payload: any }) {
  const data = payload as RecommendPayload;
  const [activeLevel, setActiveLevel] = useState<MatchLevel>("匹配");

  const hasRecommendData = Boolean(
    (data.by_country && data.by_country.length > 0) ||
      data.application_strategy ||
      (data.major_recommendations && data.major_recommendations.length > 0),
  );

  const handleExport = () => {
    window.print();
  };

  const profile = useProfileStore((s) => s.profile);
  const mbtiType = profile?.tianshu?.mbti?.type;
  const fitMajors = profile?.tianshu?.mbti?.fitMajors;
  const fitMajorTags = useMemo(
    () =>
      fitMajors
        ? fitMajors
            .split(/[,，\n]/)
            .map((m) => m.trim())
            .filter((m) => m.length > 0)
        : [],
    [fitMajors],
  );

  // group all schools across countries by match_level
  const { grouped, countryCount } = useMemo(() => {
    const byCountry = Array.isArray(data.by_country) ? data.by_country : [];
    const map: Record<MatchLevel, Array<{ school: RecommendSchool; country: string }>> = {
      冲刺: [],
      匹配: [],
      保底: [],
    };
    for (const entry of byCountry) {
      for (const school of entry.schools ?? []) {
        map[normalizeLevel(school.match_level)].push({
          school,
          country: entry.country,
        });
      }
    }
    return { grouped: map, countryCount: byCountry.length };
  }, [data.by_country]);

  const activeList = grouped[activeLevel];
  const summary = data.match_summary;

  return (
    <div className="flex flex-col gap-3 w-full recommend-card-print">
      {/* 打印专用头部（屏幕隐藏，打印时显示） */}
      <div className="print-header" aria-hidden="true">
        <h1>天权选校方案</h1>
        <div className="print-date">
          生成日期：{new Date().toLocaleDateString("zh-CN")}
        </div>
      </div>

      {/* header */}
      <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
        <h3 className="text-[16px] font-semibold text-slate-900">
          🎯 选校推荐
        </h3>
        {summary && (
          <span className="text-[12px] text-slate-500">
            共 {summary.total_schools ?? activeList.length} 所 ·{" "}
            {summary.total_cases ?? "—"} 例案例{countryCount > 0 ? ` · ${countryCount} 国` : ""}
          </span>
        )}
        {hasRecommendData && (
          <button
            type="button"
            onClick={handleExport}
            data-no-print
            className="ml-auto text-xs text-slate-500 hover:text-indigo-600 transition-colors"
            aria-label="导出选校方案为 PDF"
          >
            📄 导出选校方案
          </button>
        )}
      </div>

      {/* tianshu assessment-recommended majors summary */}
      {fitMajorTags.length > 0 && (
        <div className="p-3 rounded-xl bg-white border border-violet-200">
          <div className="text-[13px] font-semibold text-slate-900 mb-2">
            📊 根据你的测评结果
          </div>
          <div className="flex flex-wrap gap-1.5">
            {fitMajorTags.map((tag, i) => (
              <span
                key={i}
                className="inline-flex items-center bg-violet-50 text-violet-700 rounded-full text-xs px-2 py-1"
              >
                {tag}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* tabs */}
      <div className="flex gap-1 p-1 rounded-xl bg-slate-100 border border-slate-200 self-start overflow-x-auto thin-scrollbar flex-nowrap">
        {LEVEL_ORDER.map((lvl) => {
          const count = grouped[lvl].length;
          const active = lvl === activeLevel;
          return (
            <button
              key={lvl}
              type="button"
              onClick={() => setActiveLevel(lvl)}
              className={`px-3 py-1.5 rounded-lg text-[13px] font-medium transition-colors ${
                active
                  ? "bg-white text-indigo-700 shadow-sm border border-indigo-100"
                  : "text-slate-500 hover:text-slate-700"
              }`}
            >
              {lvl}
              <span
                className={`ml-1.5 text-[11px] ${
                  active ? "text-indigo-400" : "text-slate-400"
                }`}
              >
                {count}
              </span>
            </button>
          );
        })}
      </div>

      {/* schools grid: mobile stacked, desktop 3-col */}
      {activeList.length === 0 ? (
        <div className="px-4 py-6 rounded-xl bg-slate-50 border border-slate-200 text-center text-[13px] text-slate-500">
          暂无{activeLevel}档学校
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {activeList.map(({ school, country }) => (
            <SchoolCard key={`${country}-${school.name}`} school={school} country={country} mbtiType={mbtiType} />
          ))}
        </div>
      )}

      {/* pathway accordion */}
      {data.pathway_suggestions && data.pathway_suggestions.length > 0 && (
        <PathwayAccordion suggestions={data.pathway_suggestions} />
      )}

      {/* application strategy */}
      {data.application_strategy && (
        <div className="mt-2 p-4 rounded-xl bg-gradient-to-br from-indigo-50 to-violet-50 border border-indigo-100">
          <div className="text-[13px] font-semibold text-indigo-900 mb-1.5">
            📋 申请策略
          </div>
          <div className="text-[13px] text-slate-700 leading-relaxed whitespace-pre-wrap">
            {data.application_strategy}
          </div>
        </div>
      )}

      {/* major recommendations */}
      {data.major_recommendations && data.major_recommendations.length > 0 && (
        <div className="mt-1 p-4 rounded-xl bg-white border border-slate-200">
          <div className="text-[13px] font-semibold text-slate-900 mb-2">
            📚 专业推荐
          </div>
          <ul className="flex flex-col gap-1.5">
            {data.major_recommendations.map((m, i) => {
              const name = typeof m === "string" ? m : m.name ?? "";
              const reason = typeof m === "string" ? "" : m.reason ?? "";
              return (
                <li key={i} className="text-[13px] text-slate-700">
                  <span className="font-medium text-slate-900">{name}</span>
                  {reason && (
                    <span className="text-slate-500"> — {reason}</span>
                  )}
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </div>
  );
}