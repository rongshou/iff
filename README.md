# IFF · 留学智能平台

让 17 万个过来人，帮你选校。

一个集**AI 智能问答 + 三维评分推荐引擎 + 多维度测评**于一体的留学选校平台。

| 入口 | 说明 | 地址 |
|------|------|------|
| 🎓 **天权** | AI 选校助手 — 基于 17.6 万真实案例的三维评分推荐引擎 | `/tianquan/` |
| 🧭 **天枢** | 多维度交叉测评（MBTI / 霍兰德 / 八字 / 紫微） | `/tianshu/` |

---

## 技术栈

| 层 | 技术 |
|---|------|
| **前端** | React 19 + TypeScript 6 + Vite 8 + Tailwind CSS 4 + Zustand 5 |
| **后端** | Python 3.11 + FastAPI + SQLite (FTS5) + Uvicorn |
| **AI** | OpenCode API（`deepseek-v4-flash-free`） |
| **部署** | Docker + Docker Compose + Nginx |
| **CI/CD** | GitHub Actions → GitHub Pages + webhook → 自托管服务器 |
| **测试** | Vitest (前端) + pytest (后端) + Playwright (E2E) |

---

## 项目结构

```
/
├── src/                    # 前端源码 (Vite + React SPA)
│   ├── App.tsx             # 路由入口 + AuthGuard
│   ├── main.tsx            # 应用入口
│   ├── pages/              # 页面组件
│   │   ├── Login.tsx       # 登录页（授权码验证）
│   │   ├── Chat.tsx        # AI 对话主页（含多轮信息收集）
│   │   └── ProfilePage.tsx # 个人档案 + 查询历史
│   ├── components/         # 通用组件
│   │   └── MessageBubble.tsx
│   ├── hooks/              # 自定义 Hook
│   │   ├── useChatSend.ts  # 聊天核心逻辑 (handleSend/doSendToAI)
│   │   ├── useChatInput.ts # 输入状态
│   │   └── useChatScroll.ts# 滚动控制
│   ├── services/           # 服务层
│   │   ├── auth.ts         # 登录/登出/会话管理
│   │   ├── chat.ts         # AI 对话 API
│   │   ├── chat-helpers.ts # 信息提取工具函数
│   │   ├── profile.ts      # 档案 CRUD
│   │   ├── api.ts          # 新闻/授权码 API
│   │   └── school.ts       # 学校简称缓存层
│   ├── store/              # Zustand 状态管理
│   ├── types/              # TypeScript 类型定义
│   ├── config/             # 场景配置
│   └── utils/              # 工具函数
│
├── backend/                # 后端源码 (Python FastAPI)
│   └── app/
│       ├── main.py         # FastAPI 应用入口，挂载全部路由
│       ├── api/            # API 路由层
│       │   ├── chat.py     # POST /api/chat (AI 对话)
│       │   ├── auth.py     # POST /api/verify-auth-code
│       │   ├── recommend.py# POST /api/recommend
│       │   ├── news.py     # GET /api/news
│       │   ├── school.py   # GET /api/school/abbreviations
│       │   ├── knowledge.py# 知识库搜索
│       │   ├── mbti.py     # MBTI 数据接口
│       │   └── timeline.py # 时间线数据
│       ├── core/           # 核心配置
│       │   ├── config.py   # Settings (Pydantic)
│       │   ├── security.py # verify_auth 全局依赖
│       │   └── database.py # SQLite 连接工厂
│       ├── services/       # 业务逻辑层
│       │   ├── chat.py     # 聊天服务（SYSTEM_PROMPT, 知识检索, LLM 调用）
│       │   ├── recommend.py# 推荐引擎编排（含 5min 结果缓存）
│       │   ├── case_matcher.py # 三维评分核心（GPA/排名/案例）
│       │   ├── school_engine.py# 规则增强 & 申请策略
│       │   ├── news_knowledge.py# 知识库 FTS 搜索
│       │   ├── school_abbrev.py # 学校简称权威映射（49条）
│       │   └── content_filter.py# 广告内容过滤
│       ├── models/         # Pydantic 数据模型
│       └── utils/          # 工具函数
│
├── tianshu/                # 天枢静态页面（独立 HTML + JS）
│   ├── index.html          # 首页（带 auth 跳转检查）
│   ├── app.js, bazi.js, beidou.js, engine.js, data.js
│   └── VERSION
│
├── landing/                # 着陆页 (纯静态 HTML)
│   └── index.html
│
├── scripts/                # 构建 & 运维脚本
│   ├── build-prod.sh       # 生产构建（Vite → 目录重组 → 产物到 dist/）
│   └── kb_pipeline.py      # 知识库文章清洗管道
│
├── tests/                  # 测试
│   ├── test_case_matcher.py# 推荐引擎 70 用例（pytest）
│   └── smoke-test.sh       # E2E 冒烟测试
│
├── nginx.conf              # Nginx 反向代理配置
├── Dockerfile              # nginx 容器镜像构建
├── docker-compose.yml      # Docker 编排（nginx + backend）
└── vite.config.ts          # Vite 构建配置
```

