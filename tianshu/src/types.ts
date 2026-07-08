/**
 * 天枢测评 - 类型定义
 *
 * 旧 app.js 的 state 对象结构迁移到 TypeScript。
 * 后续 sub-step 会在这个基础上扩展。
 */

export interface Student {
  name: string;
  gender: "男" | "女";
  birthYear: number;
  birthMonth: number;
  birthDay: number;
  birthHour: number;
  grade: string;
}

export interface HollandScores {
  R: number;
  I: number;
  A: number;
  S: number;
  E: number;
  C: number;
}

export interface TianshuState {
  step: 1 | 2 | 3 | 4 | 5;
  student: Student;
  mbtiType: string;
  hollandScores: HollandScores;
  results: any | null; // 报告结果（sub-3.6 详细化）
}

export interface TianshuContextValue {
  state: TianshuState;
  setState: (updater: Partial<TianshuState> | ((s: TianshuState) => Partial<TianshuState>)) => void;
  goNext: () => void;
  goPrev: () => void;
  goTo: (step: 1 | 2 | 3 | 4 | 5) => void;
}

export const DEFAULT_STATE: TianshuState = {
  step: 1,
  student: {
    name: "",
    gender: "男",
    birthYear: 2010,
    birthMonth: 5,
    birthDay: 15,
    birthHour: 14,
    grade: "高一",
  },
  mbtiType: "INTJ-A",
  hollandScores: { R: 30, I: 85, A: 70, S: 65, E: 40, C: 35 },
  results: null,
};

// 全局对象（由 index.html 中的 <script> 标签加载）
export const TianShuBazi = (window as any).TianShuBazi;
export const TianShuData = (window as any).TianShuData;
export const TianShuEngine = (window as any).TianShuEngine;
export const TianShuBeidou = (window as any).TianShuBeidou;