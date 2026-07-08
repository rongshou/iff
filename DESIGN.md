# IFF / 天权 · 天枢 Design System

## 1. Atmosphere & Identity

A calm, glass-layered intelligence platform. The signature is **graded depth through light**: surfaces float at different elevations via subtle blur, tinted shadows, and translucent borders rather than opaque boxes. The brand identity carries a three-tone gradient (indigo → violet → rose) that signals movement and transformation — the journey from information to insight.

Two sibling apps share one shell:
- **天权 (tianquan)** — the IFF brand anchor. Cool indigo-dominant, authoritative.  
- **天枢 (tianshu)** — a warm violet-to-amber variant. Intimate, personal, assessment-focused.

Each retains its own accent identity while sharing the same navigation architecture, typographic rhythm, and glass-surface language.

## 2. Color

### Palette

| Role | Token | Value | Usage |
|------|-------|-------|-------|
| Surface/base | `--surface-base` | `#f8fafc` | Page background |
| Surface/card | `--surface-card` | `#ffffff` | Cards, chat bubbles |
| Surface/elevated | `--surface-elevated` | `rgba(255,255,255,0.75)` | Glass nav, overlays |
| Text/primary | `--text-primary` | `#0f172a` | Headlines, body |
| Text/secondary | `--text-secondary` | `#475569` | Descriptions |
| Text/muted | `--text-muted` | `#64748b` | Captions, meta |
| Text/placeholder | `--text-placeholder` | `#94a3b8` | Input hints, disabled |
| Border/default | `--border-default` | `rgba(226,232,240,0.7)` | Card borders, dividers |
| Border/subtle | `--border-subtle` | `rgba(226,232,240,0.4)` | Soft separations |
| Border/accent | `--border-accent` | `rgba(199,210,254,0.8)` | Active, focus rings |
| Accent/primary | `--accent-primary` | `#6366f1` | CTAs, links, active states |
| Accent/hover | `--accent-hover` | `#4f46e5` | Button hover |
| Accent/deep | `--accent-deep` | `#4338ca` | Pressed, strong emphasis |
| Accent/soft | `--accent-soft` | `#eef2ff` | Tag backgrounds, code bg |
| Accent/glow | `--accent-glow` | `rgba(99,102,241,0.45)` | Icon shadows, button glows |
| Gradient/brand | `--gradient-brand` | `#6366f1 → #a855f7 → #ec4899` | Logo mark, brand stripe |
| Gradient/soft | `--gradient-soft` | `#eef2ff → #f5f3ff` | Card hover, scene prompts |

### Rules
- Accent is indigo-first. Violet and rose exist only in gradients — never as solid fills.
- Surface hierarchy: base → card → glass. One level of elevation per context; never stack glass on glass.
- Tinted shadows always carry the accent hue at low opacity.

## 3. Typography

### Scale

| Level | Size | Weight | Line Height | Usage |
|-------|------|--------|-------------|-------|
| Display | 20px | 700 | 1.3 | Empty state hero title |
| H1 | 18px | 600 | 1.4 | Chat section headers |
| Body | 15-16px | 400 | 1.6 | Chat messages, form text |
| Body/sm | 13-14px | 400 | 1.5 | Scene prompts, secondary |
| Caption | 11-12px | 400-500 | 1.4 | Labels, metadata, footer |
| Nav/link | 11.5px | 500 | 1.4 | Navigation pills |
| Brand/mark | 11px | 800 | 1.0 | Logo monogram |
| Code | 0.83em | 400 | 1.55 | Inline code, pre blocks |

### Font Stack
- Primary: `-apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Helvetica Neue", sans-serif`
- Mono: `ui-monospace, SFMono-Regular, Menlo, monospace`

### Rules
- Max 2 font families. System stack for UI, mono for code and the brand mark.
- Letter-spacing: brand mark uses 0.18em; overline labels use 0.08em; captions use 0.02em.
- CJK text: PingFang SC preferred; fallback to Microsoft YaHei.

## 4. Spacing & Layout

### Base Unit
All spacing derives from 4px.

| Token | Value | Usage |
|-------|-------|-------|
| `--space-1` | 4px | Icon-to-label, micro gaps |
| `--space-2` | 8px | Compact groups |
| `--space-3` | 12px | Form padding, card inner |
| `--space-4` | 16px | Standard padding |
| `--space-5` | 20px | Section gaps |
| `--space-6` | 24px | Card groups |
| `--space-8` | 32px | Major sections |

### Grid
- Max content: 100% width, centered
- Chat: single column, max-readable width
- Breakpoints: sm 640px, md 768px, lg 1024px

## 5. Components

### BrandNav (shared navigation bar)

- **Structure**: Fixed-width floating glass pill. Logo monogram → separator → subtitle/label → nav links (right-aligned pills) → action buttons
- **Variants**: IFF (indigo gradient logo, default) / TIA (violet→amber gradient logo)
- **Spacing**: py-2 px-4, gap-3 between sections
- **States**:
  - Default: glass bg (white/75 + saturate(180%) blur(12px)), subtle bottom border, text-muted links
  - Hover (links): bg shifts to white/90, text to accent, border to accent/20
  - Active (current page): indigo text, white/80 bg, indigo border
  - Focus: visible ring on keyboard nav (2px indigo outline offset)
- **Accessibility**: All links are `<a>` with href. Logo has aria-label. Keyboard: Tab through links, Enter to activate.
- **Motion**: Link hover: 150ms ease-out on bg, color, border. No layout shifts.

### Chat Bubble

- **User**: indigo gradient bg, white text, tinted glow shadow, right-aligned
- **AI**: white bg, slate border, left-aligned, subtle lift shadow

### Scene Card (empty state)

- Glass-adjacent white card with soft indigo-tinted shadow, lift on hover (translateY -2px)

## 6. Motion & Interaction

| Type | Duration | Easing | Usage |
|------|----------|--------|-------|
| Micro | 150ms | ease-out | Link hover, button press, icon color |
| Standard | 200-250ms | ease | Card hover lift, border transitions |
| Emphasis | 300ms | ease-out | Empty state entry, hero fade-in |

### Rules
- Animate only `transform` and `opacity`.
- No `top`, `left`, `width`, `height` animations.
- `prefers-reduced-motion`: disable all non-essential transitions.
- Glass blur only on fixed/sticky elements (nav bar).

## 7. Depth & Surface

**Strategy**: Glass + tonal shift (mixed).

| Level | Treatment | Usage |
|-------|-----------|-------|
| Base | `#f8fafc` solid | Page background |
| Card | `#ffffff` + 1px border + subtle shadow | Chat bubbles, cards |
| Glass | `white/75` + `backdrop-blur(12px)` + `saturate(180%)` + border | Navigation |
| Elevated | Card + lift shadow (+2px Y, expanded glow) | Hover states |
