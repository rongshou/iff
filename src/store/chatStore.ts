import { create } from "zustand";

interface ChatStore {
  loading: boolean;
  error: string | null;
  /** { sceneId: { field: value } } — 从聊天中收集的信息 */
  collectedInfo: Record<string, Record<string, string>>;

  setLoading: (v: boolean) => void;
  setError: (v: string | null) => void;
  setCollectedInfo: (v: Record<string, Record<string, string>> | ((prev: Record<string, Record<string, string>>) => Record<string, Record<string, string>>)) => void;
  mergeCollectedInfo: (scene: string, fields: Record<string, string>) => void;
  resetChat: () => void;
}

const initialState = {
  loading: false,
  error: null,
  collectedInfo: {},
};

export const useChatStore = create<ChatStore>((set) => ({
  ...initialState,

  setLoading: (v) => set({ loading: v }),
  setError: (v) => set({ error: v }),
  setCollectedInfo: (v) =>
    set((state) => ({
      collectedInfo: typeof v === "function" ? v(state.collectedInfo) : v,
    })),

  mergeCollectedInfo: (scene, fields) =>
    set((s) => ({
      collectedInfo: {
        ...s.collectedInfo,
        [scene]: { ...(s.collectedInfo[scene] || {}), ...fields },
      },
    })),

  resetChat: () => set(initialState),
}));
