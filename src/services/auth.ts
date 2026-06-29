/**
 * 本地授权管理 — 基于用户名+授权码验证
 * 默认授权码: 88888888
 */
import { loadProfile, saveProfile } from "./profile";

const AUTH_KEY = "iff_auth";
const DEFAULT_AUTH_CODE = "88888888";

export interface AuthSession {
  loggedIn: boolean;
  username: string;
  timestamp: number;
}

export function login(username: string, code: string): { ok: boolean; error?: string } {
  const trimmedUser = username.trim();
  const trimmedCode = code.trim();

  if (!trimmedUser) return { ok: false, error: "请输入用户名" };
  if (!trimmedCode) return { ok: false, error: "请输入授权码" };

  const profile = loadProfile();

  // 首次使用或旧档案缺少用户名 → 自动注册/补全
  if (!profile || !profile.username) {
    if (trimmedCode !== DEFAULT_AUTH_CODE) {
      return { ok: false, error: "授权码不正确，请使用默认授权码 88888888" };
    }
    saveProfile({ username: trimmedUser, auth_code: profile?.auth_code || DEFAULT_AUTH_CODE });
    const session: AuthSession = { loggedIn: true, username: trimmedUser, timestamp: Date.now() };
    localStorage.setItem(AUTH_KEY, JSON.stringify(session));
    return { ok: true };
  }

  // 已有完整档案 → 正常验证
  const validUsername = profile.username;
  const validCode = profile.auth_code || DEFAULT_AUTH_CODE;

  if (trimmedUser !== validUsername) return { ok: false, error: "用户名不正确" };
  if (trimmedCode !== validCode) return { ok: false, error: "授权码不正确" };

  const session: AuthSession = {
    loggedIn: true,
    username: trimmedUser,
    timestamp: Date.now(),
  };
  localStorage.setItem(AUTH_KEY, JSON.stringify(session));
  return { ok: true };
}

export function logout(): void {
  localStorage.removeItem(AUTH_KEY);
}

export function isAuthenticated(): boolean {
  try {
    const raw = localStorage.getItem(AUTH_KEY);
    if (!raw) return false;
    const data: AuthSession = JSON.parse(raw);
    return data.loggedIn === true;
  } catch {
    return false;
  }
}

export function getAuthUsername(): string {
  try {
    const raw = localStorage.getItem(AUTH_KEY);
    if (!raw) return "";
    const data: AuthSession = JSON.parse(raw);
    return data.username || "";
  } catch {
    return "";
  }
}
