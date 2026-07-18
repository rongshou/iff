# tianquan 工程文档

> 记录知识库清洗、聊天服务优化等后台改动，以及前端功能开发的工程决策和配置。
> 每次重开项目前先读这个文件，避免遗忘。

---

## 一、知识库清洗

### 1.1 数据源

| 项目 | 路径 |
|------|------|
| 原始文章库 | `/home/admin/werss/data/db.db`（articles 表，2220 条） |
| 应用数据库 | `/home/admin/tianquan/backend/data/advisor.db` |
| 排除表 | `advisor.db.excluded_articles` |
| 清洗脚本 | `/home/admin/scripts/cleanup_knowledge_base.py` |

### 1.2 排除策略

**策略**：只排除纯商品广告和私域导流垃圾内容，其余全部保留。

**保留分类**（直接放行，无需关键词匹配）：
- 选校与申请、政策与解读、大学动态、排名与榜单
- 就业与实习、生活适应、低龄留学
- 签证与出入境、考试技巧、语言考试、费用与奖学金

**排除依据**（仅标题含以下任一关键词）：

```
AD_KEYWORDS = [
    # 商品推销
    "T恤", "瘦身", "健身", "减肥", "穿搭",
    "凉鞋", "运动鞋", "编织鞋", "小黑裙",
    "风扇", "空调", "席子", "床单", "枕头",
    "耳机", "冰淇淋", "雪糕", "小龙虾",
    "项链", "手串", "玉石", "睡衣",
    "洗发水", "护肤品", "面膜",
    # 私域导流
    "加入20万准留学家庭的家长交流群",
    # 测试数据
    "test", "测试",
]
```

**当前状态**：2220 → 保留 2155 / 排除 65

⚠️ **注意**：title 字段可能存了文章全文（最长 1000 字符），所以关键词匹配会对全文进行。添加新的排除关键词时，要确认不会匹配到正常教育内容的正文。

### 1.3 清洗脚本操作方式

```bash
python3 /home/admin/scripts/cleanup_knowledge_base.py
```

脚本逻辑：
1. 遍历 werss.db.articles 中所有文章
2. 按 `should_keep()` 判断保留/排除
3. 写入 `advisor.db.excluded_articles` 表
4. 如果清了 `excluded_articles` 或改了排除策略，需要同时删除 FTS 索引让下次搜索重建：

```python
conn.execute('DELETE FROM excluded_articles')
conn.execute('DROP TABLE IF EXISTS articles_fts')
conn.commit()
```

### 1.4 FTS 索引

文件：`/home/admin/tianquan/backend/app/services/news_knowledge.py`

- `articles_fts` 是 FTS5 虚拟表，存储搜索索引
- **惰性重建**：首次调用 `search_articles()` 时自动触发
- **已修改**：重建时跳过 `excluded_articles` 表中的文章（`_build_fts_index()` 中有 `excluded_ids` 检查）
- 如果想强制重建：删掉 `articles_fts` 表，下次搜索自动重建

---

## 二、聊天服务改动

文件：`/home/admin/tianquan/backend/app/services/chat.py`

### 2.1 `_parse_undergrad()` — 学校名称解析

**Bug 修复**：
1. **Substring 误判**："中山大学" → 正则 `山大` 匹配 → 返回"山东大学"
   - 修复：改用 `_extract_best_university()` 全名校名校名优先 + 缩写白名单
2. **系后缀干扰**："计算机系"、"数学系" → 被当作大学名称
   - 修复：`_UNIV_PATTERN` 正则去掉 `系` 后缀匹配
3. **冒号吞词**："学校是北京大学" → 返回"是北京大学"（"是"被吞）
   - 修复：label:value 模式要求冒号存在，且不在 value 前过滤单词

**解析优先级**：
1. 全名校名校名提取（优先 `XX大学` 或 `XX学院` 结尾的完整名称）
2. 缩写匹配（"北大"、"清华"等 20+ 缩写）
3. 院校层级关键词（"985"、"211"、"双一流"）
4. label:value 模式（"学校：北京大学"）

**已移除的死代码**：
- `_UNIV_PATTERN` 正则
- `_contains_standalone()` 函数

**测试用例**：27 个案例全部通过，覆盖缩写、全称、干扰项。

### 2.2 `_is_likely_ad()` — 运行时广告过滤

三级检测：

