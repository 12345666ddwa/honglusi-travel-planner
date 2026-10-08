# Travel Brief & Task-Order Templates (v0.1)

> Spoke contract: every department works from the same brief; all ministry task orders reference the brief ID so nobody works from a different picture.

---

## A. Frontend Form Fields (single submission)

| Field | Required | Type | Notes |
|---|---|---|---|
| Origin | ✅ | city picker / input | supports granularity like "Chengdu", "Chengdu Shuangliu Airport", "Chengdu East Railway Station" |
| Destination | ✅ | city picker / input | single destination in the internal build (round trip); the system suggests transfer cities |
| Days | ✅ | number | includes travel days, e.g. "3 days 2 nights" |
| Budget (CNY/person) | ❌ | range slider | 0–20,000; either bound may be omitted |
| Travel style | ❌ | slider | hardcore ────────── relaxed (defaults to middle) |
| Companions | ❌ | multi-select + counts | solo / couple / friends (n) / family (n) / with elderly / with kids (age) |
| Dates | ❌ | date or season | "late August", "National Day", "next Spring Festival" all accepted |
| Preferences | ❌ | tags | nature / history & culture / food / shopping / family / photo spots / off-beat |
| Notes | ❌ | free text | e.g. "want to see Sanxingdui", "no spicy food" |

**Follow-up rules (Crown Prince):** ask only in these cases (max 2 questions merged into one round):
- no date and no season → "roughly when are you going?"
- kids mentioned without age → "how old are the kids?"
- budget = 0 with hardcore style → "roughly what's the budget ceiling?"
Everything else silently gets defaults.

## B. Structured Travel Brief (Crown Prince output)

```json
{
  "brief_id": "YZ-20260814-001",
  "origin": {"city": "Chengdu", "point": "Chengdu East Station"},
  "destination": {"city": "Chongqing", "point": ""},
  "days": 3,
  "budget": {"min": 800, "max": 3000, "unit": "CNY/person"},
  "style": 0.75,
  "style_read": "leaning hardcore: tight schedule, early starts, maximum coverage",
  "companions": {
    "count": 2,
    "type": "friends",
    "elderly": false,
    "kids": null,
    "implications": "twin room economical; hardcore pacing OK; no dietary restrictions"
  },
  "date_window": {"certainty": "fuzzy", "text": "early September", "guess": "2026-09-05 ±7d"},
  "preferences": ["food", "nature"],
  "notes": "want to see Sanxingdui",
  "followup": null
}
```

## C. Ministry Task-Order Template (issued by State Affairs)

Each ministry receives: the full brief + its slice of work + output file path + source-tagging requirements.

```
=== Revenue Ministry task order ===
Brief ID: YZ-20260814-001
Task: itemized budget for "Chengdu → Chongqing, 3 days 2 nights" per the brief
Requirements:
1. Items: intercity transport (round trip + local) / lodging (2 nights) / food (3 days) / tickets / contingency (10% of total)
2. For each item: low / mid / high tiers plus your recommended tier
3. Every number must carry: source (URL or site) + query time + ✅verified/📊estimated
4. Output to: workspace/travel-planner/jobs/YZ-20260814-001/hubu-budget.md
5. If a price can't be found, write "📊 estimated range" with the basis for the estimate
```

The other five ministries follow the same shape; see `architecture.md` §2.2 for their scopes.

## D. Job Directory Convention (shared source of truth)

```
travel-planner/
├── ARCHITECTURE.md
├── jobs/
│   └── YZ-20260814-001/          # one directory per job
│       ├── yizhi.json            # travel brief (single source of truth)
│       ├── libu_hr-party.md      # Personnel: companion strategy
│       ├── hubu-budget.md        # Revenue: budget accounting
│       ├── libu-guides.md        # Rites: guide research
│       ├── bingbu-transport.md   # War: transport research
│       ├── gongbu-routes.md      # Works: route measurement
│       ├── xingbu-verify.md      # Justice: verification report
│       ├── zhongshu-plans.md     # Secretariat: 2–3 candidate plans
│       ├── menxia-veto.md        # Chancellery: veto result
│       └── plan.html             # final deliverable: the plan page
└── agents/                       # ministry SOUL.md addenda
```

## E. Plan Page (plan.html) Section Order

1. Top overview card: destination / days / budget attainment / style match / companion fit
2. Plan tabs (2–3): budget / balanced / comfort
3. Each plan:
   - Itinerary overview (one card per day: morning / afternoon / evening + route)
   - Interactive map (POI markers + daily route lines + click for details)
   - Daily timeline (time – activity – transport – duration – cost)
   - Lodging suggestions (area + tier + sources)
   - Itemized budget table + total + comparison bar vs. user budget
   - Pros & cons (✅ highlights / ⚠️ pitfalls / 👥 who it suits)
   - Source tags (every number clickable to its source)
4. Bottom: side-by-side comparison table of the plans
5. Feedback box → partial re-dispatch
