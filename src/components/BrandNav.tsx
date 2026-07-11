/**
 * BrandNav — 共用浮岛式导航栏
 *
 * 设计语言：
 * - 浮岛式：脱离页面顶部，圆角胶囊悬浮
 * - 毛玻璃：backdrop-blur + saturate 半透明背景
 * - 品牌标记：渐变文字 logo + 分隔线 + 副标题
 * - 导航链接：药丸形按钮，hover 微交互（缩放 + 颜色渐变）
 */

import type { CSSProperties } from "react";
import { Link } from "react-router-dom";

// ── 轻量 SVG 图标（替代 emoji）──

function HomeIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
      strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 12L12 3l9 9" />
      <path d="M9 21V12h6v9" />
    </svg>
  );
}

function CompassIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
      strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76" />
    </svg>
  );
}

function UserIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
      strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
      <circle cx="12" cy="7" r="4" />
    </svg>
  );
}

function ArchiveIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
      strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 8v13H3V8" />
      <path d="M1 3h22v5H1z" />
      <path d="M10 12h4" />
    </svg>
  );
}

function GlobeIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
      strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <path d="M2 12h20" />
      <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
    </svg>
  );
}

function TrashIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
      strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="3 6 5 6 21 6" />
      <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
    </svg>
  );
}

const ICON_MAP: Record<string, React.FC> = {
  home: HomeIcon,
  compass: CompassIcon,
  user: UserIcon,
  archive: ArchiveIcon,
  globe: GlobeIcon,
  trash: TrashIcon,
};

// ── 类型 ──

export interface BrandNavLink {
  label: string;
  icon?: string;   // key from ICON_MAP, e.g. "home"
  href?: string;
  to?: string;      // react-router
  active?: boolean;
  variant?: "primary" | "accent";
  title?: string;
}

export interface BrandNavAction {
  label: string;
  icon?: string;
  onClick: () => void;
  hideTextOnMobile?: boolean;
  title?: string;
}

export interface BrandNavProps {
  brandName: string;
  brandSubtitle: string;
  sceneLabel?: string;
  links?: BrandNavLink[];
  actions?: BrandNavAction[];
  /** CSS gradient for the logo text */
  brandGradient?: string;
  /** Separator gradient */
  brandSepColor?: string;
}

// ── 默认值 ──

const DEFAULT_GRADIENT = "linear-gradient(135deg, #6366f1 0%, #a855f7 50%, #ec4899 100%)";
const DEFAULT_SEP = "linear-gradient(180deg, #6366f1, #a855f7)";

// ── 组件 ──

export default function BrandNav({
  brandName,
  brandSubtitle,
  sceneLabel,
  links = [],
  actions = [],
  brandGradient = DEFAULT_GRADIENT,
  brandSepColor = DEFAULT_SEP,
}: BrandNavProps) {
  const logoStyle: CSSProperties = { background: brandGradient };
  const sepStyle: CSSProperties = { background: brandSepColor };

  return (
    <nav
      className="nav-float"
      role="navigation"
      aria-label="主导航"
    >
      {/* ── 左侧：品牌区 ── */}
      <div className="nav-brand">
        <span className="nav-logo" style={logoStyle}>
          {brandName}
        </span>
        <span className="nav-sep" style={sepStyle} />
        <span className="nav-meta">
          {brandSubtitle}
          {sceneLabel && (
            <>
              <span className="nav-meta-sep">·</span>
              <b>{sceneLabel}</b>
            </>
          )}
        </span>
      </div>

      {/* ── 右侧：导航链接 ── */}
      <div className="nav-links">
        {links.map((link, i) => {
          const IconComp = link.icon ? ICON_MAP[link.icon] : null;
          const isActive = link.active;
          const isAccent = link.variant === "accent";

          const pillClass = [
            "nav-pill",
            isActive && "nav-pill--active",
            isAccent && "nav-pill--accent",
          ].filter(Boolean).join(" ");

          const href = link.to || link.href;
          const useRouterLink = !!link.to;
          const Tag = useRouterLink ? Link : href ? "a" : "button";
          const linkProps = useRouterLink
            ? { to: href! }
            : href
              ? { href }
              : { type: "button" as const };

          return (
            <Tag
              key={i}
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              {...(linkProps as any)}
              className={pillClass}
              title={link.title || link.label}
              {...(isActive ? { "aria-current": "page" as const } : {})}
            >
              {IconComp && (
                <span className="nav-pill-icon"><IconComp /></span>
              )}
              <span className="nav-pill-label">{link.label}</span>
            </Tag>
          );
        })}

        {/* ── 操作按钮 ── */}
        {actions.map((action, i) => {
          const IconComp = action.icon ? ICON_MAP[action.icon] : null;
          return (
            <button
              key={i}
              onClick={action.onClick}
              className="nav-action"
              title={action.title || action.label}
            >
              {IconComp && <span className="nav-action-icon"><IconComp /></span>}
              {action.hideTextOnMobile ? (
                <>
                  <span className="hidden sm:inline">{action.label}</span>
                  <span className="sm:hidden">{IconComp && <IconComp />}</span>
                </>
              ) : (
                <span>{action.label}</span>
              )}
            </button>
          );
        })}
      </div>
    </nav>
  );
}
