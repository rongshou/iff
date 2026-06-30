import { create } from "zustand";
import type { ProfileData } from "../services/profile";
import { loadProfile, saveProfile, clearProfile } from "../services/profile";

interface ProfileStore {
  profile: ProfileData | null;
  loaded: boolean;

  load: () => void;
  update: (data: Partial<ProfileData>) => ProfileData;
  setProfileField: (key: string, value: unknown) => void;
  clear: () => void;
}

export const useProfileStore = create<ProfileStore>((set, get) => ({
  profile: null,
  loaded: false,

  load: () => {
    const p = loadProfile();
    set({ profile: p, loaded: true });
  },

  update: (data) => {
    const merged = saveProfile(data);
    set({ profile: merged });
    return merged;
  },

  setProfileField: (key, value) =>
    set((state) => ({
      profile: state.profile
        ? { ...state.profile, [key]: value }
        : ({ [key]: value, updated_at: "" } as ProfileData),
    })),

  clear: () => {
    clearProfile();
    set({ profile: null });
  },
}));
