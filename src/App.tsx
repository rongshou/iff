import { HashRouter, Routes, Route } from "react-router-dom";
import ExplorePage from "./pages/Explore";
import ChatPage from "./pages/Chat";
import ProfilePage from "./pages/ProfilePage";

const VERSION = import.meta.env.VITE_APP_VERSION || "v?";

export default function App() {
  return (
    <>
      <HashRouter>
        <Routes>
          <Route path="/" element={<ChatPage />} />
          <Route path="/explore" element={<ExplorePage />} />
          <Route path="/chat" element={<ChatPage />} />
          <Route path="/profile" element={<ProfilePage />} />
        </Routes>
      </HashRouter>
      <footer
        style={{
          textAlign: "center",
          padding: "24px 0 16px",
          fontSize: 11,
          color: "#94a3b8",
          lineHeight: 1.8,
        }}
      >
        <div style={{ fontWeight: 600, color: "#b45309", fontSize: 12 }}>提示：我们只提供工具，生成的内容仅供参考，请自主做出判断、选择和决策。</div>
        <div style={{ marginTop: 4 }}>{VERSION}</div>
      </footer>
    </>
  );
}
