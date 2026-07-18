/**
 * 学校简称映射的单一数据源（前端缓存层）。
 *
 * 数据从后端 `/api/school/abbreviations` 拉取，返回结构为
 * `Record<全称, 简称[]>`。本模块提供：
 *  - `loadSchoolAbbreviations()`：异步加载并缓存（首次调用触发 fetch，
 *    后续调用复用同一 Promise / 缓存）。
 *  - `getSchoolAbbrevMap()`：返回 `简称 → 全称` 的反向映射（chat 页面
 *    简称匹配函数使用的形状）。缓存未就绪时会触发一次 fetch。
 *
 * App.tsx 启动时即 fire-and-forget 调用 `loadSchoolAbbreviations()`，
 * 正常情况下用户进入 Chat 页面时缓存已就绪。
 */

import { getAuthHeaders } from "./auth";

const API_BASE = import.meta.env.VITE_API_BASE || "/api";

type AbbreviationsResponse = {
  abbreviations: Record<string, string[]>;
  total: number;
};

let cache: Record<string, string[]> | null = null;
let loadingPromise: Promise<Record<string, string[]>> | null = null;

export async function loadSchoolAbbreviations(): Promise<Record<string, string[]>> {
  if (cache) return cache;
  if (loadingPromise) return loadingPromise;

  loadingPromise = (async () => {
    const res = await fetch(`${API_BASE}/school/abbreviations`, {
      headers: { ...getAuthHeaders() },
    });
    if (!res.ok) throw new Error("获取学校简称映射失败");
    const data: AbbreviationsResponse = await res.json();
    cache = data.abbreviations;
    return cache;
  })();

  try {
    const result = await loadingPromise;
    return result;
  } catch {
    // loadingPromise was cleared by finally; no-op — caller gets empty map from getSchoolAbbrevMap
    throw new Error("获取学校简称映射失败");
  } finally {
    loadingPromise = null;
  }
}

/**
 * 返回 `简称 → 全称` 的映射（与原 Chat.tsx 中硬编码的 SCHOOL_ABBREV 形状一致）。
 * 缓存未就绪时会触发一次 fetch 并 await，因此调用方需在 async 上下文中使用。
 *
 * 如果加载失败（网络错误 / 认证失败），返回空映射而不是抛出异常，
 * 避免整个消息发送流程因简称映射加载失败而中断。
 */
export async function getSchoolAbbrevMap(): Promise<Record<string, string>> {
  try {
    const data = await loadSchoolAbbreviations();
    const map: Record<string, string> = {};
    for (const [full, abbrevs] of Object.entries(data)) {
      for (const abbr of abbrevs) {
        map[abbr] = full;
      }
    }
    return map;
  } catch (e) {
    console.warn("加载学校简称映射失败，将跳过简称解析:", e);
    return {};
  }
}
