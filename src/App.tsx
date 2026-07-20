import { Navigate, HashRouter, Routes, Route, Outlet } from "react-router-dom";
import { useEffect } from "react";
import { isAuthenticated, getTrialId } from "./services/auth";
import { loadSchoolAbbreviations } from "./services/school";
import { useAppStore } from "./store/appStore";
import LoginPage from "./pages/Login";
import ChatPage from "./pages/Chat";
import ProfilePage from "./pages/ProfilePage";

const VERSION = import.meta.env.VITE_APP_VERSION || "v?";

/**
 * 路由守卫：
 * - 已登录用户 → 放行
 * - 未登录且未用过试用 → 放行（试用模式，由 Chat 页面在首次回复后拦截）
 * - 未登录且已用过试用 → 跳转 /login
 */
function AuthGuard() {
  const trialUsed = useAppStore((s) => s.trialUsed);
  if (!isAuthenticated() && trialUsed) {
    return <Navigate to="/login" replace />;
  }
  return <Outlet />;
}

export default function App() {
  // 启动时预加载学校简称映射（fire-and-forget），让 Chat 页面调用时走同步缓存
  useEffect(() => {
    void loadSchoolAbbreviations();
    // 确保匿名试用 ID 尽早生成，后续 chat 请求头才能带上
    try {
      getTrialId();
    } catch {
      // ignore storage failures (private mode / quota)
    }
  }, []);
  return (
    <>
      <HashRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />

          {/* 受保护路由 */}
          <Route element={<AuthGuard />}>
            <Route path="/" element={<ChatPage />} />
            <Route path="/chat" element={<ChatPage />} />
            <Route path="/profile" element={<ProfilePage />} />
          </Route>

          {/* 兜底：未匹配的 hash 路由 → 跳首页（由 AuthGuard 处理登录态） */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </HashRouter>
      <footer
        style={{
          textAlign: "center",
          padding: "12px 0 16px",
          fontSize: 11,
          color: "#94a3b8",
          lineHeight: 1.8,
        }}
      >
        <div style={{ fontWeight: 600, color: "#b45309", fontSize: 12 }}>
          ⚠ 我们只提供工具，生成的内容仅供参考，请自主做出判断、选择和决策。
        </div>
        <div style={{ marginTop: 4, opacity: 0.7 }}>
          Iff · 天权智能留学问答平台 · {VERSION}
        </div>
        <div style={{ marginTop: 4, opacity: 0.6 }}>
          <a
            href="https://beian.miit.gov.cn/"
            target="_blank"
            rel="noopener noreferrer"
            style={{ color: "inherit", textDecoration: "none" }}
          >
            沪ICP备20004281号-1
          </a>
        </div>
      </footer>
    </>
  );
}
