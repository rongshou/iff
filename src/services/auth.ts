/**
 * 本地授权管理 — 基于用户名+授权码验证
 *
 * TODO(security): auth_code 目前保存在 localStorage，可被 XSS 读取。
 * 更安全的方案是改用 httpOnly + Secure + SameSite cookie 由后端下发会话，
 * 但这需要后端会话支持，超出本次改动范围。
 */
import { loadProfile, saveProfile } from "./profile";

const AUTH_KEY = "iff_auth";
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
    try {
      localStorage.setItem(AUTH_KEY, JSON.stringify(session));
    } catch (e) {
      console.error("Failed to save auth session:", e);
    }
    return { ok: true };
  }

  // 已有档案 → 正常验证绑定的用户名和授权码
  const validUsername = profile.username;
  const validCode = profile.auth_code;

  if (!validCode) return { ok: false, error: "授权码未绑定，请联系管理员" };
  if (trimmedUser !== validUsername) return { ok: false, error: "用户名不正确" };
  if (trimmedCode !== validCode) return { ok: false, error: "授权码不正确" };

  const session: AuthSession = {
    loggedIn: true,
    username: trimmedUser,
    timestamp: Date.now(),
  };
  try {
    localStorage.setItem(AUTH_KEY, JSON.stringify(session));
  } catch (e) {
    console.error("Failed to save auth session:", e);
  }
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

/**
 * 获取当前用户的授权码，用于 X-Auth-Code 请求头。
 */
export function getAuthCode(): string {
  try {
    const raw = localStorage.getItem("iff_profile");
    if (!raw) return "";
    const profile = JSON.parse(raw);
    return profile.auth_code || "";
  } catch {
    return "";
  }
}

/**
 * 获取或创建匿名试用 ID（iff_trial_id），用于未登录用户的试用额度追踪。
 *
 * 首次读取时若 localStorage 中不存在则就地生成并持久化，保证每个浏览器
 * 只有一个稳定 ID。后端通过 X-Trial-Id 请求头识别试用用户。
 */
export function getTrialId(): string {
  try {
    let id = localStorage.getItem("iff_trial_id");
    if (!id) {
      id = crypto.randomUUID();
      localStorage.setItem("iff_trial_id", id);
    }
    return id;
  } catch {
    return "";
  }
}

/**
 * 生成包含授权码的请求头（X-Auth-Code），供所有需认证的 API 调用使用。
 *
 * 始终返回带 X-Auth-Code 键的对象（即便值为空），防止 Vite/ESBuild
 * 在 production build 中因空对象展开优化将 auth header 整条剥离。
 *
 * 同时附带 X-Trial-Id：未登录用户靠它走试用额度，已登录用户的后端
 * 会优先校验 X-Auth-Code 而忽略试用 ID，因此始终发送是安全的。
 */
export function getAuthHeaders(): Record<string, string> {
  const code = getAuthCode();
  const trialId = getTrialId();
  return { "X-Auth-Code": code, "X-Trial-Id": trialId };
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
