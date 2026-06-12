import { BrowserRouter, Routes, Route, Link, useLocation } from "react-router-dom";
import RecommendPage from "./pages/Recommend";
import ExplorePage from "./pages/Explore";
import NewsPage from "./pages/News";

function Nav() {
  const location = useLocation();
  if (location.pathname.startsWith("/news")) return null;
  const linkClass = (path: string) =>
    `px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
      location.pathname === path
        ? "bg-indigo-600 text-white"
        : "text-gray-600 hover:bg-gray-100"
    }`;

  return (
    <nav className="bg-white">
      <div className="max-w-4xl mx-auto px-4 flex items-center gap-4 h-12">
        <Link to="/" className="font-bold text-indigo-700 text-lg" style={{ textDecoration: "none" }}>天权</Link>
        <Link to="/" className={linkClass("/")}>选校推荐</Link>
        <Link to="/news" className={linkClass("/news")}>资讯</Link>
        <Link to="/explore" className={linkClass("/explore")}>留学工具箱</Link>
      </div>
    </nav>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Nav />
      <Routes>
        <Route path="/" element={<RecommendPage />} />
        <Route path="/news" element={<NewsPage />} />
        <Route path="/explore" element={<ExplorePage />} />
      </Routes>
    </BrowserRouter>
  );
}