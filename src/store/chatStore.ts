import { create } from "zustand";

interface ChatStore {
  loading: boolean;
  error: string | null;
  collectedInfo: Record<string, Record<string, string>>;

  setLoading: (v: boolean) => void;
  setError: (v: string | null) => void;
  setCollectedInfo: (v: Record<string, Record<string, string>> | ((prev: Record<string, Record<string, string>>) => Record<string, Record<string, string>>)) => void;
}

const initialState = {
  loading: false,
  error: null,
  collectedInfo: {},
};

export const useChatStore = create<ChatStore>((set) => ({
  ...initialState,

  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  setCollectedInfo: (v) =>
    set((s) => ({
      collectedInfo: typeof v === "function" ? v(s.collectedInfo) : v,
    })),
}));