| 层级 | 策略 | 判定 |
|------|------|------|
| 品牌白名单 | 知名留学媒体内容直接放行 | 匹配白名单 → 放行 |
| 强信号 | 任一匹配即广告 | "立即咨询"、"扫码"、"添加微信" 等 |
| 弱信号 | ≥2 匹配即广告 | "限时"、"免费"、"名额"、"点击" 等 |
| UI 碎片 | ≥2 匹配即低质量 | "轻触阅读原文"、"点赞在看" 等 |
| 中文占比 | < 40% 且 > 20 字符 | 非中文内容 |

品牌白名单：
```python
_BRAND_SOURCES = {
    "棕榈君", "启德", "新东方", "前途出国", "棕榈大道",
}
```

### 2.3 `load_context_from_history()` — 知识注入流程

```
SYSTEM_PROMPT
  → search_articles(last_user_query, limit=8)
  → _is_likely_ad() 过滤（最多保留 5 条非广告）
  → 选校模式 / 通用模式
```

### 2.4 SYSTEM_PROMPT 修改

1. **替换引用表述**：`【参考信息】（请自然吸收...）` → `【你的知识储备】`
2. **去掉文章标题**：引用时不再附带原标题
3. **增加对照表**：`正确与错误表达对比`（由助手老师提供）
4. **增加保护指令**：`审慎推荐原则`（区分事实与推广、不背书机构、客观数据优先）
5. **增加禁止指令**：`绝对禁止的表述`（如"根据文章"、"参考了某篇文章"等）
6. 后续如果还需要改提示词，直接在 `SYSTEM_PROMPT` 常量中修改

---

## 三、数据库结构

### 3.1 excluded_articles 表

```sql
CREATE TABLE excluded_articles (
    article_id TEXT PRIMARY KEY,
    reason TEXT,
    title TEXT,
    created_at TEXT
);
```

这个表只做排除用——里面的文章不会出现在搜索结果中。

### 3.2 相关路径速查

| 文件/数据库 | 用途 |
|------------|------|
| `/home/admin/werss/data/db.db` | 源文章库（只读） |
| `/home/admin/tianquan/backend/data/advisor.db` | 应用数据库（含 excluded_articles） |
| `/home/admin/tianquan/backend/app/services/chat.py` | 聊天服务（核心改动） |
| `/home/admin/tianquan/backend/app/services/news_knowledge.py` | 知识库搜索（FTS 构建） |
| `/home/admin/scripts/cleanup_knowledge_base.py` | 清洗脚本 |

---

## 四、后续维护指引

### 4.1 想重新清洗知识库

```python
# 清除旧排除 + FTS
conn = sqlite3.connect('/home/admin/tianquan/backend/data/advisor.db')
conn.execute('DELETE FROM excluded_articles')
conn.execute('DROP TABLE IF EXISTS articles_fts')
conn.commit()

# 重新跑脚本
python3 /home/admin/scripts/cleanup_knowledge_base.py
```

### 4.2 想添加/删除排除规则

编辑 `/home/admin/scripts/cleanup_knowledge_base.py` 中的 `AD_KEYWORDS`，然后按 4.1 重跑。

### 4.3 想修改 SYSTEM_PROMPT

注意 SYSTEM_PROMPT 的 `## 📋 回复结构要求` 章节（v0.14 新增），要求 LLM 按 `## 推荐院校` / `## 申请策略` 章节组织推荐回复。修改时保留此结构。

编辑 `/home/admin/tianquan/backend/app/services/chat.py` 中的 `SYSTEM_PROMPT` 常量。

### 4.4 想修改广告过滤规则

编辑 `_AD_STRONG_PATTERNS` / `_AD_WEAK_PATTERNS` / `_UI_NOISE_PATTERNS` / `_BRAND_SOURCES`。

### 4.5 想修改学校简称映射

编辑 `backend/app/services/school_abbrev.py` 中的 `UNIVERSITY_ABBREVIATIONS` 字典。这是**唯一权威源**，前后端共用。

```bash
# 验证前后端条目一致
python3 -c "from backend.app.services.school_abbrev import UNIVERSITY_ABBREVIATIONS; print(len(UNIVERSITY_ABBREVIATIONS))"
```

### 4.6 启动服务

```bash
cd /home/admin/tianquan
docker-compose up -d
```

首次请求会触发 FTS 重建（跳过 excluded_articles），约 5-10 秒。

