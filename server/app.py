# -*- coding: utf-8 -*-
"""
「鸿胪寺」旅游规划网站 —— 后端服务
=====================================

职责边界（重要）：
  本后端只负责「数据落盘 + 状态读取 + 方案页返回」，
  不直接调用 OpenClaw —— 多Agent编排由 Hermes 中枢执行。

接口一览：
  GET  /                    → 返回 static/index.html（表单页）
  POST /api/submit          → 收表单 JSON → 生成旨意编号 → 落盘 yizhi.json + status.json
  GET  /api/status/<job_id> → 返回该单状态（供前端轮询 + Hermes 编排读写）
  GET  /plan/<job_id>       → 方案已生成则返回 plan.html，否则返回「规划中」提示页

目录约定（与 BRIEF_TEMPLATE.md §D 一致）：
  workspace/travel-planner/
  ├── server/                ← 本文件所在
  │   ├── app.py
  │   ├── static/index.html  ← 前端表单页（StaticFiles 挂载）
  │   ├── requirements.txt
  │   └── run.bat            ← Windows 一键启动
  └── jobs/<旨意编号>/        ← 每单一个目录
      ├── yizhi.json          ← 《行旅旨意》brief（唯一真相源）
      ├── status.json         ← 编排进度（Hermes 中枢负责更新）
      └── plan.html           ← 最终方案页（Hermes 渲染后写入）

启动：python -m uvicorn app:app --host 127.0.0.1 --port 8767
  或直接双击 run.bat。
"""

import json
import re
import threading
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

# ---------------------------------------------------------------------------
# 路径常量
# ---------------------------------------------------------------------------
SERVER_DIR = Path(__file__).resolve().parent          # .../travel-planner/server
PROJECT_ROOT = SERVER_DIR.parent                      # .../travel-planner
STATIC_DIR = SERVER_DIR / "static"
JOBS_ROOT = PROJECT_ROOT / "jobs"

# 确保关键目录存在（幂等）
STATIC_DIR.mkdir(parents=True, exist_ok=True)
JOBS_ROOT.mkdir(parents=True, exist_ok=True)

# 旨意编号格式：YZ-20260814-001（日期 + 当日序号）
JOB_ID_RE = re.compile(r"^YZ-\d{8}-\d{3}$")
JOB_ID_LOOSE_RE = re.compile(r"^[A-Za-z0-9_-]{3,64}$")  # 防路径穿越的宽松校验

# ---------------------------------------------------------------------------
# 表单字段与默认值
# ---------------------------------------------------------------------------
# 前端字段名 → 默认值。所有字段均可空，缺失时按此表填充（「默认值填充逻辑」）。
FORM_DEFAULTS = {
    "origin": "",            # 出发地（城市或具体点，如「成都」「成都东站」）
    "destination": "",       # 目的地（内测版单目的地）
    "days": None,            # 出行天数（含往返日）
    "budget_low": None,      # 预算下限（元/人）
    "budget_high": None,     # 预算上限（元/人）
    "style": None,           # 风格滑杆 0~10（0=特种兵，10=佛系）
    "party_type": "",        # 同行类型：独自/情侣/朋友/家人…
    "party_size": None,      # 同行人数（含本人）
    "has_elderly": False,    # 是否带老人
    "has_kids": False,       # 是否带小孩
    "kids_age": None,        # 小孩年龄
    "date_desc": "",         # 大概日期（「8月下旬」「国庆」「明年春节」均可）
    "preferences": [],       # 兴趣偏好标签
    "notes": "",             # 自由备注（「想去三星堆」「不吃辣」）
}

# 六部（旅游专署）状态清单 —— status.json 初始状态
MINISTRIES = ["礼部", "兵部", "工部", "户部", "吏部", "刑部"]

# ---------------------------------------------------------------------------
# FastAPI 应用
# ---------------------------------------------------------------------------
app = FastAPI(
    title="鸿胪寺 · 后端",
    description="中国国内旅游规划网站后端：表单收单 → 落盘 JSON → 状态查询 → 方案页返回。",
    version="0.1.0",
)

