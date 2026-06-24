import type { PathwaySuggestion } from "../types";

function getCountryFlag(country: string): string {
  const flags: Record<string, string> = {
    UK: "🇬🇧", US: "🇺🇸", AU: "🇦🇺", CA: "🇨🇦",
    HK: "🇭🇰", SG: "🇸🇬", IE: "🇮🇪", MY: "🇲🇾",
  };
  return flags[country] ?? "🎓";
}

interface Props {
  suggestions: PathwaySuggestion[];
}

export default function PathwaySection({ suggestions }: Props) {
  if (suggestions.length === 0) return null;

  return (
    <div className="mt-6 bg-gradient-to-r from-amber-50 to-orange-50 rounded-xl shadow-sm border border-amber-200 p-6">
      <div className="flex items-center gap-2 mb-4">
        <span className="text-xl">🛤️</span>
        <h2 className="text-lg font-bold text-amber-800">预科/通路建议</h2>
        <span className="text-xs bg-amber-200 text-amber-700 px-2 py-0.5 rounded-full">
          低GPA逆袭名校
        </span>
      </div>

      <p className="text-sm text-amber-700 mb-4">
        {suggestions[0].reason || "你的 GPA 直接申请这些名校可能有一定难度，但通过预科/硕士预科课程可以实现弯道超车："}
      </p>

      <div className="space-y-3">
        {suggestions.map((s, i) => (
          <div
            key={i}
            className="bg-white rounded-lg border border-amber-100 p-4"
          >
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <span>{getCountryFlag(s.country)}</span>
                <span className="font-semibold text-gray-900">{s.university}</span>
                {s.qs_rank && (
                  <span className="text-xs bg-indigo-100 text-indigo-700 px-1.5 py-0.5 rounded">
                    QS#{s.qs_rank}
                  </span>
                )}
              </div>
            </div>

            {s.programs.map((p, j) => (
              <div
                key={j}
                className="mt-2 ml-6 p-3 bg-gray-50 rounded border border-gray-100 text-sm"
              >
                <div className="flex items-center gap-2 flex-wrap mb-1">
                  <span className="font-medium text-indigo-700">
                    {p.program_type}
                  </span>
                  {p.provider && (
                    <span className="text-gray-400">| {p.provider}</span>
                  )}
                  {p.direction && (
                    <span className="text-gray-500">· {p.direction}</span>
                  )}
                </div>
                <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-500">
                  {p.duration && <span>⏱ {p.duration}</span>}
                  {p.intake && <span>📅 {p.intake}开学</span>}
                  {p.academic_req && <span>📚 {p.academic_req}</span>}
                  {p.ielts_req && <span>🗣 {p.ielts_req}</span>}
                  {p.location && <span>📍 {p.location}</span>}
                </div>
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