---

## 五、前端页面架构

### 5.1 路由表

| 路径 | 页面 | 说明 |
|------|------|------|
| `#/login` | Login.tsx | 登录 / 自动注册 |
| `#/` | Chat.tsx | AI 智能问答（首页） |
| ~~`#/recommend`~~ | ~~Recommend.tsx~~ | ~~选校推荐引擎（三维评分）~~ *v0.14 已删除，统一到 Chat* |
| `#/chat` | Chat.tsx | AI 智能问答 |
| `#/profile` | ProfilePage.tsx | 个人档案 |
| 外部 `/tianshu/` | tianshu/ | 天枢测评（独立页面） |

所有受保护路由通过 `AuthGuard`（`App.tsx`）守卫，未登录自动跳转 `#/login`。

### 5.2 核心前端模块

| 文件 | 职责 |
|------|------|
| `src/services/auth.ts` | 登录/登出/验证，默认授权码 `88888888`，7 天 session 过期 |
| `src/services/profile.ts` | 档案 CRUD（localStorage `iff_profile`），历史记录（`iff_history`） |
| `src/services/chat.ts` | AI 对话 API（流式 + 非流式） |
| `src/hooks/useChatSend.ts`（291 行） | 聊天核心逻辑：handleSend/doSendToAI/清空 |
| `src/hooks/useChatInput.ts`（30 行） | 输入状态 + Enter 发送处理 |
| `src/hooks/useChatScroll.ts`（23 行） | 滚动定位 + 回到底部按钮 |
| `src/services/api.ts` | 新闻 API / 授权码验证 |
| `src/utils/markdown.tsx` | 轻量 Markdown 渲染器 |
| `src/pages/Login.tsx` | 登录页，后端验证授权码 + 前端本地绑定 |
| `src/pages/Chat.tsx`（321 行） | AI 问答主页，多轮信息收集向导 + 档案预填 |
| `src/pages/ProfilePage.tsx` | 档案管理 + 查询历史 |
| `src/services/school.ts` | 学校简称映射前端缓存层（从后端 API 拉取） |

### 5.3 ProfileData 数据结构

```typescript
interface ProfileData {
  username?: string;         // 用户名
  email?: string;            // 邮箱
  auth_code?: string;        // 授权码（默认 88888888）
  school?: string;           // 学校
  original_major?: string;   // 专业
  gpa_score?: number;        // GPA 分数
  gpa_format?: string;       // 百分制 / 4分制 / 5分制 / 7分制 / 9分制 / 英制百分制
  target_countries?: string[];
  study_level?: string;      // 本科 / 硕士 / 博士 / 预科
  target_major?: string;     // 目标专业
  ielts?: number | null;
  toefl?: number | null;
  gre?: number | null;
  tianshu?: TianshuData;    // 天枢测评结果（只读）
  updated_at: string;
}
```

### 5.4 信息自动提取

`Chat.tsx` 中的 `extractInfo()` 从用户对话中自动提取档案信息（该函数是 `async`）：

| 字段 | 提取方式 |
|------|---------|
| GPA | 正则 `/(GPA\|均分\|绩点)\s*[:：]?\s*\d+(?:\/\d+)?/` |
| 学校 | 50+ 简称映射（从后端 `/api/school/abbreviations` 动态加载，缓存层在 `src/services/school.ts`），回退到 XX大学/XX学院 匹配 |
| 国家 | 25+ 别名映射（澳大利亚→澳洲，枫叶国→加拿大） |
| 专业 | 多层级匹配：`本科读/学/专业`、`专业[：:是为]`、`读/学 XXX`、`XXX专业`（不含专业课） |
| 目标专业 | `目标专业[：:是为]? XXX`，排除"其他/不限/还没想好"等占位词 |

**学校简称数据源**：`backend/app/services/school_abbrev.py` 是**唯一权威源**（49 条），前端通过 `GET /api/school/abbreviations` 拉取。修改简称只改后端一处即可。


提取后在符合条件时自动调用 `mergeChatInfo()` 保存到 localStorage。

首次对话会自动从 `iff_profile` 预填已有信息，避免重复追问。

### 5.5 信息收集向导（Chat.tsx 多轮追问）

选校场景下，系统通过以下流程收集完整背景信息：

