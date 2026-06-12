import type { RecommendRequest, RecommendResult } from "../types";

const API_BASE = "http://localhost:3470/api";

export async function fetchRecommend(
  data: RecommendRequest
): Promise<RecommendResult> {
  const res = await fetch(`${API_BASE}/recommend`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "请求失败");
  }
  return res.json();
}

export async function fetchHealth(): Promise<{ status: string; version: string }> {
  const res = await fetch(`${API_BASE}/health`);
  return res.json();
}

export interface NewsCategory {
  name: string;
  count: number;
}

export interface NewsArticle {
  id: string;
  title: string;
  pic_url: string | null;
  url: string;
  description: string | null;
  publish_time: number;
  publish_date: string;
  category?: string;
}

export interface NewsResponse {
  articles: NewsArticle[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export async function fetchNewsCategories(): Promise<NewsCategory[]> {
  const res = await fetch(`${API_BASE}/news/categories`);
  if (!res.ok) throw new Error("获取分类失败");
  return res.json();
}

export async function fetchNewsArticles(
  category?: string,
  page: number = 1,
  pageSize: number = 20
): Promise<NewsResponse> {
  const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
  if (category) params.set("category", category);
  const res = await fetch(`${API_BASE}/news/articles?${params}`);
  if (!res.ok) throw new Error("获取文章失败");
  return res.json();
}

export async function fetchLatestNews(limit: number = 5): Promise<NewsArticle[]> {
  const res = await fetch(`${API_BASE}/news/latest?limit=${limit}`);
  if (!res.ok) throw new Error("获取最新文章失败");
  return res.json();
}
