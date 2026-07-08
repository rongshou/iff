/**
 * BrandNav - 共用顶部导航栏（步骤 1）
 *
 * 设计原则：
 * - 通过 props 接收所有可变数据（品牌名/色/链接），组件本身保持中性
 * - tianshu 和 tianquan 各自传入自己的色值和跳转目标
 * - 当前版本（步骤 1）只用于 tianquan
 * - 步骤 2/3 会扩展：tianshu 通过静态生成的 HTML+CSS 副本引入
 */

import type { CSSProperties } from "react";

export interface BrandNavLink {
  /** 显示文字 */
  label: string;
  /** emoji 或图标字符 */
  icon?: string;
  /** 跳转路径（react-router 用 to，其他用 href） */
  to?: string;
  href?: string;
  /** 当前是否激活（用于主样式区分） */
  active?: boolean;
  /** 主题色变体（'primary' | 'accent'） */
  variant?: "primary" | "accent";
  /** 标题属性 */
  title?: string;
}

export interface BrandNavAction {
  /** 按钮文字 */
  label: string;
  /** emoji 图标 */
  icon?: string;
  /** 点击处理 */
  onClick: () => void;
  /** 移动端是否隐藏文字（只显示 icon） */
  hideTextOnMobile?: boolean;
  /** 标题属性 */
  title?: string;
}

export interface BrandNavProps {
  /** 品牌名（方形 logo 里的字母，如 IFF / TIA） */
  brandName: string;
  /** 品牌副标题（"智能留学平台" 或 "综合特质测评"） */
  brandSubtitle: string;
  /** 当前场景名（如 "选校定位"，没有就传 undefined） */
  sceneLabel?: string;
  /** 跳转链接（首页/档案/天枢 等） */
  links?: BrandNavLink[];
  /** 操作按钮（清空等） */
  actions?: BrandNavAction[];
  /** Logo 渐变色（CSS background），默认 indigo→purple */
  brandGradient?: string;
  /** 分隔符渐变色 */
  brandSepColor?: string;
  /** 顶层额外 className（默认含 brand-stripe 渐变背景） */
  className?: string;
}

const DEFAULT_GRADIENT =
  "linear-gradient(135deg, #6366f1 0%, #a855f7 50%, #ec4899 100%)";
const DEFAULT_SEP = "linear-gradient(180deg, #6366f1, #a855f7)";

export default function BrandNav({
  brandName,
  brandSubtitle,
  sceneLabel,
  links = [],
  actions = [],
  brandGradient = DEFAULT_GRADIENT,
  brandSepColor = DEFAULT_SEP,
  className = "brand-stripe",
}: BrandNavProps) {
  const logoStyle: CSSProperties = { background: brandGradient };
  const sepStyle: CSSProperties = { background: brandSepColor };

  return (
    <div className={`${className} nav-glass -mx-4 sm:-mx-6 px-3 sm:px-4 py-1.5 flex items-center gap-2 sm:gap-3`}>
      {/* 左侧品牌区 */}
      <div className="flex items-center gap-2 min-w-0">
        <span className="brand-mark shrink-0" style={logoStyle}>
          {brandName}
        </span>
        <span className="brand-sep shrink-0" style={sepStyle} />
        <span className="brand-meta truncate">
          {brandSubtitle}
          {sceneLabel && (
            <>
              {" · "}
              <b>{sceneLabel}</b>
            </>
          )}
        </span>
      </div>

      {/* 右侧链接区 */}
      <div className="flex items-center gap-1 ml-auto shrink-0">
        {links.map((link, i) => {
          const baseClass =
            "inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11.5px] font-medium transition-all whitespace-nowrap";
          const variantClass = link.active
            ? "text-indigo-600 bg-white/80 border border-indigo-200 hover:bg-indigo-100"
            : link.variant === "accent"
            ? "text-slate-500 border border-slate-200 bg-white/60 hover:text-purple-600 hover:border-purple-300 hover:bg-white"
            : "text-slate-500 border border-slate-200 bg-white/60 hover:text-indigo-600 hover:border-indigo-300 hover:bg-white";

          const href = link.to || link.href;
          const Comp: any = href ? "a" : "button";

          return (
            <Comp
              key={i}
              {...(href ? { href } : { type: "button" })}
              className={`${baseClass} ${variantClass}`}
              title={link.title || link.label}
            >
              {link.icon && <span className="inline-block w-3.5 h-3.5 leading-none text-[13px] text-center align-middle">{link.icon}</span>}
              <span>{link.label}</span>
            </Comp>
          );
        })}

        {/* 操作按钮 */}
        {actions.map((action, i) => (
          <button
            key={i}
            onClick={action.onClick}
            className="text-[11.5px] text-slate-500 hover:text-red-600 px-2.5 py-1 rounded-lg hover:bg-red-50 transition-colors flex items-center gap-1"
            title={action.title || action.label}
          >
            {action.icon && <span className="inline-block w-3.5 h-3.5 leading-none text-[13px] text-center align-middle">{action.icon}</span>}
            {action.hideTextOnMobile ? (
              <>
                <span className="hidden sm:inline">{action.label}</span>
                <span className="sm:hidden">{action.icon || ""}</span>
              </>
            ) : (
              <span>{action.label}</span>
            )}
          </button>
        ))}
      </div>
    </div>
  );
}