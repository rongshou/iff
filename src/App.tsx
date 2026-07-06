import { Navigate, HashRouter, Routes, Route, Outlet } from "react-router-dom";
import { useEffect } from "react";
import { isAuthenticated } from "./services/auth";
import { loadSchoolAbbreviations } from "./services/school";
import LoginPage from "./pages/Login";
import ChatPage from "./pages/Chat";
import ProfilePage from "./pages/ProfilePage";

const VERSION = import.meta.env.VITE_APP_VERSION || "v?";

/** 路由守卫：未登录跳转 /login */
function AuthGuard() {
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }
  return <Outlet />;
}

export default function App() {
  // 启动时预加载学校简称映射（fire-and-forget），让 Chat 页面调用时走同步缓存
  useEffect(() => {
    void loadSchoolAbbreviations();
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
          IFF · 智能留学平台 · {VERSION}
        </div>
      </footer>
    </>
  );
}