---

## 快速开始

### 本地开发

```bash
# 1. 后端
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 3470

# 2. 前端 (另一个终端)
npm install
npm run dev          # Vite dev server → http://localhost:5173
```

Vite 已配置 `/api` 代理 → `http://localhost:3470`。

### Docker 构建

```bash
docker compose up -d --build
```

启动后：
- **首页**: http://localhost:8080/
- **天权**: http://localhost:8080/tianquan/
- **天枢**: http://localhost:8080/tianshu/
- **API 健康检查**: http://localhost:8080/api/health

---

## 核心功能

### 🎓 天权 — AI 选校助手

| 功能 | 说明 |
|------|------|
| **AI 对话** | 多轮信息收集 + 知识库检索（FTS5, 2165 篇文章） |
| **三维评分推荐** | GPA 匹配 40% + 学校排名 30% + 案例证据 30% |
| **推荐缓存** | 同 profile 5 分钟内不重复计算 |
| **选校触发** | 强信号 12 个关键词（任一命中）+ 弱信号 9 个（需 ≥2 命中） |
| **信息提取** | 自动从对话提取 GPA/学校/专业/国家等字段 |

### 🧭 天枢 — 多维测评

独立静态页面（不依赖 React），集成 MBTI / 霍兰德 / 八字 / 紫微斗数四种测评工具。访问时自动检查登录状态，无有效会话则跳转到天权登录页。

### 🔐 登录与授权

前后端双层验证：
1. 用户输入授权码 → `POST /api/verify-auth-code` 后端校验
2. 通过后写入 `localStorage.iff_auth`（7 天有效）
3. 天权路由由 `AuthGuard` 守卫，天枢页面由内联脚本守卫

授权码通过 `TIANQUAN_VALID_AUTH_CODES` 环境变量配置（逗号分隔），当前已配置 30 个。

---

## API 一览

| 端点 | 方法 | 说明 | 鉴权 |
|------|------|------|------|
| `/api/health` | GET | 健康检查 | 免鉴权 |
| `/api/verify-auth-code` | POST | 授权码验证 | 免鉴权 |
| `/api/chat` | POST | AI 对话（支持 stream） | `X-Auth-Code` |
| `/api/recommend` | POST | 三维评分推荐 | `X-Auth-Code` |
| `/api/news` | GET | 知识库文章搜索 | `X-Auth-Code` |
| `/api/school/abbreviations` | GET | 学校简称映射 | `X-Auth-Code` |

> 所有受保护端点在请求头携带 `X-Auth-Code: <授权码>` 即可。全局 `verify_auth` 依赖注入，`/api/health` 和 `/api/verify-auth-code` 白名单放行。

---

## 部署

### 双轨部署

| 目标 | 方式 | 地址 |
|------|------|------|
| GitHub Pages | GitHub Actions 自动构建部署 | `https://rongshou.github.io/iff/` |
| 自托管服务器 | GitHub Actions webhook → Docker 重建 | `http://47.93.149.29/tianquan/` |

### CI/CD

```
git push master
  → GitHub Actions (.github/workflows/deploy.yml)
    → npm ci → npm run build
    → 部署到 GitHub Pages
    → POST webhook → 自托管服务器
```

### 手动部署

```bash
git pull origin master
docker compose up -d --build
```

---

## 环境变量

参见 `.env.example`：

| 变量 | 说明 |
|------|------|
| `TIANQUAN_LLM_API_KEY` | OpenCode API 密钥 |
| `TIANQUAN_VALID_AUTH_CODES` | 授权码白名单（逗号分隔） |
| `ADVISOR_DATA_DIR` | 应用数据库目录 |
| `WERSS_DB_PATH` | 源文章库路径 |

---

## 关联文档

- [`INTERNAL_DOCS.md`](./INTERNAL_DOCS.md) — 详细工程文档（知识库清洗、推荐引擎、前端架构等）
