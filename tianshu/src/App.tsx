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
        {/* ── 浮岛导航（天枢品牌色）── */}
        <BrandNav
          brandName="TIA"
          brandSubtitle="综合特质测评与生涯规划"
          links={[
            { label: "首页", icon: "home", href: "./", variant: "primary" },
            { label: "天权", icon: "globe", href: "../tianquan/", variant: "primary" },
            { label: "档案", icon: "user", href: "../tianquan/#/profile" },
            { label: "旧测评", icon: "archive", href: "./legacy/", variant: "accent" },
          ]}
          brandGradient="linear-gradient(135deg, #a855f7 0%, #ec4899 50%, #f59e0b 100%)"
          brandSepColor="linear-gradient(180deg, #a855f7, #ec4899)"
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