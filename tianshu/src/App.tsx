/**
 * tianshu App - sub-3.1 核心架构
 *
 * 完整结构：
 *   <TianshuProvider>
 *     <BrandNav />        共用顶栏
 *     <ProgressBar />     5 步进度
 *     <StepRouter />      当前步骤（sub-3.1 全是占位）
 *   </TianshuProvider>
 *
 * sub-3.2~3.5 会替换 StepRouter 里的占位为真正的表单
 * sub-3.6 会替换 Step 5 为完整报告 + 下载/打印
 */

import BrandNav from "../../src/components/BrandNav";
import { TianshuProvider } from "./TianshuContext";
import ProgressBar from "./ProgressBar";
import StepRouter from "./StepRouter";
import "./tianshu.css";

export default function App() {
  return (
    <TianshuProvider>
      <div className="tianshu-app">
        {/* ── 浮岛导航（统一 IFF 品牌）── */}
        <BrandNav
          brandName="Iff"
          brandSubtitle="天权智能留学问答平台"
          links={[
            { label: "首页", icon: "home", href: "../", variant: "primary" },
            { label: "天权", icon: "globe", href: "../tianquan/", variant: "primary" },
            { label: "档案", icon: "user", href: "../tianquan/#/profile" },
          ]}
        />

        {/* 测评主体 */}
        <main className="tianshu-main">
          <ProgressBar />
          <div className="tianshu-content">
            <StepRouter />
          </div>
        </main>

        <footer className="tianshu-footer">
          天枢 · 基于八字 + 紫微 + MBTI + 霍兰德四维交叉 · v0.14
        </footer>
      </div>
    </TianshuProvider>
  );
}