1. 首次选校请求 → 从档案 + 消息提取已有信息
2. 如有缺失字段 → 逐个追问（学校/专业/GPA/目标国家/目标专业）
3. 用户每次回复都重新提取+合并，直到全部字段齐全
4. 收集完成后自动调用推荐引擎，并保存到个人档案

### 5.6 性能优化

- `MessageBubble` 使用 `memo()` + 自定义比较器，streaming 期间仅当前输出消息重渲染
- `renderMarkdown()` 结果通过 `useMemo` 缓存
- `onScroll` 解除对 `messages.length` 的依赖，使用 ref 避免回调重建

---

## 六、登录与授权

### 6.1 设计

前后端双层验证：后端验证授权码合法性，前端管理本地会话。

| 文件 | 说明 |
|------|------|
| `src/services/auth.ts` | `login()` / `logout()` / `isAuthenticated()`，含 7 天过期 |
| `src/pages/Login.tsx` | 登录页，先后端验证再前端绑定 |
| `src/App.tsx` | AuthGuard 路由守卫 |
| `backend/app/api/auth.py` | `POST /api/verify-auth-code` 后端授权码校验 |
| `backend/app/core/config.py` | `VALID_AUTH_CODES` 环境变量配置 |

### 6.2 登录流程

```
用户输入用户名 + 授权码
  → 前端调 POST /api/verify-auth-code 验证授权码是否在 VALID_AUTH_CODES 白名单
  → 不合法 → "授权码无效，请联系管理员"
  → 合法 → 前端本地绑定：首次绑定用户名+授权码，再次校验一致性
  → 写入 localStorage.iff_auth = { loggedIn, username, timestamp }
```

### 6.3 会话管理

- 会话标记：`localStorage.iff_auth` = `{ loggedIn, username, timestamp }`
- 过期策略：`isAuthenticated()` 检查 `Date.now() - timestamp > 7天`，超期自动清除
- 档案数据：`localStorage.iff_profile` = `ProfileData`
- 历史记录：`localStorage.iff_history`
- **重启容器后无需重新登录**（纯前端会话，不依赖后端 Session）

### 6.4 授权码配置

在 `.env` 中设置 `TIANQUAN_VALID_AUTH_CODES=码1,码2,...`，逗号分隔。留空则全部放行（兼容旧版）。当前已配置 30 个授权码。

---

## 七、推荐引擎

### 7.1 三维评分模型

**文件**：`backend/app/services/case_matcher.py`

| 维度 | 权重 | 说明 |
|------|------|------|
| GPA 匹配分 | 40% | 用户 GPA 在该校历史录取分布中的位置（p25/p50/p75 区间线性得分） |
| 学校排名分 | 30% | QS 排名越靠前 → 基础分越低 → 天然偏冲刺（QS#1-20=18, #21-50=22, #51-100=25, #101-200=28, #200+=30） |
| 案例证据分 | 30% | 同背景录取案例数：0例=0, 1-5例=10, 6-15例=18, 16+例=30 |

**分档阈值**：总分 ≥75 = 保底 | 55-74 = 匹配 | <55 = 冲刺

**冲刺校 GPA 提升建议**：计算需要多少百分点才能达到总分 55（匹配档），通过 `gpa_gap` 字段返回。

### 7.2 输出控制

| 规则 | 值 |
|------|-----|
| 每档上限 | 6 所 |
| 档内排序 | QS 排名升序 |
| 最终排序 | 冲刺 → 匹配 → 保底 |
| 非大学过滤 | 排除语言学校、国际学院、预科、分校区 |

### 7.3 数据来源

案例数据来自 `backend/data/advisor.db` 的 `cases` 表（约 17.6 万条）。GPA 百分位数据：
- 专业级：`school_major_gpa_percentiles` 表（同校 + 同专业类别 + 同学校层次的 p10/p25/p50/p75）
- 学校级回退：`real_case_probability.json`（同校 + 同层次的 p25/p50/p75）

### 7.4 Chat.tsx 重构历程（v0.14）

**起点**：单文件 1072 行，耦合场景定义/消息管理/信息收集/AI 调用/UI 渲染。

**拆分过程**：

