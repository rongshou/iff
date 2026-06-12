import type { CountryMatchResult } from "../types";

interface Props {
  data: CountryMatchResult;
  rankLabel: string;
}

export default function SchoolTable({ data, rankLabel }: Props) {
  const chanceColors: Record<string, string> = {
    安全: "bg-green-100 text-green-800",
    匹配: "bg-blue-100 text-blue-800",
    冲刺: "bg-amber-100 text-amber-800",
    彩票: "bg-red-100 text-red-800",
  };

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b bg-gray-50">
            <th className="text-left p-2 font-semibold">学校</th>
            <th className="text-right p-2 font-semibold">{rankLabel}</th>
            <th className="text-right p-2 font-semibold">案例数</th>
            <th className="text-right p-2 font-semibold">GPA 范围</th>
            <th className="text-right p-2 font-semibold">录取中位GPA</th>
            <th className="text-center p-2 font-semibold">录取概率</th>
            <th className="text-left p-2 font-semibold">专业</th>
          </tr>
        </thead>
        <tbody>
          {data.schools.map((s, i) => {
            const label = s.admission_chance || (s.meets_requirement ? "可达" : "冲刺");
            const color = chanceColors[label] || "bg-gray-100 text-gray-600";
            return (
            <tr key={i} className="border-b hover:bg-gray-50">
              <td className="p-2 font-medium">{s.name}</td>
              <td className="p-2 text-right">{s.qs_rank ?? s.usnews_rank ?? "-"}</td>
              <td className="p-2 text-right">{s.matched_cases}</td>
              <td className="p-2 text-right">
                {s.gpa_min !== null ? `${s.gpa_min}-${s.gpa_max}` : "-"}
              </td>
              <td className="p-2 text-right">
                {s.p50_reference !== null ? `${s.p50_reference}分` : "-"}
              </td>
              <td className="p-2 text-center">
                <span className={`px-2 py-0.5 rounded text-xs font-medium ${color}`}>
                  {label}
                </span>
              </td>
              <td className="p-2 text-gray-500">{s.majors.join(", ") || "-"}</td>
            </tr>
          )})}
        </tbody>
      </table>
    </div>
  );
}
