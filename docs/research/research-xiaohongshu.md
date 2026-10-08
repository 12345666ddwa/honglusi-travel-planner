# 小红书攻略获取方案 可行性调研报告

> 项目：中国国内旅游规划网站（本地内测版）
> 调研日期：2026-08-14
> 调研人：Hermes 子代理
> 状态：调研中（边查边写）

---

## 0. 继承的已有实测结论（上一轮调研，本报告不再重复实测）

1. 小红书网页/API 有 WAF 防护（acw_tc cookie），海外 IP 直接返回 `300012「IP存在风险」`；本项目运行在中国网络（Windows 本地），可能避开海外 IP 问题，但 WAF 仍存在。
2. 无签名的搜索 API 返回 404（jarvis-gateway invoker failed）——即直接调 `/api/sns/web/v1/search/notes` 不带 x-s 签名不可行。
3. 重大线索：GitHub 存在「cn-scraper-mcp」项目（2026-07 仍活跃），自称支持 XHS 等中国站点爬取，需深入调研其 XHS 引擎实现方式。
4. Bing RSS 搜索可用（搜狗微信搜索也可尝试）。

---

## A. cn-scraper-mcp 深度调研 + 同类项目扫描

### A1. cn-scraper-mcp 基本盘（数据来自 GitHub API 实测，2026-08-14 拉取）

| 项 | 值 |
|---|---|
| 仓库 | `goesByhc/cn-scraper-mcp`（https://github.com/goesByhc/cn-scraper-mcp） |
| Star | **21**（实查，2026-08-14） |
| Fork | 2 |
| Open Issues | 1 |
| 语言 | Python |
| License | **MIT** |
| 创建时间 | 2026-07-13 |
| 最近推送 | **2026-07-29**（v0.5.0 发布准备） |
| 仓库元数据更新时间 | 2026-08-13 |
| 定位 | 「Let AI agents search the Chinese internet via MCP」——淘宝/京东/小红书/知乎/微博/B站/知识星球/豆瓣/大众点评等 |

**维护状态判定**：2026-07 创建后两周内高频迭代（v0.3.0 → v0.5.0，含 Bilibili、JD、豆瓣、点评等引擎），最近推送距今约 2.5 周，属于**活跃但社区极小**的新项目（21 stars，几乎无社区反馈可参考）。

### A2. cn-scraper-mcp 的 XHS 引擎技术实现（源码级确认，非猜测）

源码：`src/cn_scraper_mcp/engines/xiaohongshu.py`（741 行）。**核心结论：没有做 x-s 签名逆向，也没有直接调 API。方案是「本地真实浏览器（Chrome CDP）+ 用户登录 Cookie + DOM 抓取」，让小红书网页自己的 JS 去完成签名请求。**

关键机制：

