/**
 * 天枢 · 北斗七星星座组件(SVG)
 * 替代 emoji,呼应「天枢 = 北斗第一星」
 */
function renderBeidouSvg({ size = 120, theme = "purple" } = {}) {
  // 主题色
  const colors = {
    purple: { main: "#fbbf24", star: "#c084fc", bg: "#4f7cff", line: "rgba(192,132,252,0.3)" },
    blue:   { main: "#fbbf24", star: "#93c5fd", bg: "#60a5fa", line: "rgba(147,197,253,0.3)" },
    dark:   { main: "#fbbf24", star: "#e5e7eb", bg: "#94a3b8", line: "rgba(229,231,235,0.2)" }
  };
  const c = colors[theme] || colors.purple;

  // 七星坐标(viewBox 0 0 200 200)
  // 勺形:左边斗口(4 星) + 右边斗柄(3 星)
  // 斗口:天枢 → 天璇 → 天权 → 天玑(形成一个类梯形/斗形)
  // 斗柄:天权 → 玉衡 → 开阳 → 摇光(向右延伸)
  const stars = [
    { name: "天枢", x: 40,  y: 110, size: 11, main: true  },  // 斗口左下
    { name: "天璇", x: 70,  y: 70,  size: 7,  main: false },  // 斗口左上
    { name: "天玑", x: 105, y: 70,  size: 7,  main: false },  // 斗口右上
    { name: "天权", x: 105, y: 115, size: 8,  main: false },  // 斗口右下,连接柄
    { name: "玉衡", x: 130, y: 95,  size: 7,  main: false },  // 柄中
    { name: "开阳", x: 155, y: 80,  size: 7,  main: false },  // 柄后
    { name: "摇光", x: 180, y: 60,  size: 8,  main: false },  // 柄末
  ];

  // 连线顺序(勺子形状)
  const lines = [
    [0, 1], [1, 2], [2, 3], [3, 0],  // 斗口四边形
    [3, 4], [4, 5], [5, 6]            // 斗柄
  ];

  // 生成星点
  const starSvg = stars.map((s, i) => {
    const isMain = s.main;
    const fill = isMain ? c.main : c.star;
    const r = s.size;
    // 中心实心 + 外部光晕
    return `
      <g class="star star-${i}" style="animation-delay: ${i * 0.3}s">
        <circle cx="${s.x}" cy="${s.y}" r="${r * 2.2}" fill="${fill}" opacity="0.15">
          <animate attributeName="opacity" values="0.15;0.35;0.15" dur="${2.5 + i * 0.2}s" repeatCount="indefinite"/>
        </circle>
        <circle cx="${s.x}" cy="${s.y}" r="${r * 1.4}" fill="${fill}" opacity="0.4">
          <animate attributeName="opacity" values="0.4;0.7;0.4" dur="${2 + i * 0.15}s" repeatCount="indefinite"/>
        </circle>
        <circle cx="${s.x}" cy="${s.y}" r="${r}" fill="${fill}">
          ${isMain ? `<animate attributeName="r" values="${r};${r * 1.15};${r}" dur="2.5s" repeatCount="indefinite"/>` : ''}
        </circle>
        ${isMain ? `<text x="${s.x}" y="${s.y - r - 6}" text-anchor="middle" fill="${fill}" font-size="9" font-weight="600" font-family="serif">天枢</text>` : ''}
      </g>
    `;
  }).join("");

  // 生成连线
  const lineSvg = lines.map(([a, b]) => {
    const sa = stars[a], sb = stars[b];
    return `<line x1="${sa.x}" y1="${sa.y}" x2="${sb.x}" y2="${sb.y}" stroke="${c.line}" stroke-width="1.5" opacity="0.8" stroke-linecap="round"/>`;
  }).join("");

  return `
    <svg class="beidou-svg" width="${size}" height="${size}" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg" aria-label="北斗七星">
      <defs>
        <radialGradient id="bgGlow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stop-color="${c.bg}" stop-opacity="0.15"/>
          <stop offset="100%" stop-color="${c.bg}" stop-opacity="0"/>
        </radialGradient>
      </defs>
      <!-- 背景光晕 -->
      <circle cx="100" cy="100" r="100" fill="url(#bgGlow)"/>
      <!-- 连线 -->
      ${lineSvg}
      <!-- 星点 -->
      ${starSvg}
    </svg>
  `;
}

// 暴露到全局
if (typeof window !== "undefined") {
  window.TianShuBeidou = { renderBeidouSvg };
}