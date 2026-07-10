/**
 * 个人档案 + 查询历史 localStorage 工具
 *
 * 数据结构：
 *   iff_profile  → 用户基本信息（可编辑）+ 天枢测评结果（只读）
 *   iff_history  → 所有查询/测评记录的时间线
 */

import type { ChatMessage } from "../types";

/* ==================== 类型定义 ==================== */

export interface ProfileData {
  /** 基本信息（可编辑） */
  username?: string;
  email?: string;
  auth_code?: string;
  school?: string;
  original_major?: string;
  gpa_score?: number;
  gpa_format?: string;
  target_countries?: string[];
  study_level?: string;
  target_major?: string;
  ielts?: number | null;
  toefl?: number | null;
  gre?: number | null;

  /** 天枢测评结果（只读，从天枢同步） */
  tianshu?: TianshuData;

  updated_at: string;
}

export interface BaziData {
  yearZhu?: string;
  monthZhu?: string;
  dayZhu?: string;
  hourZhu?: string;
  dayMaster?: string;
  dayMasterWx?: string;
  xiZhong?: string[];
  yongShen?: string;
  comments?: string;
}

export interface TianshuData {
  student: {
    name: string;
    gender: string;
    birthYear: number;
    birthMonth: number;
    birthDay: number;
    birthHour: number;
    grade: string;
  };
  bazi?: BaziData;
  ziwei?: Record<string, unknown>;
  mbti?: {
    type: string;
    nick: string;
    core: string;
    strength: string;
    weakness: string;
    fitMajors?: string;
  };
  holland?: {
    scores: Record<string, number>;
    top3: string;
    codeExplain: string;
    dimensions: Record<string, { name: string; fit: string }>;
    sorted: [string, number][];
  };
  sunSign?: string | { name?: string; nameCN?: string };
  summary?: {
    tags: string[];
    summary: string;
  };
  updated_at: string;
}

export type HistoryType = "recommend" | "mbti" | "chat_session" | "tianshu_report";

export interface HistoryItem {
  id: string;
  type: HistoryType;
  system: "tianquan" | "tianshu";
  /** 当时的 profile 快照 */
  profile_snapshot?: Partial<ProfileData>;
  /** 结果数据 */
  data: unknown;
  /** 摘要（列表展示用） */
  summary: string;
  /** 子标题 */
  subtitle?: string;
  created_at: string;
}

/* ==================== Profile CRUD ==================== */

const PROFILE_KEY = "iff_profile";

export function loadProfile(): ProfileData | null {
  try {
    const raw = localStorage.getItem(PROFILE_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as ProfileData;
  } catch {
    return null;
  }
}

export function saveProfile(profile: Partial<ProfileData>): ProfileData {
  const existing = loadProfile() || {} as ProfileData;
  const merged: ProfileData = {
    ...existing,
    ...profile,
    updated_at: new Date().toISOString(),
  };
  try {
    localStorage.setItem(PROFILE_KEY, JSON.stringify(merged));
  } catch (e) {
    console.error("Failed to save profile:", e);
  }
  return merged;
}

export function clearProfile(): void {
  localStorage.removeItem(PROFILE_KEY);
}

/** 从聊天收集的信息合并到 profile */
export function mergeChatInfo(info: Record<string, string>): void {
  const mapped: Partial<ProfileData> = {};
  if (info.school) mapped.school = info.school;
  if (info.major && !/^(时间|安排|规划|怎么|如何|推荐|建议|什么|哪些|哪所|是否|需要|可以|准备|开始|申请|选校|这|那|方向|留学|国家|学校|大学|学院|怎么样)/.test(info.major)) {
    mapped.original_major = info.major;
  }
  if (info.gpa) {
    const parsed = parseGpaInput(info.gpa);
    if (parsed) {
      mapped.gpa_score = parsed.score;
      mapped.gpa_format = parsed.format;
    }
  }
  if (info.targetCountry) mapped.target_countries = [info.targetCountry];
  if (info.targetMajor && !["其他","其它","不限","不确定","还没想好","未定"].includes(info.targetMajor)) {
    mapped.target_major = info.targetMajor;
  }
  if (Object.keys(mapped).length > 0) {
    saveProfile(mapped);
  }
}

function parseGpaInput(text: string): { score: number; format: string } | null {
  const m = text.match(/([\d.]+)\s*\/\s*([\d.]+)/);
  if (m) {
    const score = parseFloat(m[1]);
    const total = parseFloat(m[2]);
    if (total === 4) return { score, format: "4分制" };
    if (total === 5) return { score, format: "5分制" };
    if (total === 100) return { score, format: "100分制" };
    return { score, format: `${total}分制` };
  }
  const simple = parseFloat(text);
  if (isNaN(simple)) return null;
  // 启发式判断
  if (simple > 10) return { score: simple, format: "100分制" };
  return { score: simple, format: "4分制" };
}

/* ==================== History CRUD ==================== */

const HISTORY_KEY = "iff_history";
const MAX_HISTORY = 200;

export function loadHistory(): HistoryItem[] {
  try {
    const raw = localStorage.getItem(HISTORY_KEY);
    if (!raw) return [];
    return JSON.parse(raw) as HistoryItem[];
  } catch {
    return [];
  }
}

export function addHistoryItem(item: Omit<HistoryItem, "id" | "created_at">): HistoryItem {
  const history = loadHistory();
  const newItem: HistoryItem = {
    ...item,
    id: generateId(),
    created_at: new Date().toISOString(),
  };
  history.unshift(newItem);
  // 限制最大数量
  if (history.length > MAX_HISTORY) {
    history.length = MAX_HISTORY;
  }
  try {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
  } catch (e) {
    console.error("Failed to save history:", e);
  }
  return newItem;
}

export function deleteHistoryItem(id: string): void {
  const history = loadHistory();
  const filtered = history.filter((h) => h.id !== id);
  try {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(filtered));
  } catch (e) {
    console.error("Failed to save history:", e);
  }
}

export function clearHistory(): void {
  localStorage.removeItem(HISTORY_KEY);
}

/* ==================== 工具 ==================== */

function generateId(): string {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
}

/** 创建对话历史记录 */
export function createChatHistoryItem(
  scene: string,
  messages: ChatMessage[],
): Omit<HistoryItem, "id" | "created_at"> {
  const lastMsg = messages[messages.length - 1];
  return {
    type: "chat_session",
    system: "tianquan",
    data: { scene, messages },
    summary: `${{ school: "选校", essay: "文书", visa: "签证" }[scene] || scene} · 共 ${messages.length} 轮`,
    subtitle: lastMsg ? lastMsg.content.slice(0, 40) : "",
  };
}
