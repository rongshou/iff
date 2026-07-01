import { create } from "zustand";
import type { ProfileData } from "../services/profile";
import { loadProfile, saveProfile } from "../services/profile";

interface ProfileStore {
  profile: ProfileData | null;
  loaded: boolean;

  load: () => void;
  update: (data: Partial<ProfileData>) => ProfileData;
  setProfileField: (key: string, value: unknown) => void;
}

export const useProfileStore = create<ProfileStore>((set, _get) => ({
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
    set((state) => {
      if (state.profile) {
        return { profile: { ...state.profile, [key]: value } };
      }
      const initial: Partial<ProfileData> & { updated_at: string } = { [key]: value, updated_at: "" };
      return { profile: initial as ProfileData };
    }),
}));
