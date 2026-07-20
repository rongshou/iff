import { useState } from "react";
import type { Scene } from "../config/scenes";
import { SCENES } from "../config/scenes";
import type { SceneId } from "../config/scenes";
import type { ProfileData } from "../services/profile";
import { saveProfile } from "../services/profile";

export interface OnboardingWizardProps {
  scene: Scene;
  onSceneChange: (id: SceneId) => void;
  onComplete: () => void;
}

const COUNTRIES = ["英国", "美国", "澳洲", "加拿大", "香港", "新加坡", "欧洲", "日本", "韩国"];
const STUDY_LEVELS = ["高中", "本科", "硕士", "博士", "预科"];
const GPA_FORMATS = ["百分制", "4分制", "5分制", "7分制", "9分制", "英制百分制"];

interface WizardForm {
  gpaScore: string;
  gpaFormat: string;
  school: string;
  targetCountries: string[];
  studyLevel: string;
  targetMajor: string;
}

const INITIAL_FORM: WizardForm = {
  gpaScore: "",
  gpaFormat: "",
  school: "",
  targetCountries: [],
  studyLevel: "",
  targetMajor: "",
};

type Step = 1 | 2 | 3;

export default function OnboardingWizard({
  scene,
  onSceneChange,
  onComplete,
}: OnboardingWizardProps) {
  const [step, setStep] = useState<Step>(1);
  const [form, setForm] = useState<WizardForm>(INITIAL_FORM);

  const finish = () => {
    const profile: Partial<ProfileData> = {};
    if (form.gpaScore.trim()) {
      const n = parseFloat(form.gpaScore);
      if (!isNaN(n)) profile.gpa_score = n;
    }
    if (form.gpaFormat) profile.gpa_format = form.gpaFormat;
    if (form.school.trim()) profile.school = form.school.trim();
    if (form.targetCountries.length > 0) profile.target_countries = form.targetCountries;
    if (form.studyLevel) profile.study_level = form.studyLevel;
    if (form.targetMajor.trim()) profile.target_major = form.targetMajor.trim();
    saveProfile(profile);
    onComplete();
  };

  const skip = () => onComplete();

  const toggleCountry = (c: string) => {
    setForm((f) => ({
      ...f,
      targetCountries: f.targetCountries.includes(c)
        ? f.targetCountries.filter((x) => x !== c)
        : [...f.targetCountries, c],
    }));
  };

  return (
    <div className="min-h-full flex flex-col justify-center py-4 sm:py-6">
      <div className="mx-auto max-w-xl w-full px-3 sm:px-0">
        {/* ---------- 进度指示 ---------- */}
        <div className="flex items-center justify-center gap-2 mb-5">
          {[1, 2, 3].map((n) => (
            <div
              key={n}
              className={`h-1.5 rounded-full transition-all duration-200 ${
                n === step
                  ? "w-8 bg-indigo-500"
                  : n < step
                  ? "w-4 bg-indigo-300"
                  : "w-4 bg-slate-200"
              }`}
            />
          ))}
        </div>

        <div className="scene-card">
          {/* ---------- Step 1: 选择目标 ---------- */}
          {step === 1 && (
            <div>
              <div className="text-[11px] font-semibold text-slate-500 mb-2.5 px-1 tracking-wide">
                第 1 步 · 选择目标
              </div>
              <h2 className="text-lg sm:text-xl font-bold text-slate-900 mb-1 px-1">
                你想做什么？
              </h2>
              <p className="text-[12px] text-slate-500 mb-4 px-1">
                选一个方向，我们会为你定制快捷问题
              </p>
              <div className="sc-prompts">
                {SCENES.map((s) => {
                  const isActive = scene.id === s.id;
                  return (
                  <button
                    key={s.id}
                    onClick={() => {
                      onSceneChange(s.id);
                      setStep(2);
                    }}
                    className={`sc-prompt transition-all duration-200 ${
                      isActive
                        ? "!bg-indigo-50 !border-indigo-300 !text-indigo-700"
                        : ""
                    }`}
                  >
                    <span className="pi">{s.icon}</span>
                    <span className="flex-1">
                      <span className="block font-semibold text-slate-800">
                        {s.label}
                      </span>
                      <span className="block text-[11px] text-slate-400 mt-0.5">
                        {s.intro}
                      </span>
                    </span>
                  </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* ---------- Step 2: 填写档案 ---------- */}
          {step === 2 && (
            <div>
              <div className="text-[11px] font-semibold text-slate-500 mb-2.5 px-1 tracking-wide">
                第 2 步 · 基本信息（可选）
              </div>
              <h2 className="text-lg sm:text-xl font-bold text-slate-900 mb-4 px-1">
                填写你的档案
              </h2>

              <div className="space-y-4">
                {/* GPA + format */}
                <div>
                  <label className="block text-[12px] font-medium text-slate-600 mb-1.5 px-1">
                    GPA
                  </label>
                  <div className="flex gap-2 px-1">
                    <input
                      type="text"
                      inputMode="decimal"
                      value={form.gpaScore}
                      onChange={(e) =>
                        setForm((f) => ({ ...f, gpaScore: e.target.value }))
                      }
                      placeholder="如 82 或 3.4"
                      className="flex-1 px-3 py-2 rounded-xl border border-slate-200 bg-white text-sm text-slate-800 placeholder:text-slate-400 focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 transition-all outline-none"
                    />
                    <select
                      value={form.gpaFormat}
                      onChange={(e) =>
                        setForm((f) => ({ ...f, gpaFormat: e.target.value }))
                      }
                      className="px-3 py-2 rounded-xl border border-slate-200 bg-white text-sm text-slate-800 focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 transition-all outline-none"
                    >
                      <option value="">计分制</option>
                      {GPA_FORMATS.map((g) => (
                        <option key={g} value={g}>
                          {g}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                {/* School */}
                <div className="px-1">
                  <label className="block text-[12px] font-medium text-slate-600 mb-1.5">
                    所在学校
                  </label>
                  <input
                    type="text"
                    value={form.school}
                    onChange={(e) =>
                      setForm((f) => ({ ...f, school: e.target.value }))
                    }
                    placeholder="如 北京邮电大学"
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 bg-white text-sm text-slate-800 placeholder:text-slate-400 focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 transition-all outline-none"
                  />
                </div>

                {/* Target countries */}
                <div className="px-1">
                  <label className="block text-[12px] font-medium text-slate-600 mb-1.5">
                    目标国家 / 地区（可多选）
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {COUNTRIES.map((c) => {
                      const active = form.targetCountries.includes(c);
                      return (
                        <button
                          key={c}
                          type="button"
                          onClick={() => toggleCountry(c)}
                          className={`px-3 py-1.5 rounded-full text-[12.5px] font-medium border transition-all duration-200 ${
                            active
                              ? "bg-indigo-50 border-indigo-300 text-indigo-700"
                              : "bg-white border-slate-200 text-slate-600 hover:border-indigo-200"
                          }`}
                        >
                          {c}
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Study level */}
                <div className="px-1">
                  <label className="block text-[12px] font-medium text-slate-600 mb-1.5">
                    申请层级
                  </label>
                  <select
                    value={form.studyLevel}
                    onChange={(e) =>
                      setForm((f) => ({ ...f, studyLevel: e.target.value }))
                    }
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 bg-white text-sm text-slate-800 focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 transition-all outline-none"
                  >
                    <option value="">请选择</option>
                    {STUDY_LEVELS.map((l) => (
                      <option key={l} value={l}>
                        {l}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Target major */}
                <div className="px-1">
                  <label className="block text-[12px] font-medium text-slate-600 mb-1.5">
                    目标专业
                  </label>
                  <input
                    type="text"
                    value={form.targetMajor}
                    onChange={(e) =>
                      setForm((f) => ({ ...f, targetMajor: e.target.value }))
                    }
                    placeholder="如 计算机 / 金融"
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 bg-white text-sm text-slate-800 placeholder:text-slate-400 focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 transition-all outline-none"
                  />
                </div>
              </div>

              <div className="flex justify-between mt-5 px-1">
                <button
                  onClick={() => setStep(1)}
                  className="px-4 py-2 rounded-xl text-sm font-medium text-slate-600 bg-slate-100 hover:bg-slate-200 transition-colors"
                >
                  上一步
                </button>
                <button
                  onClick={() => setStep(3)}
                  className="btn-primary px-5 py-2 rounded-xl text-sm font-medium"
                >
                  下一步
                </button>
              </div>
            </div>
          )}

          {/* ---------- Step 3: 确认 ---------- */}
          {step === 3 && (
            <div>
              <div className="text-[11px] font-semibold text-slate-500 mb-2.5 px-1 tracking-wide">
                第 3 步 · 确认信息
              </div>
              <h2 className="text-lg sm:text-xl font-bold text-slate-900 mb-4 px-1">
                确认你的档案
              </h2>

              <dl className="space-y-2.5 px-1">
                <SummaryRow label="GPA" value={
                  form.gpaScore || form.gpaFormat
                    ? `${form.gpaScore || "—"}${form.gpaFormat ? " · " + form.gpaFormat : ""}`
                    : "—"
                } />
                <SummaryRow label="学校" value={form.school || "—"} />
                <SummaryRow
                  label="目标国家"
                  value={
                    form.targetCountries.length > 0
                      ? form.targetCountries.join("、")
                      : "—"
                  }
                />
                <SummaryRow label="申请层级" value={form.studyLevel || "—"} />
                <SummaryRow label="目标专业" value={form.targetMajor || "—"} />
              </dl>

              <p className="text-[11px] text-slate-400 mt-3 px-1">
                空着的字段可以稍后在「档案」页补充。
              </p>

              <div className="flex justify-between mt-5 px-1">
                <button
                  onClick={() => setStep(2)}
                  className="px-4 py-2 rounded-xl text-sm font-medium text-slate-600 bg-slate-100 hover:bg-slate-200 transition-colors"
                >
                  上一步
                </button>
                <button
                  onClick={finish}
                  className="btn-primary px-5 py-2 rounded-xl text-sm font-medium"
                >
                  开始选校
                </button>
              </div>
            </div>
          )}
        </div>

        {/* ---------- 跳过 ---------- */}
        <div className="text-center mt-4">
          <button
            onClick={skip}
            className="text-[12px] text-slate-400 hover:text-indigo-600 transition-colors underline-offset-2 hover:underline"
          >
            跳过，直接开始
          </button>
        </div>
      </div>
    </div>
  );
}

function SummaryRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-baseline gap-3 py-1.5 border-b border-slate-100 last:border-0">
      <dt className="text-[12px] text-slate-500 w-20 shrink-0">{label}</dt>
      <dd className="text-[13.5px] text-slate-800 font-medium flex-1">{value}</dd>
    </div>
  );
}