1. **浏览器驱动**：通过 CDP（Chrome DevTools Protocol）驱动本地浏览器。首选一个叫 **Obscura** 的轻量浏览器（内置反检测 stealth，约 30MB 内存，端口 9222）；未安装则回退到**有头 Chrome**（独立 profile `~/.xhs_cdp_profile`，端口 9251）。明确禁止 headless 云端浏览器——注释写明「Cloud/datacenter IP → error_code=300012，REJECTED BEFORE checking cookies」。
2. **登录态注入**：需要的 Cookie 字段：`web_session, a1, webId, gid, abRequestId, xsecappid, webBuild`。通过 CDP `Network.setCookie` 注入 `.xiaohongshu.com` 域。Cookie 存放于 `$XHS_COOKIES_FILE` 或 `~/.cn-scraper-cookies/xiaohongshu.json`。
3. **登录引导（关键工具）**：MCP 工具 `guided_login(platform="xiaohongshu")` —— 自动打开本地 Chrome 进入官方登录页（login_url=`https://www.xiaohongshu.com/login`），**用户扫码后，工具通过 CDP 自动收割完整 Cookie（含 HttpOnly），存到本地**。也有 `harvest_cookies()` 支持从已登录的远程调试 Chrome 直接收割。登录成功判定信号：`web_session` 出现。
4. **Cookie 过期判断**：本地文件级启发式——超过 24 小时（`STALE_HOURS=24`）判为「几乎肯定过期」；引擎另有页面级检测：URL/正文出现 `login`/`passport`/「登录」→ `XHS_LOGIN_EXPIRED`；出现 `error_code=300012`/「IP存在风险」→ `XHS_IP_RISK`；出现「验证/滑块/人机验证」→ `XHS_CAPTCHA`。
5. **搜索流程**：直接导航到 `https://www.xiaohongshu.com/search_result?keyword={kw}&source=web_explore_feed&type=51`，等页面加载（wait=5s），用注入的 JS 提取笔记卡片：以 `<a href*="xsec_token">` 为信号（搜索结果卡片才带 xsec_token），正则 `/^\/(explore|search_result|discovery\/item)\/([0-9a-f]{16,})/` 拿 noteId，DOM 层层向上找标题/作者/点赞。
6. **笔记详情**：拿到 `noteId + xsec_token` 后导航笔记页，读 `window.__INITIAL_STATE__.note.noteDetailMap[noteId]` 拿标题/正文/标签/互动数。
7. **评论**：仅抓首屏评论（先试 `__INITIAL_STATE__`，回退 DOM 选择器），不做分页。
8. **MCP 工具面**：`xiaohongshu_search` / `xiaohongshu_note` / `xiaohongshu_comments`。
9. **部署形态**：`pip install cn-scraper-mcp`；支持 stdio 或远程 HTTP 模式；提供 Docker 镜像（内置 Chromium + no-sandbox），但 README 明确警告「小红书仍需住宅 IP——数据中心 IP 会被封」，即 Docker 部署对 XHS 基本无效，必须本地浏览器。

**对它的评价**：技术路线务实且与本项目约束高度契合（中国网络 + Windows 本地 + 有真实浏览器），MIT 协议可自由商用集成。但 21 stars 的小项目，代码健壮性未经大规模验证，且它依赖 Obscura 这个第三方轻量浏览器（可回退 Chrome）。核心风险与所有浏览器方案相同：风控/验证码打断时需人工介入。

### A3. 同类项目 2025-2026 维护状态（GitHub API 实查，2026-08-14）

| 项目 | Stars | 最近推送 | 状态 | 技术要点 |
|---|---|---|---|---|
| **NanmiCoder/MediaCrawler** | **62,320** | **2026-08-12**（2天前） | ✅ 非常活跃 | 纯 Python 实现 x-s 签名（`media_platform/xhs/xhs_sign.py`：自定义 Base64 表 + CRC32 查表，**代码内版权标注 2025**，说明 2025 年后仍在维护签名算法）；另有 `playwright_sign.py`（Playwright 注入式签名）与 `login.py`（Playwright 扫码登录）。**License: NON-COMMERCIAL LEARNING LICENSE 1.1（禁止商业用途！）** |
| **JoeanAmier/XHS-Downloader** | **12,335** | **2026-08-13**（1天前） | ✅ 非常活跃 | JavaScript（Node），作品链接提取/采集/下载，同样依赖登录 Cookie |
| **cv-cat/Spider_XHS** | **7,267** | 2026-07-29 | ✅ 活跃 | 「小红书全域运营解决方案」，采集+运营 |
| **xhs996/xhs_spider** | 364 | **2026-08-10** | ✅ 活跃 | 自述涵盖「小红书 Cookie、xsec_token 生成、App shield 算法、web 算法、逆向」——App 端算法逆向路线 |
| Guing/xhs-downloader-skill | 8 | 2026-02-05 | 一般 | 面向 AI 编码助手（Claude Code 等）的 XHS 下载 Skill，与本项目「让 Agent 拿攻略」目标相似，但体量小 |
| lewis-007/MediaCrawler 等 fork | ≤508 | 2024-03 前后 | ❌ 已死 | 老 fork 均停更 |

