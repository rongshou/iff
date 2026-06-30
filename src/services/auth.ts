/**
 * 本地授权管理 — 基于用户名+授权码验证
 * 默认授权码: 88888888
 */
import { loadProfile, saveProfile } from "./profile";

const AUTH_KEY = "iff_auth";
const DEFAULT_AUTH_CODE = "88888888";
const SESSION_MAX_AGE_MS = 7 * 24 * 60 * 60 * 1000; // 1 周

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

  // 首次使用或旧档案缺少用户名 → 绑定用户名和授权码
  if (!profile || !profile.username) {
    saveProfile({ username: trimmedUser, auth_code: trimmedCode });
    const session: AuthSession = { loggedIn: true, username: trimmedUser, timestamp: Date.now() };
    localStorage.setItem(AUTH_KEY, JSON.stringify(session));
    return { ok: true };
  }

  // 已有档案 → 正常验证绑定的用户名和授权码
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
    if (data.loggedIn !== true) return false;
    // 登录状态超过 1 周则自动过期
    if (Date.now() - data.timestamp > SESSION_MAX_AGE_MS) {
      localStorage.removeItem(AUTH_KEY);
      return false;
    }
    return true;
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