| Phase | 提取内容 | 文件 | 行数 | 目标行数 |
|-------|---------|------|------|---------|
| 1 | MessageBubble 组件 | `components/MessageBubble.tsx` | 112 | 994 |
| 2 | EmptyState + Scene 配置 | `config/scenes.ts` + 内联 | 83+72 | 796 |
| 3 | 10 个工具函数 | `services/chat-helpers.ts` | 189 | 613 |
| 4A | 输入状态 Hook | `hooks/useChatInput.ts` | 27 | 595 |
| 4B | 滚动定位 Hook | `hooks/useChatScroll.ts` | 23 | 595 |
| 5 | 聊天核心逻辑（handleSend/doSendToAI） | `hooks/useChatSend.ts` | 291 | **321** |

**结果**：Chat.tsx 净减 751 行（1072→321），可维护性显著提升。

### 7.5 测试覆盖

`tests/test_case_matcher.py`（v0.14 新增）：
- **70 个测试用例**，覆盖 3D 评分、GPA 提分建议、案例聚合、档位划分、辅助函数
- 纯函数测试，**不依赖数据库/网络**
- 6 个 `skip`（依赖 sqlite 的函数标记占位）
- 运行：`python3 -m pytest tests/test_case_matcher.py -v`

### 7.6 推荐结果在 Chat 中的呈现

**v0.14 删除 Recommend 页面**（功能与 Chat 重叠），推荐结果统一由 Chat 呈现：

1. `recommend.run()` 输出的结构化数据通过 `_format_recommend_result()` 转为带章节标题的文本，注入 LLM system context
2. LLM 按以下格式组织回复：
   - `## 推荐院校` — 按国家 + 档位（冲刺/匹配/保底）列出学校，含 QS 排名、案例数、GPA 中位数、三维评分
   - `## 申请策略` — 简要列出当前背景的补充路径（预科/桥梁/双录取等），无则提示"适合直录"
3. `recommend_payload` 字段包含完整结构化数据，供前端未来扩展（当前不使用）

---

## 八、部署与构建





### 8.1 双轨部署

| 目标 | 方式 | 地址 |
|------|------|------|
| GitHub Pages | GitHub Actions 自动构建部署 | `https://rongshou.github.io/iff/tianquan/` |
| 自托管服务器 | GitHub Actions webhook → Docker rebuild | `http://47.93.149.29/tianquan/` |

### 8.2 CI/CD 流程

```
git push master
  → GitHub Actions (.github/workflows/deploy.yml)
    → npm ci → npm run build
    → 部署到 GitHub Pages
    → POST webhook → 47.93.149.29:7800
      → git pull → npm run build → docker restart tianquan-nginx
```

### 8.3 Webhook 配置

- Webhook 服务：`webhook-server.js`，运行在宿主机端口 7800
- Nginx 代理：`nginx.conf` 中 `/webhook/` → `host.docker.internal:7800`
- Docker extra_hosts：`docker-compose.yml` 中 `host.docker.internal:host-gateway`
- 密钥文件：`/home/admin/tianquan/.webhook-secret`（自动生成）

### 8.4 手动部署（服务器）

```bash
cd /home/admin/tianquan
git pull origin master
docker compose up -d --build
```

### 8.5 Docker 构建注意事项

- Node 阶段使用 `node:20-alpine`，需安装 bash（`apk add --no-cache bash`）
- 构建脚本 `scripts/build-prod.sh` 依赖 bash，不可改为 sh
- Nginx 配置文件变更后需要重建容器才能生效

### 8.6 本地开发

```bash
cd /home/admin/tianquan
npm run dev          # Vite dev server → localhost:5173
```

API 代理配置在 `vite.config.ts`：`/api` → `http://localhost:3470`。

---

## 九、相关路径速查（更新）

| 文件/路径 | 用途 |
|-----------|------|
| `/home/admin/tianquan/src/` | 前端源码 |
| `/home/admin/tianquan/backend/app/` | 后端源码 |
| `/home/admin/tianquan/backend/app/services/case_matcher.py` | 推荐引擎核心（三维评分 + 案例匹配） |
| `/home/admin/tianquan/backend/app/api/auth.py` | 授权码验证 API |
| `/home/admin/tianquan/backend/app/services/school_abbrev.py` | 学校简称映射权威源（49 条） |
| `/home/admin/tianquan/backend/app/api/school.py` | `GET /api/school/abbreviations` |
| `/home/admin/tianquan/src/services/school.ts` | 前端学校简称缓存层 |
| `/home/admin/tianquan/tests/test_case_matcher.py` | 推荐引擎单元测试（70 用例） |
| `/home/admin/tianquan/backend/data/advisor.db` | 应用数据库 |
| `/home/admin/werss/data/db.db` | 源文章库（只读） |
| `/home/admin/tianquan/.webhook-secret` | Webhook 密钥 |
| `/home/admin/tianquan/nginx.conf` | Nginx 配置 |
| `/home/admin/tianquan/docker-compose.yml` | Docker 编排 |
| `/home/admin/tianquan/Dockerfile` | nginx 容器构建

