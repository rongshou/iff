import { create } from "zustand";
import type { MBTIMajorResult, TimelinePhase } from "../types";

interface ExploreStore {
  answers: Record<number, string>;
  mbtiResult: MBTIMajorResult | null;
  timeline: TimelinePhase[];
  studyLevel: string;
  loading: boolean;

  setAnswers: (v: Record<number, string>) => void;
  setMbtiResult: (v: MBTIMajorResult | null) => void;
  setTimeline: (v: TimelinePhase[]) => void;
  setStudyLevel: (v: string) => void;
  setLoading: (v: boolean) => void;
  reset: () => void;
}

const initialState = {
  answers: {},
  mbtiResult: null,
  timeline: [],
  studyLevel: "硕士",
  loading: false,
};

export const useExploreStore = create<ExploreStore>((set) => ({
  ...initialState,

  setAnswers: (v) => set({ answers: v }),
  setMbtiResult: (v) => set({ mbtiResult: v }),
  setTimeline: (v) => set({ timeline: v }),
  setStudyLevel: (v) => set({ studyLevel: v }),
  setLoading: (v) => set({ loading: v }),
  reset: () => set(initialState),
}));
