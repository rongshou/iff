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

编辑 `/home/admin/tianquan/backend/app/services/chat.py` 中的 `SYSTEM_PROMPT` 常量。

### 4.4 想修改广告过滤规则

编辑 `_AD_STRONG_PATTERNS` / `_AD_WEAK_PATTERNS` / `_UI_NOISE_PATTERNS` / `_BRAND_SOURCES`。

### 4.5 想修改学校名称解析规则

编辑 `_parse_undergrad()` 中的 `_extract_best_university()`、缩写映射表、院校层级关键词。

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
| `#/explore` | Explore.tsx | 留学工具箱（MBTI + 时间线） |
| `#/profile` | ProfilePage.tsx | 个人档案 |
| 外部 `/tianshu/` | tianshu/ | 天枢测评（独立页面） |

所有受保护路由通过 `AuthGuard`（`App.tsx`）守卫，未登录自动跳转 `#/login`。

### 5.2 核心前端模块

| 文件 | 职责 |
|------|------|
| `src/services/auth.ts` | 登录/登出/验证，默认授权码 `88888888` |
| `src/services/profile.ts` | 档案 CRUD（localStorage `iff_profile`），历史记录（`iff_history`） |
| `src/services/chat.ts` | AI 对话 API（流式 + 非流式） |
| `src/services/api.ts` | 推荐引擎 / 新闻 API |
| `src/utils/markdown.tsx` | 轻量 Markdown 渲染器 |
| `src/pages/Login.tsx` | 登录页，首次访问自动注册 |
| `src/pages/Chat.tsx` | AI 问答主页，含信息自动提取 |
| `src/pages/Explore.tsx` | MBTI 测评 + 申请时间线 |
| `src/pages/Recommend.tsx` | 选校推荐引擎页面 |
| `src/pages/ProfilePage.tsx` | 档案管理页 |

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

`Chat.tsx` 中的 `extractInfo()` 从用户对话中自动提取档案信息：

| 字段 | 提取方式 |
|------|---------|
| GPA | 正则 `/(GPA\|均分\|绩点)\s*[:：]?\s*\d+(?:\/\d+)?/` |
| 学校 | 45+ 简称映射（北邮→北京邮电大学），回退到 XX大学/XX学院 匹配 |
| 国家 | 25+ 别名映射（澳大利亚→澳洲，枫叶国→加拿大） |
| 专业 | `专业：XXX` 或 `目标专业：XXX` 模式，到标点终止 |

提取后在符合条件时自动调用 `mergeChatInfo()` 保存到 localStorage。

提取逻辑与后端 `chat.py` 的 `_extract_profile_from_history()` 并行——前端负责即时反馈，后端负责推荐引擎输入。

### 5.5 性能优化

- `MessageBubble` 使用 `memo()` + 自定义比较器，streaming 期间仅当前输出消息重渲染
- `renderMarkdown()` 结果通过 `useMemo` 缓存
- `onScroll` 解除对 `messages.length` 的依赖，使用 ref 避免回调重建

---

## 六、登录系统

### 6.1 设计

基于 localStorage 的本地授权，不使用服务端用户系统。

| 文件 | 说明 |
|------|------|
| `src/services/auth.ts` | `login()` / `logout()` / `isAuthenticated()` |
| `src/pages/Login.tsx` | 登录页 |
| `src/App.tsx` | AuthGuard 路由守卫 |

### 6.2 登录流程

```
首次访问 → 无档案或档案无用户名 → 输入用户名 + 88888888 → 自动创建档案并登录
已有档案 → 验证用户名 + 授权码 → 登录成功
```

### 6.3 会话存储

- 会话标记：`localStorage.iff_auth` = `{ loggedIn, username, timestamp }`
- 档案数据：`localStorage.iff_profile` = `ProfileData`
- 历史记录：`localStorage.iff_history`

---

## 七、部署与构建

### 7.1 双轨部署

| 目标 | 方式 | 地址 |
|------|------|------|
| GitHub Pages | GitHub Actions 自动构建部署 | `https://rongshou.github.io/iff/tianquan/` |
| 自托管服务器 | GitHub Actions webhook → Docker rebuild | `http://47.93.149.29/tianquan/` |

### 7.2 CI/CD 流程

```
git push master
  → GitHub Actions (.github/workflows/deploy.yml)
    → npm ci → npm run build
    → 部署到 GitHub Pages
    → POST webhook → 47.93.149.29:7800
      → git pull → npm run build → docker restart tianquan-nginx
```

### 7.3 Webhook 配置

- Webhook 服务：`webhook-server.js`，运行在宿主机端口 7800
- Nginx 代理：`nginx.conf` 中 `/webhook/` → `host.docker.internal:7800`
- Docker extra_hosts：`docker-compose.yml` 中 `host.docker.internal:host-gateway`
- 密钥文件：`/home/admin/tianquan/.webhook-secret`（自动生成）

### 7.4 手动部署（服务器）

```bash
cd /home/admin/tianquan
git pull origin master
docker compose up -d --build
```

### 7.5 Docker 构建注意事项

- Node 阶段使用 `node:20-alpine`，需安装 bash（`apk add --no-cache bash`）
- 构建脚本 `scripts/build-prod.sh` 依赖 bash，不可改为 sh
- Nginx 配置文件变更后需要重建容器才能生效

### 7.6 本地开发

```bash
cd /home/admin/tianquan
npm run dev          # Vite dev server → localhost:5173
```

API 代理配置在 `vite.config.ts`：`/api` → `http://localhost:3470`。

---

## 八、相关路径速查（更新）

| 文件/路径 | 用途 |
|-----------|------|
| `/home/admin/tianquan/src/` | 前端源码 |
| `/home/admin/tianquan/backend/app/` | 后端源码 |
| `/home/admin/tianquan/backend/data/advisor.db` | 应用数据库 |
| `/home/admin/werss/data/db.db` | 源文章库（只读） |
| `/home/admin/tianquan/.webhook-secret` | Webhook 密钥 |
| `/home/admin/tianquan/nginx.conf` | Nginx 配置 |
| `/home/admin/tianquan/docker-compose.yml` | Docker 编排 |
| `/home/admin/tianquan/Dockerfile` | nginx 容器构建
