import { useState, useEffect } from "react";
import {
  fetchNewsCategories,
  fetchNewsArticles,
  type NewsCategory,
  type NewsArticle,
} from "../services/api";

export default function NewsPage() {
  const [categories, setCategories] = useState<NewsCategory[]>([]);
  const [articles, setArticles] = useState<NewsArticle[]>([]);
  const [total, setTotal] = useState(0);
  const [selectedCat, setSelectedCat] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const pageSize = 20;

  useEffect(() => {
    setLoading(true);
    setError(null);
    fetchNewsCategories()
      .then((cats) => {
        setCategories(cats);
        return fetchNewsArticles(selectedCat ?? undefined, page, pageSize);
      })
      .then((res) => {
        setArticles(res.articles);
        setTotal(res.total);
      })
      .catch((e: any) => setError(e?.message || "加载失败"))
      .finally(() => setLoading(false));
  }, [selectedCat, page]);

  return (
    <div className="min-h-screen bg-gray-50 pb-12">
      {/* 头部 */}
      <div style={{ marginTop: "24px", padding: "20px", background: "#fff", borderBottom: "1px solid #eee" }}>
        <h1 style={{ fontSize: "20px", fontWeight: "bold", color: "#1a1a1a", marginBottom: "4px" }}>留学资讯</h1>
        <p style={{ fontSize: "13px", color: "#888" }}>共 {total} 篇</p>
      </div>

      {/* 分类筛选 */}
      {categories.length > 0 && (
        <div style={{ padding: "12px 20px", display: "flex", gap: "8px", flexWrap: "wrap", background: "#fff" }}>
          <button
            onClick={() => { setSelectedCat(null); setPage(1); }}
            style={{
              padding: "4px 12px",
              borderRadius: "16px",
              fontSize: "13px",
              border: selectedCat === null ? "1px solid #6366f1" : "1px solid #ddd",
              background: selectedCat === null ? "#eef2ff" : "#fff",
              color: selectedCat === null ? "#4f46e5" : "#666",
              cursor: "pointer",
            }}
          >
            全部
          </button>
          {categories.map((cat) => (
            <button
              key={cat.name}
              onClick={() => { setSelectedCat(cat.name); setPage(1); }}
              style={{
                padding: "4px 12px",
                borderRadius: "16px",
                fontSize: "13px",
                border: selectedCat === cat.name ? "1px solid #6366f1" : "1px solid #ddd",
                background: selectedCat === cat.name ? "#eef2ff" : "#fff",
                color: selectedCat === cat.name ? "#4f46e5" : "#666",
                cursor: "pointer",
              }}
            >
              {cat.name} ({cat.count})
            </button>
          ))}
        </div>
      )}

      {/* 文章列表 */}
      <div style={{ padding: "20px", maxWidth: "800px", margin: "0 auto" }}>
        {loading && articles.length === 0 && (
          <p style={{ textAlign: "center", color: "#999", padding: "40px 0" }}>加载中...</p>
        )}

        {!loading && articles.length === 0 && (
          <p style={{ textAlign: "center", color: "#999", padding: "40px 0" }}>暂无文章</p>
        )}

        {articles.map((article) => (
          <div
            key={article.id}
            style={{
              background: "#fff",
              borderRadius: "8px",
              padding: "16px",
              marginBottom: "12px",
              border: "1px solid #eee",
              cursor: "pointer",
            }}
            onClick={() => article.url && window.open(article.url, "_blank")}
          >
            {article.cover && (
              <img
                src={article.cover}
                alt={article.title}
                style={{ width: "100%", height: "160px", objectFit: "cover", borderRadius: "6px", marginBottom: "10px" }}
              />
            )}
            <h3 style={{ fontSize: "15px", fontWeight: "bold", color: "#1a1a1a", marginBottom: "6px", lineHeight: "1.4" }}>
              {article.title}
            </h3>
            {article.summary && (
              <p style={{ fontSize: "13px", color: "#666", lineHeight: "1.5", marginBottom: "8px" }}>
                {article.summary.length > 100 ? article.summary.slice(0, 100) + "..." : article.summary}
              </p>
            )}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              {article.category && (
                <span style={{ fontSize: "12px", color: "#8b5cf6", background: "#f3f0ff", padding: "2px 8px", borderRadius: "10px" }}>
                  {article.category}
                </span>
              )}
              <span style={{ fontSize: "12px", color: "#999" }}>
                {article.publish_time ? new Date(article.publish_time * 1000).toLocaleDateString("zh-CN") : ""}
              </span>
            </div>
          </div>
        ))}

        {/* 分页 */}
        {total > pageSize && (
          <div style={{ display: "flex", justifyContent: "center", gap: "8px", marginTop: "20px" }}>
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              style={{
                padding: "6px 16px",
                borderRadius: "6px",
                border: "1px solid #ddd",
                background: page <= 1 ? "#f5f5f5" : "#fff",
                color: page <= 1 ? "#ccc" : "#333",
                cursor: page <= 1 ? "not-allowed" : "pointer",
              }}
            >
              上一页
            </button>
            <span style={{ padding: "6px 12px", color: "#666", fontSize: "13px" }}>
              第 {page} / {Math.ceil(total / pageSize)} 页
            </span>
            <button
              onClick={() => setPage((p) => p + 1)}
              disabled={page >= Math.ceil(total / pageSize)}
              style={{
                padding: "6px 16px",
                borderRadius: "6px",
                border: "1px solid #ddd",
                background: page >= Math.ceil(total / pageSize) ? "#f5f5f5" : "#fff",
                color: page >= Math.ceil(total / pageSize) ? "#ccc" : "#333",
                cursor: page >= Math.ceil(total / pageSize) ? "not-allowed" : "pointer",
              }}
            >
              下一页
            </button>
          </div>
        )}
      </div>
    </div>
  );
}