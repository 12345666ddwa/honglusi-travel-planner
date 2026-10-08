# GitHub AI 旅行规划 / 多Agent 行程生成开源项目调研报告

> **调研日期**：2026-08-14
> **调研方法**：GitHub Search API 多关键词检索（travel planner LLM / trip planner AI agent / multi-agent travel planner / travel itinerary generator / travel langgraph / trip planner crewai 等），对候选项目逐一抓取仓库元数据、README 与核心 Agent 定义源码进行核实。
> **数据口径**：所有 star 数为 GitHub API 实时返回的真实数值；更新时间取仓库 `pushed_at` 字段。
> **用途**：为「三省六部」多Agent 旅游规划网站（需求解析/攻略采集/信息核验/预算核算/路线测算/方案草拟）提供架构参考。

---

## 一、总览对比表

| 项目 | Star | 语言/框架 | 类型 | 最近提交 | 对本项目价值 |
|---|---|---|---|---|---|
| [liketrek/TREK](https://github.com/liketrek/TREK) | 12,184 | TypeScript/NestJS+React | 自托管旅行规划产品 | 2026-08-13 | ⭐⭐⭐ UI/协作/MCP 参考 |
| [OSU-NLP-Group/TravelPlanner](https://github.com/OSU-NLP-Group/TravelPlanner) | 538 | Python | 学术基准(ICML'24) | 2026-05-24 | ⭐⭐⭐ 约束验证体系 |
| [LAMDA-NeSy/ChinaTravel](https://github.com/LAMDA-NeSy/ChinaTravel) | 121 | Python | 学术基准(ICLR'26, IJCAI 竞赛官方基准) | 2026-08-13 | ⭐⭐⭐⭐ 可执行约束DSL |
| [tonykipkemboi/trip_planner_agent](https://github.com/tonykipkemboi/trip_planner_agent) | 143 | Python/CrewAI | 多Agent应用(经典示例) | 2024-06-19 | ⭐⭐ 三Agent流水线 |
| [shaheennabi/Production-Ready-TripPlanner-Multi-AI-Agents-Project](https://github.com/shaheennabi/Production-Ready-TripPlanner-Multi-AI-Agents-Project) | 77 | Python/Taskflow AI | 多Agent应用 | 2025-03-04 | ⭐⭐ 角色分工+成本选型 |
| [TBice123123/travel-planner-assistant](https://github.com/TBice123123/travel-planner-assistant) | 58 | Python/LangGraph deepagents | 多Agent应用(中文) | 2025-10-13 | ⭐⭐ 国产模型适配 |
| [kbhujbal/Multi-Agent-AI-Travel-Advisor](https://github.com/kbhujbal/Multi-Agent-AI-Travel-Advisor) | 56 | Python/CrewAI+FastAPI | 多Agent应用 | 2026-04-12 | ⭐⭐⭐ 「AI只做分析」原则 |
| [shouzhuoshouzhuo/FloatTrip](https://github.com/shouzhuoshouzhuo/FloatTrip) | 55 | Python/LangGraph+FastAPI | 多Agent应用(中文) | 2026-08-13 | ⭐⭐⭐⭐⭐ 架构最贴近本项目 |
| [Haohao-end/Ctrip-Style-AI-Travel-Assistant](https://github.com/Haohao-end/Ctrip-Style-AI-Travel-Assistant) | 54 | Python/LangGraph | 多Agent应用 | 2026-01-10 | ⭐⭐⭐ 安全/敏感工具分离 |
| [alexlmoney83-oss/travel-planning-agent](https://github.com/alexlmoney83-oss/travel-planning-agent) | 46 | Python/LangChain+MCP | 多Agent应用(中文) | 2025-12-07 | ⭐⭐⭐ 国产数据源MCP |

**未入选但值得知晓**：
- `bcefghj/multi-agent-travel-planner`（278⭐）：中文多Agent旅游规划，但定位是"面试全套资料/八股文"学习仓库，非产品级参考。
- `adl1995/trip-planner`（368⭐）：经典 CLI 行程规划器，**2024-02 起停止维护**，不推荐参考架构。
- `LeeFly-cn/TripStar-Java`（52⭐）：Spring AI Alibaba 多Agent，Java 技术栈与本项目路线差异大，仅备注。
- `vikrambhat2/MultiAgents-with-Langgraph-TravelItineraryPlanner`（48⭐）、`rsrohan99/llamaindex-trip-planner`（50⭐）：结构较简单，未深读。

---

## 二、重点项目详解

### 1. 🏆 OSU-NLP-Group/TravelPlanner — 538⭐（学术基准，约束验证体系）

- **链接**：https://github.com/OSU-NLP-Group/TravelPlanner ｜ 论文：ICML'24 Spotlight（arxiv 2402.01622）｜ MIT 许可
- **核心架构**：不是应用，而是评测基准 + 参考 Agent 实现。定义"给定查询 → Agent 用搜索工具采集信息 → 产出含交通/餐饮/景点/住宿的逐日计划 → 约束合规性评估"的完整闭环。
- **三种约束类型**（可直接映射到"信息核验/预算核算"Agent 的检查清单）：
  - **Environment Constraint（环境约束）**：数据库中查得到的事实（如某餐厅是否营业、某酒店价格）；
  - **Commonsense Constraint（常识约束）**：不违反常识（如不安排深夜参观博物馆、行程时间不重叠）；
  - **Hard Constraint（硬约束）**：用户明确要求（如总预算、指定市内交通方式）。
- **关键发现（重要教训）**：论文中 GPT-4 在该基准上**最终通过率仅 0.6%**——纯 LLM 生成的行程在预算、时间、地点真实性上几乎全军覆没。微调后的 Llama3.1-8B 也只有 3.8%。**这直接证明了"LLM 生成 + 确定性核验"分离的必要性**，正是本项目设"信息核验/预算核算/路线测算"三个专门 Agent 的理论依据。
- **可借鉴点**：约束分类法；评估指标设计（约束微/宏通过率、最终通过率）；自然语言计划 → 结构化 JSON 的后处理解析链（`parsing → element_extraction → combination`）。
- **不足**：是基准不是产品，无前端、无真实 API 集成（数据为离线 JSON 库，且标注"仅限评测用，不可商用"）。

### 2. 🏆 LAMDA-NeSy/ChinaTravel — 121⭐（中文基准，"可执行约束DSL"模式）

- **链接**：https://github.com/LAMDA-NeSy/ChinaTravel ｜ 论文：ICLR'26（arxiv 2412.13682）；IJCAI 2025/2026 官方竞赛基准（TPC@IJCAI）
- **核心架构**：中国真实旅行规划基准（含动态工具环境），支持 DeepSeek/GPT-4o/GLM4-plus/Qwen3-8B 本地推理。提供两种基线 Agent：**LLMNeSy**（LLM+神经符号）和 **LLM-modulo**（LLM生成→符号验证器→多轮修正，最多10轮 refine）。
- **最有价值的创新——硬约束写成可执行 Python DSL**：
  ```python
  # 约束同时以代码 + 自然语言两条形式存在
  "hard_logic_py": [
      "total_cost=0
       for activity in allactivities(plan):
           total_cost += activity_cost(activity)
           total_cost += innercity_transport_cost(activity_transports(activity))
       result=(total_cost<=1000)",        # 总预算 1000 元
      "innercity_transport_set=set() ... result=(innercity_transport_set<={'taxi'})"  # 只能打车
  ],
  "hard_logic_nl": ["总预算为1000元", "市内交通选择taxi"]
  ```
- **工作流**：LLM 生成行程 → **符号验证器用确定性代码逐条检查硬约束**（预算、交通方式、时间冲突、地点真实性）→ 不通过则把违规信息反馈给 LLM 修正 → 循环。官方明示：LLM-modulo 管线的校验精度显著优于纯 LLM 自检（"自己检查自己"不可靠）。
- **可借鉴点（对本项目最关键的一条）**：把"信息核验/预算核算/路线测算"从"让 LLM 写一段审核意见"升级为**确定性 Python 校验函数**（预算累加、景点间距离矩阵、营业时间冲突检测），LLM 只负责针对校验失败项定向修改。仓库还收录了 TPC@IJCAI2025 DSL 赛道冠军方案，可直接学习其 prompt 与校验代码组织方式。
- **不足**：学术基准，无产品 UI；数据库需从网盘下载，无公网 API 集成。

### 3. 🏆 shouzhuoshouzhuo/FloatTrip（途见）— 55⭐（架构最贴近本项目的多Agent产品）

- **链接**：https://github.com/shouzhuoshouzhuo/FloatTrip ｜ 2026-05 创建，持续活跃 ｜ LangGraph + FastAPI + 高德POI + React Native
- **核心架构**（README 中的完整流水线）：
  ```
  旅行对话 → [LLM对话理解] → Planning Brief（结构化确认卡）
     → 用户明确确认 → 持久化 Planning Run（SSE 进度回放）
     → Intent + Query Rewrite → 天气 + 高德POI + 地理聚类
     → [Planner Agent ⇄ Reviewer Agent]（生成⇄审阅多轮对抗优化）
     → [Time Check ⇄ Planner 定向修正]（时间冲突核验）
     → 周边餐饮 + Meal Recommend → Finalize（时刻表+餐厅+距离+地图+约束说明）
  ```
- **Agent 分工方式**：
  - **Planner Agent**：生成行程草案；
  - **Reviewer Agent**：审阅草案、提出修改意见，Planner 依据意见修订（多轮"生成-审阅"对抗循环）——对应本项目"方案草拟 + 信息核验"的对抗式设计；
  - **Time Check Agent**：独立于 LLM 判断的时间冲突核验（开放时间、路程耗时）——对应"路线测算"；
  - **修改规划走"迷你图"**：用户改行程时跳过 Intent/景点搜索，从 checkpoint 恢复，只跑 Planner⇄Reviewer（≤2轮）→餐饮→Finalize，Reviewer 专门验证"Planner 是否真正响应了修改意见"。
- **数据源**：高德地图 Web 服务 API（POI/路线/距离）；天气 API；LLM 可切换 DeepSeek/豆包。
- **前端展示形式**：JSX 单页 Web（地图动线 + 拖拽换序 + 换点 + 撤销重做 + 服务端距离重算）+ Bare React Native 移动端（复用同一 FastAPI 协议），SSE 实时展示规划阶段进度。
- **可借鉴点**：
  1. **先对话澄清 → 结构化 Planning Brief → 用户确认后才开跑**：需求解析阶段与规划阶段解耦，避免误解需求烧掉整条流水线的 token；
  2. **长期旅行记忆**（从历史对话提取偏好/避雷项，用户可审批/编辑/遗忘/单次覆盖）——"同行人/风格"参数化的高阶形态；
  3. **质量可量化**：内置代码打分器 + LLM 评委 + pass@k / pass^k 指标（tests/EVAL_GUIDE.md），多Agent系统的回归测试范式；
  4. **持久化 Run + SSE 回放 + 断线恢复**：长耗时规划的工程基础设施。
- **不足**：项目较新（55⭐），生产验证有限；依赖高德 API 密钥；LLM 评测体系对个人开发者有学习成本。

### 4. 🏆 tonykipkemboi/trip_planner_agent（VacAIgent）— 143⭐（CrewAI 多Agent经典教学范例）

- **链接**：https://github.com/tonykipkemboi/trip_planner_agent ｜ CrewAI 官方示例 fork 增强 ｜ MIT
- **Agent 分工（顺序流水线，源码 trip_agents.py 核实）**：
  1. **City Selection Expert**（城市选择专家）：根据天气、季节、价格选出最佳城市；
  2. **Local Expert**（本地专家）：工具为 `search_internet` + `scrape_and_summarize_website`（Serper + Browserless），产出该城市深度洞察；
  3. **Travel Concierge**（旅行管家）：汇总前两者产出，生成含预算与打包清单的完整行程（任务定义在 trip_tasks.py）。
- **数据源**：Serper 搜索 API + Browserless 网页抓取（实时搜索而非知识库）。
- **前端展示形式**：Streamlit 单页应用（表单输入 → 流程可视化进度 → 最终行程渲染）。
- **可借鉴点**：**"选城市 → 深挖当地 → 汇总成案"的漏斗式任务分解**简单有效；Streamlit 的 `expander` 展示中间产物模式适合原型期验证多Agent流水线；支持 Ollama 本地模型切换。
- **不足**：2024-06 后基本停更；搜索类工具在中文语境效果差；无预算/时间硬约束校验（生成的行程可能超预算、时间冲突）。

### 5. 🏆 kbhujbal/Multi-Agent-AI-Travel-Advisor — 56⭐（「AI只做分析，数据来自API」原则）

- **链接**：https://github.com/kbhujbal/Multi-Agent-AI-Travel-Advisor ｜ CrewAI + FastAPI + React/Vite ｜ MIT
- **核心架构（其 README 的架构图是同类中最清晰的）**：
  ```
  用户请求 → [AI] Travel Planning Manager（解析为结构化参数）
           → [API] 4类服务 asyncio.gather 并行拉真实数据（纯HTTP，无AI）
              ├ 航班: Amadeus(主) + SerpApi(备)
              ├ 住宿: Booking.com + Airbnb（均经 RapidAPI）
              ├ 活动: Google Places + Viator + Yelp
              └ 后勤: Google Maps + OpenWeatherMap + 汇率 + 国家信息
           → [AI] Travel Knowledge Expert（ChromaDB RAG 补文化/签证/实用信息）
           → [AI] Itinerary Compiler（综合全部真实数据生成逐日计划）
  最终行程：真实价格、真实酒店、可点击预订链接
  ```
- **Agent 分工方式**：3 个 AI Agent（解析/知识/汇总）+ 4 个纯代码 API 服务。**核心原则："AI only does analysis — all travel data comes from real APIs, not hallucinated by the LLM"**，整条流水线只做 2-3 次 LLM 调用而非 15-20 次。
- **数据源**：Amadeus、SerpApi、Booking.com/Airbnb(RapidAPI)、Google Places、Viator、Yelp、Google Maps、OpenWeatherMap、汇率 API、ChromaDB 向量库。缺失 key 的服务自动优雅跳过（可降级运行）。
- **前端展示形式**：React + Vite 前端 + FastAPI REST/WebSocket（进度推送）+ CLI 模式。
- **可借鉴点**：**"结构化参数 → 并行 API 采集 → LLM 汇总"三明治结构**完美对应本项目的"需求解析/攻略采集/方案草拟"三段；每个数据服务独立文件+coordinator 模式，易替换为高德/携程等中国数据源。
- **不足**：依赖大量付费海外 API（Amadeus/Viator/RapidAPI 商用需付费）；Yelp/Google Places 中文覆盖差；无硬约束校验环节（预算靠 LLM 自觉）。

### 6. 🏆 shaheennabi/Production-Ready-TripPlanner-Multi-AI-Agents-Project — 77⭐（角色分工 + 模型选型实录）

- **链接**：https://github.com/shaheennabi/Production-Ready-TripPlanner-Multi-AI-Agents-Project ｜ Taskflow AI 框架 ｜ MIT
- **Agent 分工（源码 src/agentic/agents/ 核实）**：
  1. **Web Research Agent**：Serper 搜索 + Wiki 文章/图片，负责目的地调研；
  2. **Travel Agent**：Amadeus 航班搜索 + Weather.com 天气；
  3. **Reporter/Travel Report Agent**：汇总前两者输出，生成图文并茂的完整旅行报告。
- **数据源**：Serper、Wikipedia API、Amadeus、Weather.com。
- **可借鉴点**：README 记录了**模型选型对比全过程**（GPT-3.5-turbo 工具调用最优且便宜 / LLaMA 长token失败 / Google 推理差 / o1 太贵 / Groq 不达标）——国内场景可直接替换为 DeepSeek V3（工具调用+成本）与 Qwen 的组合论证；含异常处理、logger 等工程化细节。
- **不足**：Jupyter Notebook 为主的教学形态，非独立部署产品；2025-03 后停更；无硬约束校验。

### 7. 🏆 Haohao-end/Ctrip-Style-AI-Travel-Assistant — 54⭐（Hub-and-Spoke + 安全工具分级）

- **链接**：https://github.com/Haohao-end/Ctrip-Style-AI-Travel-Assistant ｜ LangChain + LangGraph ｜ MIT
- **核心架构**：模仿携程客服的"轮辐式"（Hub-and-Spoke）多Agent：**Primary Assistant（中枢路由）** 负责意图识别与任务分派，下设航班/酒店/租车/短途游四个**专业子Agent**，通过 `add_conditional_edges` + `dialog_stack` 管理子Agent生命周期（`CompleteOrEscalate` 模式优雅退出）。
- **关键设计**：
  - **Safe Tools（只读）与 Sensitive Tools（写入）严格分级**：查航班/查酒店是安全的，改签/退票/下单属于敏感操作；
  - **Human-in-the-Loop**：敏感操作前 `interrupt_before` 暂停工作流，等待用户确认；
  - **工具失败自动降级**：`create_tool_node_with_fallback` + 错误信息回喂 LLM 重试。
- **可借鉴点**：若本项目未来加入"预订/下单"能力，这套**工具权限分级 + HITL 确认**是标准答案；多轮对话状态管理（MemorySaver）模式成熟。
- **不足**：CLI 演示形态（无 Web UI）；数据为模拟数据库（航班/酒店是 mock 数据）；聚焦预订操作流而非行程生成。

### 8. 🏆 alexlmoney83-oss/travel-planning-agent — 46⭐（双模型协作 + 国产数据源 MCP）

- **链接**：https://github.com/alexlmoney83-oss/travel-planning-agent ｜ LangChain Agent + Streamlit + MCP + RAG ｜ MIT
- **核心架构**：**DeepSeek R1（复杂推理：多目的地分解、预算分配、路线优化）+ Qwen3（信息提取、工具调用、方案生成）双模型协作**，按场景复杂度自动切换主导模型。预分析层将查询分为 simple/complex/multi_destination 三类路由。
- **数据源（全国产，含金量高）**：MCP 协议接入 **12306 火车票（自动站点代码+时刻+票价）、高德自驾路线（距离/时间/过路费）、高德酒店（按预算档位自动筛选：>500元豪华 / 300-500元连锁 / <300元经济）、高德多日天气、八字黄历（宜忌吉日）、航班查询（>800km 自动触发）**；RAG 向量库存旅游攻略（TXT/MD/PDF/CSV）。
- **前端展示形式**：Streamlit 对话式 UI；交通方案对比（火车 vs 自驾）、酒店推荐、逐日行程、预算分配（交通/住宿/餐饮/门票）。
- **可借鉴点**：**预算→酒店档位的确定性映射规则**是"预算核算"Agent 可落地的具体逻辑；12306+高德 MCP 组合证明国产数据源完全够支撑中国旅行规划；"按距离阈值自动触发航班查询"这类业务规则值得抄。
- **不足**：Streamlit 形态重、产品化弱；单Agent+ReAct 而非真多Agent 协作（README 自述为 LangChain Agent 架构）；黄历等特色功能与通用规划耦合较紧。

### 9. 🏆 liketrek/TREK — 12,184⭐（非AI-first，但 UI/协作/MCP 顶级参考）

- **链接**：https://github.com/liketrek/TREK ｜ NestJS 11 + React 19 + Vite + Tailwind + Leaflet/Mapbox GL ｜ AGPL-3.0（商用注意）
- **定位**：自托管旅行规划产品（拖拽式行程编排、实时协作、预算分摊、打包清单、旅行日记），**AI 不是核心生成器，而是通过内置 MCP Server 对外暴露**：
  - 150+ 工具、30 资源、OAuth 2.1、27 个 OAuth scope 分 13 权限组——AI 可创建行程、规划天数、管理预算；
  - 预置 prompt 模板（trip-summary / packing-list / budget-overview）。
- **可借鉴点**：行程的**拖拽交互范式**（跨天移动、路线自动排序、导出 Google Maps）；**费用分摊（Splitwise 式）与多人协作**——本项目"同行人"维度的产品化答案；**"产品自建 + MCP 外挂 AI"的架构思路**：行程编辑器做扎实，AI 作为工具操作它，而非 AI 直接吐文本。
- **不足**：AGPL 协议（商业网站不可直接抄代码，只可借鉴模式）；无 LLM 行程自动生成流水线（AI 依赖外部客户端驱动）；体量大、学习曲线陡。

---

## 三、对本项目最有价值的可复用模式（Top 3）

### 模式 1️⃣：「LLM 生成 + 确定性代码核验」分离（对应三省六部之"信息核验/预算核算/路线测算"）

- **来源**：ChinaTravel 的可执行约束 DSL + LLM-modulo 循环；TravelPlanner 的三类约束分类；FloatTrip 的独立 Time Check Agent 与 Reviewer。
- **为什么重要**：TravelPlanner 基准证明 GPT-4 纯生成行程的硬约束通过率 <1%。LLM 自查天然不可靠（对自己的错误"视而不见"）。
- **落地建议**：三个核验 Agent 的核心逻辑**不应该是 LLM 写审核意见，而是确定性 Python 校验函数**：
  - 信息核验 = POI 存在性/营业时间/门票价格对照真实数据源（高德/马蜂窝爬取缓存）；
  - 预算核算 = 逐项累加交通+住宿+餐饮+门票，与预算上限比对（可执行代码，如 ChinaTravel 的 `total_cost<=1000`）；
  - 路线测算 = 景点间距离矩阵 + 营业时间窗冲突检测 + 单日时长上限。
  - LLM 的角色退化为：①生成方案；②**定向修复**校验器报出的违规项（每轮只修一个问题，最多 N 轮 refine）。

### 模式 2️⃣：「结构化需求 → 并行真实数据采集 → LLM 汇总」三明治流水线

- **来源**：kbhujbal（3 AI agents + 4 纯代码 API services，asyncio.gather 并行）；alexlmoney83（12306/高德/黄历 MCP 工具层）；FloatTrip（高德 POI + 地理聚类喂给 Planner）。
- **为什么重要**：消灭幻觉价格的唯一办法是不让 LLM 编数据。kbhujbal 的"AI only does analysis"原则把整条流水线 LLM 调用压到 2-3 次。
- **落地建议**：攻略采集 Agent 的产出物应是**结构化 JSON（POI 列表/价格/营业时间/车次/酒店档位）**，而不是一段攻略散文；方案草拟 Agent 的输入严格限定为"用户参数 + 采集层结构化数据 + 核验器报告"，禁止其在无数据支撑处自由发挥（缺失数据显式标注"待核实"）。

### 模式 3️⃣：「澄清确认 → 可编辑工件 → 增量修正」的交互闭环

- **来源**：FloatTrip 的 Planning Brief 确认卡 + 持久化 Run/SSE 进度 + 行程拖拽编辑 + 修改走"迷你图"（从 checkpoint 恢复只跑 Planner⇄Reviewer≤2轮）；TREK 的拖拽式行程编辑器。
- **为什么重要**：多Agent 全量流水线贵且慢（分钟级）。用户改一个景点就全量重跑是浪费；且需求解析错误会造成整条流水线无效劳动。
- **落地建议**：
  - 需求解析 Agent 产出**结构化 Planning Brief**（出发地/目的地/天数/预算/风格/同行人逐项回显），用户确认后才触发后续 Agent——对应"三省六部"里需求解析作为把关关卡；
  - 每份方案的每一步行程是**持久化数据对象**（可单独换点/调序/改时段），草拟 Agent 的产出直接渲染为可编辑 UI；
  - 方案间差异点（利弊对比）用结构化字段承载（预算对比、节奏对比、风险提示），而不是一坨散文。

---

## 四、数据源速查清单（供攻略采集 Agent 选型）

| 数据需求 | 海外方案（已有项目验证） | 国内替代方案（本项目建议） |
|---|---|---|
| POI/景点/餐厅 | Google Places、Yelp、Viator | 高德 Web 服务 API（FloatTrip/alexlmoney83 已验证）、大众点评爬取 |
| 航班 | Amadeus（付费）、SerpApi | 飞常准/携程公开接口或搜索降级 |
| 火车 | — | 12306（alexlmoney83 的 MCP 已验证：站点代码→时刻→票价） |
| 酒店 | Booking.com/Airbnb via RapidAPI | 高德酒店搜索（按预算档位筛选）、携程 |
| 天气 | OpenWeatherMap、Open-Meteo（免费无key） | 高德天气、和风天气 |
| 攻略知识 | ChromaDB RAG（自建文档） | 本地 RAG 存马蜂窝/小红书结构化攻略 |
| 路线测算 | Google Maps Directions | 高德路线规划 2.0（含过路费/时长） |

## 五、结论摘要

1. **高 star 的"AI 旅行规划产品"并不存在**：最火的是非 AI-first 的工具（TREK 12k⭐）与学术基准（TravelPlanner 538⭐）；AI 多Agent 旅行项目普遍在 40-150⭐ 区间且以教学 Demo 为主——**这是一个蓝海，且多数项目缺"硬约束核验"环节**，正是本项目"三省六部"的差异化机会。
2. **最值得精读的三个仓库**：FloatTrip（中文多Agent产品架构全景）、ChinaTravel（约束核验方法论）、kbhujbal（数据/AI分离流水线）。
3. **必须避开的坑**（各项目共性不足）：LLM 自审预算/时间（→用确定性代码）、依赖海外付费 API 数据（→用高德/12306 国产源）、行程为一次性文本不可编辑（→持久化可编辑工件）、无评测体系（→pass@k + 约束通过率回归测试）。
