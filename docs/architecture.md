# Honglusi (鸿胪寺) — Three Departments & Six Ministries Travel Bureau
## Architecture Design · v0.1

> Draft prepared 2026-08-14, refined against three parallel research tracks.
> Original Chinese version: [`architecture.zh.md`](architecture.zh.md)

---

## 1. Project Overview

| Item | Detail |
|---|---|
| Codename | **Honglusi (鸿胪寺)** — the imperial court office historically in charge of receiving foreign envoys and managing post stations. Used here as a metaphor for "travel reception". |
| Form | Internal-test build: runs locally, used by the author |
| Scope | Domestic travel in China (single destination per trip; international routes reserved for later) |
| Input | One form: origin / destination / days / budget / travel style (hardcore ↔ relaxed slider) / companions (count, elderly, kids) / approximate dates (optional) / preference tags — everything except origin-destination-days can be left blank |
| Follow-up | At most 1–2 structured clarifying questions after submission (e.g. "roughly which season?" when dates are missing). No endless chat. |
| Output | 2–3 complete plans rendered inside a web page: interactive map + day-by-day timeline + transport chain + itemized budget + totals + pros & cons + source tags |
| Generation time | ≤ 30 minutes |

## 2. The Travel Bureau: Three Departments + Six Ministries

The system reuses the pipeline pattern and agent fleet of an earlier project (`edict`), but redefines every role for travel planning. The existing 16 OpenClaw agents all stay online — only their `SOUL.md` files are rewritten and travel-specific tools are attached. No new agents needed.

### 2.1 The Central Four

| Office | Agent | Travel-bureau role | Input → Output |
|---|---|---|---|
| Crown Prince | `taizi` | Requirement parsing | Raw form data → structured travel brief (places / days / budget / style / companion profile / preferences / date window); generates 1–2 follow-up questions when key info is missing |
| Secretariat | `zhongshu` | Plan drafting | Six-ministry research files + brief → 2–3 candidate plans (daily itinerary, transport, lodging, budget breakdown, pros & cons) |
| Chancellery | `menxia` | Review & veto | Draft plans → approve / reject with an itemized list (checks: ad-like content, staleness, itinerary contradictions, budget mismatches, missing data) |
| Dept. of State Affairs | `shangshu` | Dispatch & tracking | Brief → task orders for the six ministries + progress tracking |

### 2.2 The Six Ministries (travel specialization)

| Ministry | Agent | Responsibility | Key output |
|---|---|---|---|
| Personnel (吏部) | `libu_hr` | Companion profiling | Elderly / kids / couples / friends → pacing advice, lodging standard, transport mode, dietary constraints |
| Revenue (户部) | `hubu` | Budget accounting | Itemized costs (transport / lodging / food / tickets / contingency) + totals + price ranges + overspend risks |
| Rites (礼部) | `libu` | Guide research | Attractions / food / niche spots / clothing tips / weather / etiquette (Xiaohongshu first, with a fallback chain) |
| War (兵部) | `bingbu` | Transport research | Train schedules & fares (12306), flight references, transfer tips, mode-selection strategy |
| Works (工部) | `gongbu` | Route measurement | Point-to-point times & distances, daily routes, travel feasibility checks (Amap API) |
| Justice (刑部) | `xingbu` | Verification | Authenticity checks, ad detection, freshness checks, source tagging (✅ verified / 📊 estimated) |

### 2.3 Separation of Duties (do vs. judge)

- **Do**: the six ministries collect & measure → **Judge**: Justice independently verifies + Chancellery independently vetoes.
- If Rites says *"restaurant X ≈ ¥80/person"*, Justice must trace the source; if it can't be traced, the number is downgraded to 📊 estimated.
- Every budget number must be traceable: source URL + query time + verified/estimated tag.
- **The core of "judging" is deterministic Python validators — not an LLM writing review prose.** (Evidence: the TravelPlanner benchmark shows GPT-4-generated itineraries pass hard constraints <1% of the time; LLM self-review is inherently unreliable.)
  - Verification = POI existence / opening hours / ticket prices checked against real sources
  - Budget = itemized summation (transport + lodging + food + tickets + contingency) vs. budget cap, e.g. `total_cost <= 3000`
  - Routing = distance matrix + opening-hour conflicts + per-day duration caps
  - The LLM's role degrades to: ① generate drafts; ② repair violations reported by the validators (one fix per round, max N rounds).

## 3. Core Workflow (8-step pipeline)

```
① User submits form → Hermes validates it
② Crown Prince parses → travel brief + confirmation card echoing each interpreted field
     User confirms / edits → 1–2 follow-ups merged into the same round when needed
③ State Affairs dispatches → six ministries research in parallel
     Personnel/Revenue/Rites/War/Works run in parallel → Justice verifies afterwards
     ⚠️ Outputs must be structured JSON (POIs / prices / hours / trains / hotel tiers).
        Prose guides are banned — the only way to kill hallucinated prices is to never let the LLM invent data.
④ Justice verifies → deterministic validators + source tags → verification report
⑤ Secretariat drafts → reads only {user params + collected JSON + verification report} to assemble 2–3 plans
     No free improvisation where data is missing; gaps are explicitly marked "to be verified"
⑥ Chancellery vetoes → deterministic checks (budget sum / time conflicts / itinerary logic) → rejection list (max 2 rounds)
⑦ Hermes final pass → renders the plan page → delivery
⑧ User feedback → "mini re-run": only affected ministries are re-dispatched, resuming from the drafting/review checkpoint
```

