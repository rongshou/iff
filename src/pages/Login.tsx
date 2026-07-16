import { useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { login } from "../services/auth";
import { verifyAuthCode } from "../services/api";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [authCode, setAuthCode] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const redirectTo = searchParams.get("redirect") || "/";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!authCode.trim()) {
      setError("请输入授权码");
      return;
    }

    setLoading(true);

    // 先尝试后端验证（可选，失败不阻塞）
    try {
      const { valid } = await verifyAuthCode(authCode.trim());
      if (!valid) {
        setLoading(false);
        setError("授权码无效，请联系管理员");
        return;
      }
    } catch {
      // 后端不可达时回退到纯本地验证
      console.warn("Backend unreachable, falling back to local auth");
    }

    const result = login(username, authCode);
    setLoading(false);

    if (result.ok) {
      // 仅跨应用路径（如 /tianshu/）用 window.location 全页跳转
      // 其余路径（包括 SPA 默认 "/"）由 HashRouter navigate 处理
      const EXTERNAL_PREFIXES: string[] = ["/tianshu/"];
      if (EXTERNAL_PREFIXES.some((p) => redirectTo.startsWith(p))) {
        window.location.href = redirectTo;
      } else {
        navigate(redirectTo, { replace: true });
      }
    } else {
      setError(result.error || "登录失败");
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50 flex items-center justify-center px-4 py-6 sm:py-8">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="text-center mb-6 sm:mb-8">
          <div
            className="inline-flex items-center justify-center rounded-2xl font-bold shadow-lg mb-3 sm:mb-4"
            style={{
              width: 64,
              height: 64,
              fontSize: 18,
              letterSpacing: "0.05em",
              color: "#ffffff",
              background: "linear-gradient(135deg, #6366f1 0%, #a855f7 50%, #ec4899 100%)",
              boxShadow: "0 12px 28px -8px rgba(99,102,241,0.45)",
              textShadow: "0 1px 2px rgba(0,0,0,0.18)",
            }}
          >
            Iff
          </div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 leading-tight px-2">
            AI 留学规划与生涯规划工具
          </h1>
          <p
            className="hidden sm:block"
            style={{
              marginTop: 6,
              fontSize: 11,
              letterSpacing: "0.08em",
              color: "#6366f1",
              fontWeight: 600,
            }}
          >
            INTELLIGENT FOREIGN EDUCATION FRONTIER
          </p>
          <p className="text-[12px] sm:text-[13px] text-slate-500 mt-2 sm:mt-3 px-2">
            首次登录即绑定，后续使用相同凭据登录
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="bg-white rounded-2xl shadow-sm border border-slate-200 p-5 sm:p-6 space-y-3.5 sm:space-y-4">
          <label className="flex flex-col text-sm text-slate-600">
            用户名
            <input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="输入用户名"
              autoFocus
              className="mt-1.5 px-3.5 sm:px-4 py-2.5 border border-slate-200 rounded-xl text-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400 transition-all"
            />
          </label>

          <label className="flex flex-col text-sm text-slate-600">
            授权码
            <input
              type="password"
              value={authCode}
              onChange={(e) => setAuthCode(e.target.value)}
              placeholder="输入授权码"
              className="mt-1.5 px-3.5 sm:px-4 py-2.5 border border-slate-200 rounded-xl text-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400 transition-all"
            />
          </label>

          {error && (
            <div className="text-xs text-red-600 bg-red-50 border border-red-100 rounded-lg px-3 py-2">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 rounded-xl text-sm font-medium bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50 transition-all"
          >
            {loading ? "验证中…" : "登录"}
          </button>
        </form>

        <p className="text-[11px] text-slate-400 text-center mt-5 sm:mt-6">
          仅供授权用户使用
        </p>
      </div>
    </div>
  );
}
