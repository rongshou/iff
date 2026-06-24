import { useState } from "react";
import type { RecommendRequest } from "../types";

const COUNTRIES = [
  "英国", "美国", "澳大利亚", "中国香港", "新加坡", "加拿大",
  "日本", "韩国", "中国澳门", "新西兰", "德国", "法国",
  "荷兰", "爱尔兰", "瑞士", "瑞典", "丹麦", "意大利", "西班牙", "马来西亚",
];

const GPA_FORMATS = ["4分制", "5分制", "百分制", "7分制", "9分制"];
const STUDY_LEVELS = ["本科", "硕士", "博士"];

interface Props {
  onSubmit: (data: RecommendRequest) => void;
  loading: boolean;
}

export default function RecommendForm({ onSubmit, loading }: Props) {
  const [countries, setCountries] = useState<string[]>(["英国"]);
  const [gpaScore, setGpaScore] = useState("3.5");
  const [gpaFormat, setGpaFormat] = useState("4分制");
  const [studyLevel, setStudyLevel] = useState("硕士");
  const [targetMajor, setTargetMajor] = useState("");
  const [originalMajor, setOriginalMajor] = useState("");
  const [undergradSchool, setUndergradSchool] = useState("");

  const toggleCountry = (c: string) => {
    setCountries((prev) =>
      prev.includes(c) ? prev.filter((x) => x !== c) : [...prev, c]
    );
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (countries.length === 0) return;
    onSubmit({
      target_countries: countries,
      gpa_score: parseFloat(gpaScore) || 0,
      gpa_format: gpaFormat,
      study_level: studyLevel,
      target_major: targetMajor || undefined,
      original_major: originalMajor || undefined,
      undergraduate_school: undergradSchool || undefined,
    });
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="bg-white rounded-xl shadow-sm border p-6 space-y-4"
    >
      <div>
        <label className="block text-sm font-semibold text-gray-700 mb-2">
          目标国家/地区
        </label>
        <div className="flex flex-wrap gap-2">
          {COUNTRIES.map((c) => (
            <button
              key={c}
              type="button"
              onClick={() => toggleCountry(c)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                countries.includes(c)
                  ? "bg-indigo-600 text-white"
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              }`}
            >
              {c}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-1">
            GPA
          </label>
          <input
            type="number"
            step="0.01"
            value={gpaScore}
            onChange={(e) => setGpaScore(e.target.value)}
            className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-1">
            GPA 体系
          </label>
          <select
            value={gpaFormat}
            onChange={(e) => setGpaFormat(e.target.value)}
            className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
          >
            {GPA_FORMATS.map((f) => (
              <option key={f} value={f}>{f}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-1">
            学位阶段
          </label>
          <select
            value={studyLevel}
            onChange={(e) => setStudyLevel(e.target.value)}
            className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
          >
            {STUDY_LEVELS.map((l) => (
              <option key={l} value={l}>{l}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-1">
            目标专业 <span className="text-gray-400 font-normal">(可选)</span>
          </label>
          <input
            type="text"
            value={targetMajor}
            onChange={(e) => setTargetMajor(e.target.value)}
            placeholder="如：计算机"
            className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
          />
        </div>
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-1">
            本科专业 <span className="text-gray-400 font-normal">(可选)</span>
          </label>
          <input
            type="text"
            value={originalMajor}
            onChange={(e) => setOriginalMajor(e.target.value)}
            placeholder="如：软件工程"
            className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
          />
        </div>
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-1">
            本科/高中学校 <span className="text-gray-400 font-normal">(可选)</span>
          </label>
          <input
            type="text"
            value={undergradSchool}
            onChange={(e) => setUndergradSchool(e.target.value)}
            placeholder="如：北京大学"
            className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
          />
        </div>
      </div>

      <button
        type="submit"
        disabled={loading || countries.length === 0}
        className="w-full py-3 bg-indigo-600 text-white rounded-lg font-semibold hover:bg-indigo-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
      >
        {loading ? "分析中..." : "查询匹配案例"}
      </button>
    </form>
  );
}
