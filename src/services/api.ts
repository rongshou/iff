import { getAuthHeaders } from "./auth";

const API_BASE = import.meta.env.VITE_API_BASE || "/api";

/**
 * 验证授权码是否合法（调后端校验）
 * @returns valid: true=合法, false=无效授权码
 */
export async function verifyAuthCode(authCode: string): Promise<{ valid: boolean }> {
  const res = await fetch(`${API_BASE}/verify-auth-code`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...getAuthHeaders() },
    body: JSON.stringify({ auth_code: authCode }),
  });
  if (!res.ok) {
    console.error("verifyAuthCode request failed:", res.status, res.statusText);
    return { valid: false };
  }
  return res.json();
}