---
---

## 十、LLM 配置与优化 {#ten}

### 10.1 模型选择

| 项 | 配置值 | 说明 |
|---|--------|------|
| Provider | `opencode` | 仅支持 OpenCode API |
| Base URL | `https://opencode.ai/zen/go/v1` | OpenCode CLI 路由 |
| 主模型 | `deepseek-v4-flash` | 付费模型，选校场景输出质量好 |
| 后备模型 | `minimax-m2.7` | 主模型 401/429/5xx 自动切换 |
| max_tokens | `8192` | 通过 `TIANQUAN_LLM_MAX_TOKENS` 环境变量配置 |

**配置位置**：`docker-compose.yml`（环境变量） + `backend/app/core/config.py`（默认值） + `.env`（实际运行时值）

### 10.2 推荐结果缓存

**文件**：`backend/app/services/recommend.py`

减少同 profile 反复触发推荐引擎带来的高延迟：

| 项 | 值 |
|---|-----|
| 缓存键 | profile 的 SHA256（排除 null 字段，排序序列化） |
| TTL | 300 秒（5 分钟） |
| 最大条目 | 64 条（超限淘汰最旧） |
| 存储 | 进程内内存（dict，单容器适用） |

```python
def _profile_key(profile: dict) -> str:
    """忽略 dynamic 字段，稳定排序后 hash"""
    relevant = {k: v for k, v in profile.items() if v is not None}
    raw = json.dumps(relevant, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(raw.encode()).hexdigest()
```

### 10.3 推荐触发关键词

**文件**：`backend/app/services/chat.py`

vs 旧版（旧版 1 个列表，含 18 个词，任何一词命中即触发）

**新版**：
> 2016-01-01 v0.14 split into STRONG (12) + WEAK (9)；不再硬等所有字段齐全才触发

```python
# 强信号：含任一即触发选校推荐
STRONG_RECOMMEND_KEYWORDS = [
    "选校", "选校定位", "学校推荐", "推荐学校", "匹配学校",
    "定位", "冲刺", "保底", "主申",
    "录取概率", "录取案例",
    "留学选校",
]

# 弱信号：需要至少命中 2 个才触发
WEAK_RECOMMEND_KEYWORDS = [
    "GPA", "gpa", "均分", "绩点", "分数",
    "留学申请", "申请留学",
    "录取", "申请",
]
```

同时新增 `NON_RECOMMEND_KEYWORDS` 排除名单（文书/签证等场景不触发推荐）：

```python
NON_RECOMMEND_KEYWORDS = [
    "文书","PS","个人陈述","简历","CV","推荐信","推荐人",
    "签证","F-1","Tier 4","I-20","面签","签证材料",
]
```

### 10.4 max_tokens 调整

| 日期 | 旧值 | 新值 | 理由 |
|------|------|------|------|
| 2026-07-16 | 4096 | **8192** | 选校回复因 4096 token 上限频繁截断（`finish_reason="length"`），末尾显示「回复"继续"让 AI 接着写」但无实际续写逻辑；翻倍后基本覆盖完整选校输出 |

**截断检测**：`chat.py:349-354` 检测 `finish_reason == "length"` 时追加截断提示，但无自动续写。当前方案是提高上限从根本上避免截断。

### 10.5 Fallback 重试逻辑

旧版：单次请求失败立即抛异常。

新版：主模型失败（HTTP 401/402/429/500/502/503）时自动切换到后备模型重试一次：

```python
for attempt in range(2):
    resp = await client.post(url, json=payload, headers=headers)
    if resp.is_success:
        return data
    if attempt == 0 and fallback_model and resp.status_code in (401, 402, 429, 500, 502, 503):
        payload["model"] = fallback_model
        continue
    resp.raise_for_status()
```

### 10.6 常见问题