# CORS：允许本机（127.0.0.1 / localhost，任意端口）+ file:// 打开的页面（origin 为 null）。
# 前端同源本可省，但加上保险 —— 本地调试时前端可能以 file:// 或别的端口打开。
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://(127\.0\.0\.1|localhost)(:\d+)?",
    allow_origins=["null"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件挂载：server/static/ → /static/
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------
# 旨意编号生成锁（防并发提交拿到同一序号）
_job_id_lock = threading.Lock()


def _next_job_id(now: datetime) -> str:
    """生成旨意编号 YZ-YYYYMMDD-NNN。

    NNN 为当日序号：扫描 jobs/ 下当日已有的编号取最大值 +1。
    用线程锁保证并发安全。
    """
    with _job_id_lock:
        prefix = f"YZ-{now.strftime('%Y%m%d')}-"
        max_seq = 0
        for d in JOBS_ROOT.iterdir():
            if d.is_dir() and d.name.startswith(prefix):
                try:
                    max_seq = max(max_seq, int(d.name[-3:]))
                except ValueError:
                    pass
        return f"{prefix}{max_seq + 1:03d}"


def _atomic_write_json(path: Path, data: dict) -> None:
    """原子写 JSON：先写临时文件再替换，避免编排层读到半截文件。

    编码 UTF-8、ensure_ascii=False（保留中文）、缩进 2 空格。
    """
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    tmp.replace(path)


def _read_json(path: Path) -> dict | None:
    """读 JSON 文件，不存在或损坏返回 None。"""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


def _valid_job_id(job_id: str) -> bool:
    """校验旨意编号格式，防止路径穿越。"""
    return bool(job_id) and bool(JOB_ID_LOOSE_RE.match(job_id)) and ".." not in job_id


def _interpret_style(style: float | None) -> str:
    """风格解读文字（0=特种兵 → 10=佛系，与前端滑杆一致）。"""
    s = 5.0 if style is None else max(0.0, min(10.0, float(style)))
    if s <= 2.5:
        return "偏特种兵：行程紧凑、早出晚归、多景点覆盖、交通以高效换乘为主"
    if s <= 4.0:
        return "偏紧凑：每天 2~3 个景点、适当早起、保留晚间自由时间"
    if s <= 6.0:
        return "均衡节奏：每天 1~2 个主景点、上午动线下午弹性、不赶路"
    if s < 7.5:
        return "偏休闲：睡到自然醒、每天 1 个主景点、深度慢游"
    return "佛系漫游：不设硬性打卡、随性停留、以放松体验为主、住宿体验优先"


def _infer_date_window(date_desc: str) -> dict:
    """日期确定度推断（精确 / 模糊 / 未知）。

    说明：这里只做粗判，给《行旅旨意》和六部一个初始参考；
    最终日期解析由太子 agent 负责。
    """
    desc = (date_desc or "").strip()
    if not desc:
        return {"确定度": "未知", "描述": "", "推测": None}

    # 1) 精确日期：2026-08-14 / 2026/8/14 / 2026年8月14日
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y年%m月%d日"):
        try:
            d = datetime.strptime(desc, fmt)
            return {"确定度": "精确", "描述": desc, "推测": d.strftime("%Y-%m-%d")}
        except ValueError:
            pass

    # 2) 月份粒度：8月 / 2026-08 / 2026年8月
    for fmt in ("%Y-%m", "%Y年%m月"):
        try:
            d = datetime.strptime(desc, fmt)
            return {"确定度": "模糊", "描述": desc, "推测": d.strftime("%Y-%m")}
        except ValueError:
            pass
    m = re.search(r"(\d{1,2})\s*月", desc)
    if m:
        month = int(m.group(1))
        if 1 <= month <= 12:
            return {"确定度": "模糊", "描述": desc, "推测": f"{month}月"}

    # 3) 季节 / 节假日关键词粗映射
    season_map = [
        ("春", "3-5月"), ("夏", "6-8月"), ("秋", "9-11月"), ("冬", "12-2月"),
        ("国庆", "10月"), ("五一", "5月"), ("端午", "5-6月"),
        ("中秋", "9-10月"), ("春节", "1-2月"), ("暑假", "7-8月"), ("寒假", "1-2月"),
    ]
    for kw, guess in season_map:
        if kw in desc:
            return {"确定度": "模糊", "描述": desc, "推测": guess}

    # 4) 其它文字描述（如「下个月」）：确定度模糊、不做推测
    return {"确定度": "模糊", "描述": desc, "推测": None}


def _compose_party(form: dict) -> dict:
    """同行人画像：类型 / 人数 / 老人 / 小孩 / 影响说明。"""
    ptype = (form.get("party_type") or "").strip()
    size = form.get("party_size") or 1
    try:
        size = max(1, int(size))
    except (TypeError, ValueError):
        size = 1

    if not ptype:
        # 默认值填充：人数>1 默认「朋友」，否则「独自」
        ptype = "朋友" if size > 1 else "独自"

    kids_age = form.get("kids_age")
    impacts = []
    if ptype == "独自":
        impacts.append("单人出行：住宿/交通以单人经济型为主，行程可随性调整")
    elif ptype == "情侣":
        impacts.append("情侣出行：可接受双人间、注重体验与拍照点")
    elif ptype == "家人":
        impacts.append("家庭出行：偏稳妥节奏，优先家庭房/亲子友好")
    else:
        impacts.append(f"{size}人同行：可拼房/拼车，节奏按团体协调")

    if form.get("has_elderly"):
        impacts.append("有老人同行：节奏放缓、减少步行、住宿尽量近景点、备休整时段")
    if form.get("has_kids"):
        age_txt = f"（{int(kids_age)}岁）" if kids_age is not None else ""
        impacts.append(f"有小孩同行{age_txt}：安排亲子友好景点、注意午休与餐饮禁忌")

    return {
        "人数": size,
        "类型": ptype,
        "老人": bool(form.get("has_elderly")),
        "小孩": int(kids_age) if form.get("has_kids") and kids_age is not None else None,
        "影响": "；".join(impacts),
    }


def _build_yizhi(job_id: str, form: dict, now: datetime) -> dict:
    """把原始表单组装成《行旅旨意》结构化 brief（BRIEF_TEMPLATE.md §B 结构）。"""
    style = form.get("style")
    try:
        style = None if style in (None, "") else max(0.0, min(10.0, float(style)))
    except (TypeError, ValueError):
        style = None

    days = form.get("days")
    try:
        days = None if days in (None, "") else max(1, int(days))
    except (TypeError, ValueError):
        days = None
    if days is None:
        days = 3  # 默认值填充：未填天数按 3 天 2 晚计

    prefs = form.get("preferences") or []
    if isinstance(prefs, str):  # 兼容前端误传字符串（逗号分隔）
        prefs = [p.strip() for p in prefs.replace("，", ",").split(",") if p.strip()]

    budget_low = form.get("budget_low")
    budget_high = form.get("budget_high")
    try:
        budget_low = None if budget_low in (None, "") else max(0, int(budget_low))
        budget_high = None if budget_high in (None, "") else max(0, int(budget_high))
    except (TypeError, ValueError):
        budget_low = budget_high = None

    brief = {
        "旨意编号": job_id,
        "created_at": now.strftime("%Y-%m-%d %H:%M:%S"),
        # ---- 原始表单存档（保留所有输入，便于回溯与重派）----
        "原始表单": form,
        # ---- 结构化解析 ----
        "出发地": {"城市": (form.get("origin") or "").strip(), "具体点": ""},
        "目的地": {"城市": (form.get("destination") or "").strip(), "具体点": ""},
        "天数": days,
        "预算": {
            "下限": budget_low if budget_low is not None else 0,
            "上限": budget_high if budget_high is not None else 0,
            "单位": "元/人",
        },
        "风格": 5.0 if style is None else style,
        "风格解读": _interpret_style(style),
        "同行人": _compose_party(form),
        "日期窗口": _infer_date_window(form.get("date_desc") or ""),
        "偏好": prefs,
        "备注": (form.get("notes") or "").strip(),
        # 追问由太子 agent 负责，本后端不生成
        "追问": None,
    }
    return brief


# ---------------------------------------------------------------------------
# 接口：表单收单
# ---------------------------------------------------------------------------
@app.post("/api/submit")
async def submit(request: Request):
    """接收表单 JSON → 生成旨意编号 → 落盘 yizhi.json + status.json。

    请求体示例：
      {"origin":"成都","destination":"重庆","days":3,
       "budget_low":800,"budget_high":3000,"style":0.75,
       "party_type":"朋友","party_size":2,"has_elderly":false,"has_kids":false,
       "kids_age":null,"date_desc":"9月上旬",
       "preferences":["美食","自然风光"],"notes":"想去三星堆"}

    成功返回：{"job_id": "YZ-20260814-001"}
    """
    try:
        body = await request.json()
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JSONResponse({"error": "请求体不是合法 UTF-8 JSON"}, status_code=400)

    if not isinstance(body, dict):
        return JSONResponse({"error": "请求体必须是 JSON 对象"}, status_code=400)

    # 字段白名单过滤 + 默认值填充
    form = {k: body.get(k, v) for k, v in FORM_DEFAULTS.items()}

    # 基础校验：出发地/目的地至少给出一个（内测版尽量宽松，只拦明显无效提交）
    if not (form["origin"] or "").strip() and not (form["destination"] or "").strip():
        return JSONResponse({"error": "出发地和目的地至少填一个"}, status_code=400)

    now = datetime.now()
    job_id = _next_job_id(now)
    job_dir = JOBS_ROOT / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    # 1) 《行旅旨意》brief
    _atomic_write_json(job_dir / "yizhi.json", _build_yizhi(job_id, form, now))

    # 2) 初始状态：待调度（后续由 Hermes 编排更新 stage / ministries / status）
    _atomic_write_json(
        job_dir / "status.json",
        {
            "job_id": job_id,
            "status": "pending",          # pending → running → done / failed
            "stage": "待调度",            # 当前阶段描述（中书草拟 / 门下封驳 …）
            "ministries": {m: "pending" for m in MINISTRIES},
            "updated_at": now.strftime("%Y-%m-%d %H:%M:%S"),
            "plan_url": f"/plan/{job_id}",
        },
    )

    return JSONResponse({"job_id": job_id})


# ---------------------------------------------------------------------------
# 接口：状态查询
# ---------------------------------------------------------------------------
@app.get("/api/status/{job_id}")
async def get_status(job_id: str):
    """返回 jobs/<job_id>/status.json 内容（前端轮询用）。

    status.json 由 Hermes 编排层负责更新；本接口只读。
    """
    if not _valid_job_id(job_id):
        return JSONResponse({"error": "旨意编号格式非法"}, status_code=400)

    status = _read_json(JOBS_ROOT / job_id / "status.json")
    if status is None:
        return JSONResponse({"error": f"未找到旨意 {job_id}"}, status_code=404)
    return JSONResponse(status)


# ---------------------------------------------------------------------------
# 接口：方案页
# ---------------------------------------------------------------------------
_PLAN_PENDING_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>鸿胪寺 · 方案规划中</title>
<style>
  body{font-family:"Microsoft YaHei","PingFang SC",sans-serif;background:#f6f1e7;margin:0;
       min-height:100vh;display:flex;align-items:center;justify-content:center;color:#3d352a}
  .card{background:#fff;border-radius:16px;box-shadow:0 8px 32px rgba(61,53,42,.12);
        padding:48px 56px;max-width:560px;text-align:center}
  h1{margin:0 0 8px;font-size:26px;color:#8c4a2f}
  .sub{color:#8a7d6a;font-size:14px;margin-bottom:28px}
  .jobid{display:inline-block;background:#f3ead9;border:1px dashed #c9b48c;
         border-radius:8px;padding:6px 16px;font-size:15px;margin-bottom:20px}
  .stage{font-size:17px;font-weight:bold;color:#5a4a34;margin:8px 0 16px}
  .mins{list-style:none;padding:0;margin:0 auto 24px;max-width:300px;text-align:left}
  .mins li{display:flex;align-items:center;gap:8px;padding:6px 10px;font-size:14px;
           border-bottom:1px dashed #eee}
  .mins i{margin-left:auto;font-style:normal;color:#8a7d6a;font-size:12px}
  .dot{width:9px;height:9px;border-radius:50%;background:#d8cdb8;flex:none}
  .dot.run{background:#e6a23c;animation:pulse 1.2s infinite}
  .dot.ok{background:#67c23a}
  @keyframes pulse{50%{opacity:.35}}
  .hint{color:#a2937c;font-size:12px;margin-top:4px}
</style>
</head>
<body>
<div class="card">
  <h1>🏮 鸿胪寺正在规划中</h1>
  <p class="sub">三省六部旅游专署已接旨，正在为您的行程忙碌</p>
  <p class="jobid">旨意编号：__JOB_ID__</p>
  <p id="stage" class="stage">当前阶段：__STAGE__</p>
  <ul id="mins" class="mins">__MIN_LIS__</ul>
  <p class="hint">本页每 4 秒自动刷新进度，方案生成后自动跳转（约 10~30 分钟）</p>
</div>
<script>
(function () {
  var jobId = "__JOB_ID__";
  function esc(s){return String(s||"").replace(/[<>&]/g,function(c){
    return {"<":"&lt;",">":"&gt;","&":"&amp;"}[c];});}
  function refresh(){
    fetch("/api/status/" + jobId)
      .then(function(r){return r.json();})
      .then(function(d){
        var el = document.getElementById("stage");
        if (el && d.stage) el.textContent = "当前阶段：" + d.stage;
        var mins = document.getElementById("mins");
        if (mins && d.ministries) {
          var lis = Object.keys(d.ministries).map(function(m){
            var st = d.ministries[m], cls = st === "done" ? "ok" : (st === "running" ? "run" : "");
            return "<li><span class=\"dot " + cls + "\"></span>" + esc(m) +
                   "<i>" + esc(st) + "</i></li>";
          }).join("");
          mins.innerHTML = lis;
        }
        // 方案已生成 → 跳转方案页
        if (d.status === "done") {
          window.location.href = "/plan/" + jobId + "?t=" + Date.now();
        }
      })
      .catch(function(){});
  }
  refresh();
  setInterval(refresh, 4000);   // 每 4 秒轮询
  setTimeout(function(){        // 兜底：30 秒整页刷新一次
    if (!document.hidden) window.location.reload();
  }, 30000);
})();
</script>
</body>
</html>
"""


@app.get("/plan/{job_id}")
async def get_plan(job_id: str):
    """返回最终方案页。

    - jobs/<job_id>/plan.html 存在 → 直接返回（HTMLResponse）
    - 不存在 → 返回「规划中」提示页（内联 HTML，自动轮询状态并跳转）
    """
    if not _valid_job_id(job_id):
        return JSONResponse({"error": "旨意编号格式非法"}, status_code=400)

    plan_file = JOBS_ROOT / job_id / "plan.html"
    if plan_file.exists():
        html = plan_file.read_text(encoding="utf-8")
        # 注入 base 标签：让 plan.html 内的相对路径（images/xxx.jpg）正确解析到本 job 目录
        if "<base" not in html:
            html = html.replace("<head>", f'<head><base href="/plan/{job_id}/">', 1)
        return HTMLResponse(html)

    if not (JOBS_ROOT / job_id / "status.json").exists():
        return HTMLResponse(
            "<html lang='zh-CN'><head><meta charset='utf-8'><title>鸿胪寺</title></head>"
            "<body style='font-family:sans-serif;padding:40px;text-align:center'>"
            "<h1>未找到旨意 " + job_id + "</h1>"
            "<p><a href='/'>返回表单页</a></p></body></html>",
            status_code=404,
        )

    # 读当前状态填充提示页
    status = _read_json(JOBS_ROOT / job_id / "status.json") or {}
    stage = status.get("stage", "待调度")
    mins = status.get("ministries", {m: "pending" for m in MINISTRIES})
    lis = "".join(f"<li>{m} · {st}</li>" for m, st in mins.items())

    html = (
        _PLAN_PENDING_HTML.replace("__JOB_ID__", job_id)
        .replace("__STAGE__", stage)
        .replace("__MIN_LIS__", lis)
    )
    return HTMLResponse(html)


@app.get("/plan/{job_id}/images/{filename}")
async def get_plan_image(job_id: str, filename: str):
    """返回方案页引用的图片（jobs/<job_id>/images/<filename>）。"""
    if not _valid_job_id(job_id):
        return JSONResponse({"error": "旨意编号格式非法"}, status_code=400)
    if not re.fullmatch(r"[\w.\-（）()]+", filename, re.UNICODE):
        return JSONResponse({"error": "文件名格式非法"}, status_code=400)
    img = (JOBS_ROOT / job_id / "images" / filename).resolve()
    # 防路径穿越：必须仍位于该 job 的 images 目录内
    if not str(img).startswith(str((JOBS_ROOT / job_id / "images").resolve())):
        return JSONResponse({"error": "非法路径"}, status_code=400)
    if not img.is_file():
        return JSONResponse({"error": "图片不存在"}, status_code=404)
    return FileResponse(img)


# ---------------------------------------------------------------------------
# 接口：首页（表单页）
# ---------------------------------------------------------------------------
@app.get("/")
async def index():
    """返回 static/index.html；若前端尚未部署则返回占位页（避免 404 崩溃）。"""
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)

    return HTMLResponse(
        """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"><title>鸿胪寺 · 旅游规划</title>
<style>
body{font-family:"Microsoft YaHei",sans-serif;background:#f6f1e7;color:#3d352a;
     display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0}
.card{background:#fff;border-radius:16px;padding:48px 56px;text-align:center;
      box-shadow:0 8px 32px rgba(61,53,42,.12)}
h1{color:#8c4a2f}
code{background:#f3ead9;padding:2px 8px;border-radius:4px}
</style>
</head>
<body>
<div class="card">
<h1>🏮 鸿胪寺 · 后端已就绪</h1>
<p>后端服务运行正常。前端表单页尚未部署到 <code>server/static/index.html</code>。</p>
<p>API：<code>POST /api/submit</code> ｜ <code>GET /api/status/{job_id}</code> ｜ <code>GET /plan/{job_id}</code></p>
</div>
</body>
</html>"""
    )


if __name__ == "__main__":
    # 直接运行 python app.py 时启动（等价于 run.bat）
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8767)
