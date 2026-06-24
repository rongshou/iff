import { BrowserRouter, Routes, Route } from "react-router-dom";
import ExplorePage from "./pages/Explore";
import ChatPage from "./pages/Chat";

const BASE = import.meta.env.BASE_URL.replace(/\/$/, "");

export default function App() {
  return (
    <BrowserRouter basename={BASE}>
      <Routes>
        <Route path="/" element={<ChatPage />} />
        <Route path="/explore" element={<ExplorePage />} />
        <Route path="/chat" element={<ChatPage />} />
      </Routes>
    </BrowserRouter>
  );
}