**两条技术路线总结**：
- **路线一（签名直连 API）**：MediaCrawler / Spider_XHS。优势：不用浏览器、速度快；劣势：x-s 签名算法会随小红书反爬升级而失效（需持续跟进上游），MediaCrawler 的非商业 License 阻碍直接商用，Spider_XHS 等多为商业引流项目。
- **路线二（真实浏览器 + 登录 Cookie）**：cn-scraper-mcp（以及 XHS-Downloader 的登录方式）。优势：无需逆向签名、天然带真实浏览器指纹、中国住宅 IP + 真实登录态下稳定性最高；劣势：依赖浏览器环境、有验证码/风控时需人工、频率受限。

---

## B. Playwright + 扫码登录 Cookie 方案最新可行性搜证

### B1. 方案形态

标准做法（cn-scraper-mcp / MediaCrawler / OpenCLI 三家一致）：**Playwright（或原生 CDP）连接本地 Chrome → 弹出小红书官方登录页 → 用户手机扫码 → 浏览器内完成登录 → 持久化 Cookie 或复用 Chrome Profile → 后续请求复用登录态**。

- cn-scraper-mcp：`guided_login("xiaohongshu")` 扫码后经 CDP 收割完整 Cookie（含 HttpOnly）存入 JSON；或 `harvest_cookies()` 从已登录 Chrome 直接收割。
- MediaCrawler：`login.py` 用 Playwright 拉起浏览器扫码；`config/base_config.py` 提供 `ENABLE_CDP_MODE=True` 连接用户本地已登录 Chrome（xhs/dy 两个平台开放 CDP 模式），官方文档明示这是规避 Webdriver 检测的推荐路径。
- OpenCLI（`@jackwener/opencli`，npm 全局工具 + Chrome 扩展，136 站点适配器含小红书）：口号即「Reuse Chrome login, zero risk」，直接复用用户日常 Chrome 登录态，不自建自动化会话。

### B2. 2025-2026 社区实测证据（全部来自 GitHub 实查，2026-08-14）

**核心证据 1：MediaCrawler Issue #915（2026-06-12 开，至今未关，7 条评论）**
标题「[风控] 只是在小红书上查看帖子和下载视频，被系统提示检查到AI操作」。用户环境：Windows 10 + Python 3.10 + 无 IP 代理 + **开 VPN** + `ENABLE_CDP_MODE=True`。仅浏览/下载就被弹「检测到AI操作」。
- 官方 bot（引维护者）确认：「这是小红书近期加强了风控措施的结果，并非使用不当」「2026 年初多位用户报告类似问题，**包括账号被永久封禁的情况**（见 #865）」。
- 维护者给出的缓解措施：① 最新代码支持连接**自己的真实浏览器复用登录态**（不走自动化那一套，容易检测）；② `CDP_HEADLESS=False`（无头模式更容易被检测）；③ 合理控频。
- 评论区补充：另一用户「账号仅爬了一次数据，直接给我提示了」；有用户改用 **OpenCLI**（复用真实 Chrome 登录态）「目前还没啥问题」；有用户「上代理控制爬取频率就好一点」。疑点：该用户开着 VPN 被风控，与「海外/代理 IP 风险高」的已有结论一致。

**核心证据 2：MediaCrawler Issue #958（2026-08-11，closed）**
为 XHS 作者主页/笔记 HTML 回退路径新增阻断码识别：HTTP 401/403/429、业务码 **300011（账号安全限制）**、**300012（IP 限制）**。说明到 2026 年 8 月，这两种阻断对爬虫已是常态，代码需作为一等公民处理。

**核心证据 3：MediaCrawler Issue #963（2026-08-12，open）**
新功能「`--check_session` 预检命令，开爬前确认 cookie/代理是否可用」——从侧面证实 **cookie 过期/失效是用户高频痛点**。

**核心证据 4：cookie 有效期经验值**
- cn-scraper-mcp 源码 `STALE_HOURS=24`：cookie 文件超过 24 小时判为「几乎肯定过期」。即 web_session 登录态通常约 **24 小时**有效，需定期重扫。
- 若采用 CDP 复用用户日常 Chrome Profile（用户平时就在刷小红书），登录态与用户日常使用同步滚动，实际存活期可远超 24h，无需单独维护。

