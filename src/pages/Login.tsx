import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { login } from "../services/auth";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [authCode, setAuthCode] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    const result = login(username, authCode);
    setLoading(false);

    if (result.ok) {
      navigate("/", { replace: true });
    } else {
      setError(result.error || "登录失败");
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50 flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 text-white text-base font-bold shadow-lg shadow-indigo-200 mb-4">
            IFF
          </div>
          <h1 className="text-2xl font-bold text-slate-900">AI留学规划与生涯规划工具</h1>
          <p className="text-sm text-slate-500 mt-2">首次登录即绑定，后续使用相同凭据登录</p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 space-y-4">
          <label className="flex flex-col text-sm text-slate-600">
            用户名
            <input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="输入用户名"
              autoFocus
              className="mt-1.5 px-4 py-2.5 border border-slate-200 rounded-xl text-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400 transition-all"
            />
          </label>

          <label className="flex flex-col text-sm text-slate-600">
            授权码
            <input
              type="password"
              value={authCode}
              onChange={(e) => setAuthCode(e.target.value)}
              placeholder="输入授权码"
              className="mt-1.5 px-4 py-2.5 border border-slate-200 rounded-xl text-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400 transition-all"
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

        <p className="text-[11px] text-slate-400 text-center mt-6">
          仅供授权用户使用
        </p>
      </div>
    </div>
  );
}
