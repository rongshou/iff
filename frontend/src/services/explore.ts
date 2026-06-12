import type { MBTIType, MBTIMajorResult, TimelinePhase } from "../types";

const API_BASE = "http://localhost:3470/api";
const MBTI_QUESTIONS = [
  { id: 1, text: "在社交场合，你通常", options: [{ label: "与很多人交流让我精力充沛", value: "E" }, { label: "更喜欢与少数密友深入交谈", value: "I" }] },
  { id: 2, text: "做决定时，你更依赖", options: [{ label: "逻辑分析和客观事实", value: "T" }, { label: "个人价值观和他人感受", value: "F" }] },
  { id: 3, text: "你对未来更倾向于", options: [{ label: "制定详细计划并按部就班", value: "J" }, { label: "保持灵活，随遇而安", value: "P" }] },
  { id: 4, text: "获取信息时，你更喜欢", options: [{ label: "关注具体事实和细节", value: "S" }, { label: "关注整体模式和大局", value: "N" }] },
  { id: 5, text: "工作中你更喜欢", options: [{ label: "专注完成一个任务再开始下一个", value: "J" }, { label: "同时进行多个任务，灵活切换", value: "P" }] },
  { id: 6, text: "学习新事物时，你更倾向于", options: [{ label: "通过实际动手操作来学习", value: "S" }, { label: "先理解理论框架再实践", value: "N" }] },
  { id: 7, text: "与朋友产生分歧时，你通常", options: [{ label: "先分析谁对谁错，讲道理", value: "T" }, { label: "先安抚情绪，维护关系", value: "F" }] },
  { id: 8, text: "周末你更喜欢的活动是", options: [{ label: "参加聚会或集体活动", value: "E" }, { label: "一个人看书/看电影/散步", value: "I" }] },
] as const;

function calculateMBTI(answers: Record<number, string>): string {
  const scores: Record<string, number> = {};
  for (const v of Object.values(answers)) {
    scores[v] = (scores[v] || 0) + 1;
  }
  const e = (scores["E"] || 0) >= (scores["I"] || 0) ? "E" : "I";
  const s = (scores["S"] || 0) >= (scores["N"] || 0) ? "S" : "N";
  const t = (scores["T"] || 0) >= (scores["F"] || 0) ? "T" : "F";
  const j = (scores["J"] || 0) >= (scores["P"] || 0) ? "J" : "P";
  return e + s + t + j;
}

export async function fetchMBTIMajors(mbti: string): Promise<MBTIMajorResult> {
  const res = await fetch(`${API_BASE}/mbti/majors?mbti=${mbti}`);
  if (!res.ok) throw new Error("获取失败");
  return res.json();
}

export async function fetchMBTITypes(): Promise<MBTIType[]> {
  const res = await fetch(`${API_BASE}/mbti/types`);
  const data = await res.json();
  return data.types;
}

export async function fetchTimeline(studyLevel: string): Promise<TimelinePhase[]> {
  const res = await fetch(`${API_BASE}/timeline/plan?study_level=${studyLevel}`);
  const data = await res.json();
  return data.phases;
}

export { MBTI_QUESTIONS, calculateMBTI };