## 4. Technical Architecture

```
┌───────────── Frontend (static HTML, local) ─────────────┐
│  Form page: input + follow-up dialog                     │
│  Plan page: plan tabs + Leaflet map + timelines          │
│            + budget tables + pros/cons + source tags     │
└──────────────────────┬───────────────────────────────────┘
                       │ HTTP
┌──────────────────────▼───────────────────────────────────┐
│  Backend: Python FastAPI (local port, e.g. 8767)         │
│  /submit → accept form → write JSON → trigger pipeline   │
│  /plan/<id> → read plan JSON → return                    │
└──────────────────────┬───────────────────────────────────┘
                       │ invokes
┌──────────────────────▼───────────────────────────────────┐
│  Orchestration: Hermes (central dispatcher)              │
│  Prince parses → State Affairs dispatches → per-ministry  │
│  agent calls → Justice verifies → Secretariat → Chancellery │
│  → render plan page                                       │
└──────────────────────┬───────────────────────────────────┘
                       │ openclaw agent --agent <ministry> --message
┌──────────────────────▼───────────────────────────────────┐
│  Execution: OpenClaw agent fleet (existing WSL setup)    │
│  Each ministry = own workspace + ministry-specific SOUL   │
└───────────────────────────────────────────────────────────┘
```

**Data sources (locked after research, 2026-08-14)**:
- Guides: Xiaohongshu (local Chrome CDP + QR-login cookie + DOM extraction; MIT implementation ideas reused from `cn-scraper-mcp`) → fallback chain L2–L5: Mafengwo → Ctrip → Dianping → search snapshots
- Maps / POIs / routes: Amap Web Service API (personal developer "basic LBS" tier, 150k calls/month shared pool ✅ verified) → fallback: public OSRM endpoints
- Trains: 12306 front-end endpoint (`kyfw.12306.cn/otn/leftTicket/query`, community-validated)
- Hotels: Amap hotel search, filtered by budget tier (>¥500 luxury / ¥300–500 chain / <¥300 budget)
- Weather: QWeather (50k calls/month free ✅ verified)
- Flights: auto-triggered beyond 800 km; Ctrip/Qunar public pages attempted, otherwise 📊 estimated range with explicit tagging
- Only external dependency: a free Amap Open Platform personal account.

## 5. Source-Tagging Mechanism (hard requirement)

Every datum that makes it into a plan carries three elements:

```
[📍source: <URL or site name>] [🕐queried: 2026-08-14] [✅verified | 📊estimated | ⚠️rumor]
```

- ✅ verified — actually retrieved from an API/page for the current trip
- 📊 estimated — a reasonable range inferred from comparable data
- ⚠️ rumor — only seen in user posts, unverifiable (normally excluded from final plans)
- Rendered as small tags in the frontend; clicking reveals the source link.

## 6. Multi-Plan Design

| Tier | Positioning | Default trigger |
|---|---|---|
| Budget | price first | always produced when a budget floor is given |
| Balanced | value | always produced |
| Comfort | experience first | produced when a budget ceiling or relaxed style is given |

Each plan contains: route map (daily routes marked), day-by-day timeline (time–place–transport–notes), lodging suggestions, itemized budget + total, pros & cons (highlights / pitfalls / who it suits). A three-plan comparison table closes the page.

## 7. Milestones (internal test)

| Milestone | Content | Acceptance |
|---|---|---|
| M0 | Architecture + six-ministry SOUL rewrites | user review passed |
| M1 | Sample run: "Chengdu → Chongqing, 3d2n, ¥3000, hardcore" — six ministries in parallel → plan out | plan page viewable, source tags complete |
| M2 | Frontend form + follow-ups + submit-to-pipeline | zero manual intervention from form to plan |
| M3 | Multi-plan comparison + map polish + partial re-dispatch | user-accepted in real use |

## 8. Research Conclusions

**✅ Completed** (three reports under `docs/research/`):
1. `research-github-projects.md` — 9 reference projects + 3 reusable patterns (blue-ocean confirmed)
2. `research-xiaohongshu.md` — the "real browser + cookie" consensus route + source-level analysis of `cn-scraper-mcp` + L2–L5 fallback chain
3. `research-maps-transport.md` — Amap 150k/month free pool ✅ verified + 12306 / flights / OSRM / QWeather decisions

**⏳ Action items**:
- [x] Architecture reviewed; codename confirmed (Honglusi)
- [ ] Register Amap Open Platform personal account (free)
- [ ] Live-test during M1: 12306 endpoint availability, Mafengwo scraping, Dianping visibility without login
- [ ] Xiaohongshu first-use QR login (secondary account)
- [x] Ministry SOUL.md files augmented with the travel-bureau section