**Q: 为什么用 `/zen/go/v1` 而不是 `/zen/v1`？**
A: `/zen/go/v1` 是 OpenCode CLI 路由，支持付费模型（如 `deepseek-v4-flash`、`minimax-m2.7`）。`/zen/v1` 仅支持免费模型（`*-free` 后缀）。当前使用付费模型以获得更好的选校输出质量。

**Q: 模型响应慢怎么办？**
A: 当前 `deepseek-v4-flash` 非流式单次约 6-15s。可选的优化方向：
- 使用流式响应（前端 `stream=true`）
- 增大推荐缓存 TTL（当前 300s）
- 考虑切回 lighter 模型处理非选校类简单问答

---

## 十一、天枢（tianshu）登录保护

**文件**：
- `tianshu/index.html` — 内联 auth 检查脚本
- `src/pages/Login.tsx` — 登录页 redirect 参数处理
- `src/services/auth.ts` — `isAuthenticated()` 共享函数（React 端使用）

### 11.1 保护机制

天枢是独立静态页面（纯 HTML/JS，不依赖 React），无法使用 React 的 `AuthGuard`。因此在其 `index.html` `<head>` 中内联了独立的 auth 检查逻辑：

```javascript
// 检查 localStorage.iff_auth，与 React 端同 key
var AUTH_KEY = "iff_auth";
var SESSION_MAX_AGE = 7 * 24 * 60 * 60 * 1000;

function isAuthenticated() {
    var raw = localStorage.getItem(AUTH_KEY);
    if (!raw) return false;
    var data = JSON.parse(raw);
    if (data.loggedIn !== true) return false;
    if (Date.now() - data.timestamp > SESSION_MAX_AGE) {
        localStorage.removeItem(AUTH_KEY);
        return false;
    }
    return true;
}

if (!isAuthenticated()) {
    var redirect = encodeURIComponent(window.location.pathname + window.location.hash);
    window.location.replace("/tianquan/#/login?redirect=" + redirect);
}
```

### 11.2 Redirect 流程

```
用户访问 /tianshu/ → no auth → window.location.replace 到
  /tianquan/#/login?redirect=%2Ftianshu%2F
    → 用户在天权登录
      → Login.tsx 检测 redirect 参数
        → 外部路径（非 /tianquan/ 开头）→ window.location.href = redirectTo
        → SPA 内部路径 → navigate(redirectTo, { replace: true })
```

### 11.3 共享会话

天枢和天权共享同一个 `localStorage`（同源 `localhost:8080`），因此天枢登录后天权自动可用，反之亦然。会话有效期 7 天，与天权一致。

### 11.4 pre-commit 自动构建

修改 `tianshu/index.html` 或 `src/` 下的文件后，git commit 时会自动触发：

```bash
# .git/hooks/pre-commit（内部行为）
npm run build    # 构建产物到 dist/
```

构建产物（`dist/tianshu/`、`dist/tianquan/`）被 `.gitignore` 忽略，只供 Docker 镜像和 GitHub Actions 使用。

---

## 十二、数据库维护 {#twelve}

### 12.1 数据库概览

| 数据库 | 路径 | 用途 |
|--------|------|------|
| advisor.db | `backend/data/advisor.db` | 应用数据库（cases、schools、excluded_articles、FTS 等 61 张表） |
| werss.db | `/home/admin/werss/data/db.db` | 源文章库（只读挂载） |

### 12.2 备份与恢复

备份位置：`/home/admin/tianquan/backup/advisor/data/advisor.db`

恢复方法：
```bash
cp /home/admin/tianquan/backup/advisor/data/advisor.db /home/admin/tianquan/backend/data/advisor.db
docker compose restart tianquan-backend
```

> ⚠️ **恢复后务必重跑排名更新脚本**，否则 QS/US News 排名会回退到旧版本：
> ```bash
> python3 /home/admin/tianquan/scripts/rankings/update_qs_2027.py
> python3 /home/admin/tianquan/scripts/rankings/update_usnews.py
> ```
> 这两个脚本同时更新 live DB 和备份 DB，确保数据一致。

### 12.3 已知问题

| 问题 | 表现 | 恢复 |
|------|------|------|
| `database disk image is malformed` | 所有 SQLite 操作失败 | 从备份恢复 |
| WAL 日志未正确 checkpoint | 容器意外停止导致 `-shm`/`-wal` 残留 | 删除 `*.db-shm` `*.db-wal` 后用 PRAGMA integrity_check 验证 |