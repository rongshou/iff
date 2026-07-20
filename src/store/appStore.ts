import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { FavoriteSchool } from "../types";

export interface CrossSceneContext {
  recentSchools: string[];
}

export interface AppState {
  favorites: FavoriteSchool[];
  crossSceneContext: CrossSceneContext;
  trialUsed: boolean;

  addFavorite: (school: FavoriteSchool) => void;
  removeFavorite: (schoolName: string) => void;
  isFavorite: (schoolName: string) => boolean;
  setCrossSceneContext: (ctx: Partial<CrossSceneContext>) => void;
  clearCrossSceneContext: () => void;
  markTrialUsed: () => void;
}

const TRIAL_KEY = "iff_trial_used";

function readInitialTrialUsed(): boolean {
  try {
    return localStorage.getItem(TRIAL_KEY) === "true";
  } catch {
    return false;
  }
}

export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
      favorites: [],
      crossSceneContext: { recentSchools: [] },
      trialUsed: readInitialTrialUsed(),

      addFavorite: (school) =>
        set((s) => {
          if (s.favorites.some((f) => f.name === school.name)) return s;
          return { favorites: [...s.favorites, school] };
        }),

      removeFavorite: (schoolName) =>
        set((s) => ({
          favorites: s.favorites.filter((f) => f.name !== schoolName),
        })),

      isFavorite: (schoolName) =>
        get().favorites.some((f) => f.name === schoolName),

      setCrossSceneContext: (ctx) =>
        set((s) => ({
          crossSceneContext: { ...s.crossSceneContext, ...ctx },
        })),

      clearCrossSceneContext: () =>
        set({ crossSceneContext: { recentSchools: [] } }),

      markTrialUsed: () => {
        try {
          localStorage.setItem(TRIAL_KEY, "true");
        } catch {
          // ignore storage failures (private mode / quota)
        }
        set({ trialUsed: true });
      },
    }),
    {
      name: "iff_favorites",
      partialize: (s) => ({ favorites: s.favorites }),
    },
  ),
);