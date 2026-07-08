/**
 * Step1BasicInfo - 学生基础信息表单（sub-3.2）
 *
 * 迁移自 legacy/app.js 的 renderStep1() + nextStep1()。
 * 字段：姓名 / 性别 / 出生年月日时 / 当前学段
 *
 * 实现：
 * - 本地草稿 draft（输入时即时更新，避免每次按键都触发全局 setState）
 * - 点"下一步"时校验 → 提交到全局 state → 切到 step 2
 */

import { useState } from "react";
import { useTianshu } from "./TianshuContext";
import type { Student } from "./types";

const GRADES = ["初中", "高一", "高二", "高三", "本科", "研究生", "已毕业"] as const;

export default function Step1BasicInfo() {
  const { state, setState, goNext } = useTianshu();
  const [draft, setDraft] = useState<Student>(state.student);

  function update<K extends keyof Student>(key: K, value: Student[K]) {
    setDraft((d) => ({ ...d, [key]: value }));
  }

  function handleNext() {
    // 校验
    if (!draft.name.trim()) {
      alert("请填写姓名");
      return;
    }
    if (draft.birthYear < 1900 || draft.birthYear > 2025) {
      alert("出生年范围 1900-2025");
      return;
    }
    if (draft.birthMonth < 1 || draft.birthMonth > 12) {
      alert("月份范围 1-12");
      return;
    }
    if (draft.birthDay < 1 || draft.birthDay > 31) {
      alert("日期范围 1-31");
      return;
    }
    if (draft.birthHour < 0 || draft.birthHour > 23) {
      alert("时辰范围 0-23");
      return;
    }

    // 提交到全局 state
    setState({ student: draft });
    // 切到下一步
    goNext();
  }

  return (
    <div className="step-card-placeholder">
      <div className="step-header">
        <span className="step-num">1/5</span>
        <h2>📝 学生基础信息</h2>
      </div>

      <div className="form-grid">
        <label className="form-field">
          <span className="form-label">姓名</span>
          <input
            type="text"
            value={draft.name}
            onChange={(e) => update("name", e.target.value)}
            placeholder="例如:林小满"
            className="form-input"
          />
        </label>

        <label className="form-field">
          <span className="form-label">性别</span>
          <select
            value={draft.gender}
            onChange={(e) => update("gender", e.target.value as "男" | "女")}
            className="form-input"
          >
            <option value="男">男</option>
            <option value="女">女</option>
          </select>
        </label>

        <label className="form-field">
          <span className="form-label">出生年</span>
          <input
            type="number"
            value={draft.birthYear}
            onChange={(e) => update("birthYear", parseInt(e.target.value) || 2010)}
            min={1990}
            max={2025}
            className="form-input"
          />
        </label>

        <label className="form-field">
          <span className="form-label">出生月</span>
          <input
            type="number"
            value={draft.birthMonth}
            onChange={(e) => update("birthMonth", parseInt(e.target.value) || 1)}
            min={1}
            max={12}
            className="form-input"
          />
        </label>

        <label className="form-field">
          <span className="form-label">出生日</span>
          <input
            type="number"
            value={draft.birthDay}
            onChange={(e) => update("birthDay", parseInt(e.target.value) || 1)}
            min={1}
            max={31}
            className="form-input"
          />
        </label>

        <label className="form-field">
          <span className="form-label">出生时辰 (0-23)</span>
          <input
            type="number"
            value={draft.birthHour}
            onChange={(e) => update("birthHour", parseInt(e.target.value) || 0)}
            min={0}
            max={23}
            className="form-input"
          />
        </label>

        <label className="form-field form-field-full">
          <span className="form-label">当前学段</span>
          <select
            value={draft.grade}
            onChange={(e) => update("grade", e.target.value)}
            className="form-input"
          >
            {GRADES.map((g) => (
              <option key={g} value={g}>
                {g}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="step-actions">
        <a href="/tianshu/legacy/" className="btn-secondary">
          ← 访问旧版测评
        </a>
        <button onClick={handleNext} className="btn-primary">
          下一步 →
        </button>
      </div>
    </div>
  );
}