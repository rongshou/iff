import type { SchoolMatchItem } from "../types";

interface Props {
  school: SchoolMatchItem;
  rankLabel: string;
}

export default function SchoolCard({ school, rankLabel }: Props) {
  const label = school.admission_chance || (school.meets_requirement ? "可达" : "冲刺");
  const rankValue = rankLabel === "USNews" ? school.usnews_rank : school.qs_rank;
  const colors: Record<string, string> = {
    安全: "bg-green-100 text-green-800",
    匹配: "bg-blue-100 text-blue-800",
    冲刺: "bg-amber-100 text-amber-800",
    彩票: "bg-red-100 text-red-800",
    可达: "bg-green-100 text-green-800",
    未知: "bg-gray-100 text-gray-600",
  };

  return (
    <div className="border rounded-lg p-4 bg-white hover:shadow-md transition-shadow">
      <div className="flex justify-between items-start mb-2">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">{school.name}</h3>
          <p className="text-sm text-gray-500">
            {rankLabel}: {rankValue ?? "-"}
          </p>
        </div>
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${colors[label] || "bg-gray-100 text-gray-600"}`}>
          {label}
        </span>
      </div>

      <div className="grid grid-cols-3 gap-2 mb-3 text-sm">
        <div>
          <span className="text-gray-400">匹配案例</span>
          <p className="font-semibold text-gray-800">{school.matched_cases}</p>
        </div>
        <div>
          <span className="text-gray-400">GPA 范围</span>
          <p className="font-semibold text-gray-800">
            {school.gpa_min !== null ? `${school.gpa_min} - ${school.gpa_max}` : "-"}
          </p>
        </div>
        <div>
          <span className="text-gray-400">录取中位 GPA</span>
          <p className="font-semibold text-gray-800">
            {school.p50_reference !== null ? `${school.p50_reference}分` : "-"}
          </p>
        </div>
      </div>

      {school.majors.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {school.majors.map((m, i) => (
            <span
              key={i}
              className="px-2 py-0.5 bg-indigo-50 text-indigo-700 rounded text-xs"
            >
              {m}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
