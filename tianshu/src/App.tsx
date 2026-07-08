/**
 * tianshu App - 步骤 2 MVP
 *
 * - 顶部用 <BrandNav />（和 tianquan 共用同一个组件）
 * - 下方占位"加载中..."（旧测评功能不在此处，访问根路径还是老页面）
 *
 * 步骤 3 才会把各 step 迁移进来。
 */

import BrandNav from "../../src/components/BrandNav";

export default function App() {
  return (
    <div style={{ minHeight: "100vh", background: "#f8fafc" }}>
      {/* 共用顶栏 - 天枢品牌色（紫色变体） */}
      <BrandNav
        brandName="TIA"
        brandSubtitle="综合特质测评与生涯规划"
        links={[
          { label: "首页", icon: "🏠", href: "/tianquan/", variant: "primary" },
          { label: "天权", icon: "🌐", href: "/tianquan/", variant: "primary" },
        ]}
        brandGradient="linear-gradient(135deg, #a855f7 0%, #ec4899 50%, #f59e0b 100%)"
        brandSepColor="linear-gradient(180deg, #a855f7, #ec4899)"
      />

      {/* 占位区 - 步骤 3 才会接入真正的测评 */}
      <main
        style={{
          maxWidth: 960,
          margin: "40px auto",
          padding: "0 20px",
          textAlign: "center",
          color: "#64748b",
        }}
      >
        <div style={{ fontSize: 48, marginBottom: 16 }}>🧭</div>
        <h1 style={{ fontSize: 24, color: "#1e293b", marginBottom: 8 }}>
          天枢 · 加载中
        </h1>
        <p style={{ fontSize: 14 }}>
          React 入口已就绪（步骤 2）。测评功能仍在原页面：
          <br />
          <a href="./legacy.html" style={{ color: "#a855f7" }}>
            访问旧版天枢测评
          </a>
        </p>
      </main>
    </div>
  );
}