**核心证据 5：路线共识**
Gitee 的 MediaCrawler 镜像 README：「MediaCrawler 目前已经支持使用 playwright 连接你本地的 Chrome 浏览器了，一些因为 Webdriver 导致的问题迎刃而解了」。2026 年社区对「真实浏览器 + 真实登录态」已是共识路线，纯自动化（webdriver/headless）路线被普遍弃用。

### B3. 可行性结论（针对本项目场景）

| 维度 | 结论 |
|---|---|
| 技术可行性 | ✅ 完全可行。Playwright/Python 均有成熟实现（cn-scraper-mcp MIT 可直接抄/复用），零签名逆向成本 |
| 登录态维持时长 | web_session 约 24h（社区经验值）；复用用户日常 Chrome Profile 可显著延长 |
| 风控触发条件 | 高频、headless、webdriver 指纹、VPN/机房 IP → 触发 300011/300012/「AI操作」提示甚至封号。**本项目为低频查询（每次行程规划搜几条攻略），风险等级低** |
| 注意事项 | ① 禁用 headless、禁用 VPN/代理；② 用「小号」登录，勿用主账号（#915 显示单次触发即可能被标记）；③ 每 24h 或探测到登录失效时提醒用户重扫；④ 保持人工可控频率 |
| 建议落地形态 | 参照 cn-scraper-mcp：启动时检测登录态 → 失效则拉起 Chrome 让用户扫码 → CDP 收割 cookie → 导航 `search_result` 页用 JS 提取 DOM（xsec_token 方案），详情读 `__INITIAL_STATE__`。或直接复用用户日常 Chrome（CDP attach），零 cookie 管理成本 |

---

## C. 降级链路（小红书登录态失效/风控时的替代数据源）

> 原则：小红书是首选，但不是唯一。风控打断时不阻塞规划流程，自动降级继续。

| 层级 | 数据源 | 获取方式 | 内容质量 | 状态 |
|---|---|---|---|---|
| L1 | 小红书 | 本地 Chrome + cookie（本报告 A/B 方案） | ⭐⭐⭐ 真实体验、小众玩法最强 | ✅ 可行（需登录态） |
| L2 | 马蜂窝 | 网页版搜索页可无登录抓取 | ⭐⭐⭐ 攻略结构化好、景点/美食清单齐全 | ✅ 可行 |
| L3 | 携程攻略/社区 | 网页版攻略页 | ⭐⭐ 官方感强、广告多 | ✅ 可行（需甄别广告） |
| L4 | 大众点评 | 网页版可搜（部分需登录） | ⭐⭐ 美食/住宿价格参考 | ⚠️ 部分内容需登录 |
| L5 | 搜索快照 | Bing RSS / 百度 / 搜狗微信搜「目的地 攻略」 | ⭐⭐ 兜底，能找到 L2/L3 文章链接 | ✅ 已验证可用 |

**降级触发规则**：小红书 cookie 失效（24h）且用户不在场重扫 → 自动切 L2/L3；刑部对 L3/L5 来源额外加强广告甄别。

**落地行动项（M1 样板测试时实测）**：L2 马蜂窝搜索页的实际可抓性、L4 大众点评未登录时的可见范围。

---

## D. 最终推荐方案（汇总）

1. **主路线**：复用 `cn-scraper-mcp`（MIT）的 XHS 引擎思路——本地 Chrome CDP + 扫码登录 cookie + DOM 抓取。直接 pip 安装它，或把其 xiaohongshu.py（741 行）核心逻辑抄进本项目（MIT 允许）。
2. **登录态管理**：优先「CDP attach 用户日常 Chrome」（用户平时刷小红书=登录态自动滚动）；退而求其次「独立 profile + 24h 提醒重扫」。
3. **频率纪律**：每次行程规划仅搜索 3~5 个关键词，详情页 ≤10 篇，绝不批量。低频=低风控。
4. **账号纪律**：用小号登录（单次触发可能被标记，见 B2 证据 1）。
5. **兜底**：L2-L5 降级链常备，任何一层失效都不阻塞交付。




