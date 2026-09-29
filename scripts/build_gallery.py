#!/usr/bin/env python3
"""从 references/*.json 构建离线画廊单页（零依赖、可直接双击打开、可全文检索）。

    python scripts/build_gallery.py
输出：skills/portrait-prompter/gallery/index.html
"""

import argparse
import html
import json
import os

import lib

OUT = os.path.join(lib.ROOT, "skills", "portrait-prompter", "gallery", "index.html")

esc = html.escape


def swatch(rgb):
    if not rgb:
        return ""
    return f'<span class="sw" style="background:rgb({", ".join(map(str, rgb))})"></span>'

PAGE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>spec-face 编号画廊 · 工牌头像提示词与合规规格</title>
<style>
:root{--fg:#1a1d21;--mut:#6b7280;--line:#e5e7eb;--bg:#fff;--ac:#2563eb;--warn:#b45309}
*{box-sizing:border-box}
body{margin:0;font:15px/1.6 -apple-system,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;color:var(--fg);background:#f7f8fa}
header{background:var(--bg);border-bottom:1px solid var(--line);padding:22px 20px 14px}
h1{margin:0 0 4px;font-size:20px}
.sub{color:var(--mut);font-size:13px}
.bar{display:flex;gap:10px;flex-wrap:wrap;margin-top:14px;align-items:center}
input#q{flex:1;min-width:220px;padding:9px 12px;border:1px solid var(--line);border-radius:8px;font-size:14px}
nav{display:flex;gap:6px;flex-wrap:wrap}
nav button{padding:8px 13px;border:1px solid var(--line);background:var(--bg);border-radius:8px;cursor:pointer;font-size:13px}
nav button.on{background:var(--ac);color:#fff;border-color:var(--ac)}
main{max-width:1180px;margin:0 auto;padding:18px 20px 60px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:14px}
.card{background:var(--bg);border:1px solid var(--line);border-radius:12px;padding:15px 16px}
.id{font-weight:700;color:var(--ac);font-size:13px;letter-spacing:.4px}
.t{font-weight:700;margin:2px 0 1px}
.en{color:var(--mut);font-size:12px}
.tag{display:inline-block;background:#eef2ff;color:#3730a3;border-radius:5px;padding:1px 7px;font-size:11px;margin:6px 4px 0 0}
.row{font-size:13px;color:#374151;margin-top:7px}
.row b{color:var(--fg);font-weight:600}
.sw{display:inline-block;width:14px;height:14px;border-radius:3px;border:1px solid var(--line);vertical-align:-2px;margin-right:5px}
pre{white-space:pre-wrap;word-break:break-word;background:#f8fafc;border:1px solid var(--line);border-radius:8px;padding:9px 10px;font-size:12px;line-height:1.5;margin:9px 0 0;max-height:170px;overflow:auto}
.copy{margin-top:8px;padding:6px 11px;border:1px solid var(--ac);color:var(--ac);background:var(--bg);border-radius:7px;cursor:pointer;font-size:12px}
.copy:hover{background:var(--ac);color:#fff}
table{width:100%;border-collapse:collapse;background:var(--bg);font-size:13px}
th,td{border-bottom:1px solid var(--line);padding:8px 10px;text-align:left}
th{background:#f1f5f9;font-weight:600}
.warn{color:var(--warn);font-size:12px}
.mut{color:var(--mut);font-size:12px}
footer{max-width:1180px;margin:0 auto;padding:0 20px 40px;color:var(--mut);font-size:12px}
#n{color:var(--mut);font-size:12px;margin-left:6px}
</style>
</head>
<body>
<header>
  <h1>spec-face 编号画廊</h1>
  <div class="sub">选个编号，出张能直接印进工卡的职业照 · 岗位 __NP__ / 着装 __NW__ / 背景光型 __NB__ / 神态 __NE__ / 合规规格 __NS__</div>
  <div class="bar">
    <input id="q" placeholder="搜索编号、岗位、行业、关键词…（如 P-001 / 金融 / 白底）">
    <nav>
      <button data-t="p" class="on">岗位</button><button data-t="w">着装</button>
      <button data-t="b">背景光型</button><button data-t="e">神态</button><button data-t="s">合规规格</button>
    </nav><span id="n"></span>
  </div>
</header>
<main><div class="grid" id="g"></div></main>
<footer>
  离线单页，由 <code>scripts/build_gallery.py</code> 从 <code>references/*.json</code> 生成，改数据后重新构建。<br>
  提示词中的 <code>__OBJ__</code> 请替换为拍摄对象描述；成图后用 <code>scripts/check_spec.py</code> 做规格自检。
</footer>
<script>
const D=__DATA__;
let tab='p';
const esc=s=>String(s).replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
function swatch(rgb){return rgb?`<span class="sw" style="background:rgb(${rgb.join(',')})"></span>`:''}
function card(o){return `<div class="card" data-s="${esc(o.search)}">${o.html}</div>`}
function render(){
  const q=document.getElementById('q').value.trim().toLowerCase();
  const items=D[tab].filter(o=>!q||o.search.toLowerCase().includes(q));
  document.getElementById('g').innerHTML=items.map(o=>card(o)).join('')||'<div class="mut" style="padding:20px">无匹配结果</div>';
  document.getElementById('n').textContent=`${items.length} 项`;
}
document.getElementById('q').addEventListener('input',render);
document.querySelectorAll('nav button').forEach(b=>b.onclick=()=>{
  document.querySelectorAll('nav button').forEach(x=>x.classList.remove('on'));
  b.classList.add('on');tab=b.dataset.t;render();
});
document.addEventListener('click',e=>{
  if(!e.target.classList.contains('copy'))return;
  const t=e.target.closest('.card').querySelector('pre').textContent;
  navigator.clipboard.writeText(t).then(()=>{e.target.textContent='已复制 ✓';
    setTimeout(()=>e.target.textContent='复制双语提示词',1300);});
});
render();
</script>
</body>
</html>
"""


def persona_cards():
    out = []
    for p in lib.load("personas"):
        wear = lib.pick("wear", p["wears"][0])
        bd = lib.pick("backdrops", p["backdrops"][0])
        mood = lib.pick("moods", p["moods"][0])

        a = argparse.Namespace(persona=p["id"], wear=wear["id"], backdrop=bd["id"],
                               mood=mood["id"], spec="S-09")
        zh, en, *_ = lib.build_prompt(a, "{{对象描述：性别年龄段、脸型、发型、肤色}}")
        prompt = "【中文】\n" + "".join(zh) + "\n\n【English】\n" + " ".join(en)
        combo = f"S-09 × {p['id']} × {wear['id']} × {bd['id']} × {mood['id']}"
        rows = (
            f'<div class="row"><b>气质</b> {esc(p["impression_zh"])} · {esc(p["impression_en"])}</div>'
            f'<div class="row"><b>眼神</b> {esc(p["gaze"])}</div>'
            f'<div class="row"><b>姿态</b> {esc(p["posture"])}</div>'
            f'<div class="row"><b>推荐</b> {esc(combo)}（默认工卡规格）</div>'
            f'<div class="row warn">⚠ {esc(p["pitfalls"])}</div>'
            f'<pre>{esc(prompt)}</pre>'
            f'<button class="copy">复制双语提示词</button>'
        )
        search = " ".join([p["id"], p["name_zh"], p["name_en"], p["industry"],
                           " ".join(p["keywords_zh"]), " ".join(p["keywords_en"]), combo])
        tags = "".join(f'<span class="tag">{esc(k)}</span>' for k in p["keywords_zh"][:5])
        out.append({
            "search": search,
            "html": (f'<div class="id">{esc(p["id"])} · {esc(p["industry"])}</div>'
                     f'<div class="t">{esc(p["name_zh"])} <span class="en">{esc(p["name_en"])}</span></div>'
                     f'{tags}{rows}'),
        })
    return out


def wear_cards():
    out = []
    for w in lib.load("wear"):
        rows = (f'<div class="row">{esc(w["desc_zh"])}</div>'
                f'<div class="row en">{esc(w["desc_en"])}</div>'
                f'<div class="row"><b>适配行业</b> {esc("、".join(w["suitable_for"]))}</div>'
                f'<pre>【中文】{esc(w["prompt_zh"])}\n\n【English】{esc(w["prompt_en"])}</pre>'
                f'<button class="copy">复制双语提示词</button>')
        out.append({"search": " ".join([w["id"], w["name_zh"], w["name_en"], w["desc_zh"],
                                        " ".join(w["suitable_for"])]),
                    "html": f'<div class="id">{esc(w["id"])}</div><div class="t">{esc(w["name_zh"])}'
                            f' <span class="en">{esc(w["name_en"])}</span></div>{rows}'})
    return out


def backdrop_cards():
    out = []
    for b in lib.load("backdrops"):
        rgb = b.get("bg_rgb")
        sw = swatch(rgb) + (f'<b>目标色</b> rgb({", ".join(map(str, rgb))}) ±{b.get("bg_tolerance")} ' if rgb else '<span class="mut">不锁定底色（需按对象或品牌定）</span>')
        warn = f'<div class="row warn">⚠ {esc(b["batch_risk"])}</div>' if b.get("batch_risk") else ""
        need = f'<div class="row warn">需输入：{esc(b["requires_input"])}</div>' if b.get("requires_input") else ""
        rows = (f'<div class="row">{sw}</div>'
                f'<div class="row"><b>光型</b> {esc(b["light_zh"])}</div>'
                f'<div class="row en">{esc(b["light_en"])}</div>'
                f'<div class="row"><b>适用</b> {esc(b["use_for"])}</div>{warn}{need}'
                f'<pre>【中文】{esc(b["prompt_zh"])}\n\n【English】{esc(b["prompt_en"])}</pre>'
                f'<button class="copy">复制双语提示词</button>')
        out.append({"search": " ".join([b["id"], b["name_zh"], b["name_en"], b["light_zh"], b["use_for"]]),
                    "html": f'<div class="id">{esc(b["id"])}</div><div class="t">{esc(b["name_zh"])}'
                            f' <span class="en">{esc(b["name_en"])}</span></div>{rows}'})
    return out


def mood_cards():
    out = []
    for m in lib.load("moods"):
        note = f'<div class="row warn">{esc(m["compliance_note"])}</div>' if m.get("compliance_note") else ""
        rows = (f'<div class="row">{esc(m["desc_zh"])}</div><div class="row en">{esc(m["desc_en"])}</div>'
                f'<div class="row"><b>微笑幅度</b> {m["smile_intensity"]:.2f} / 1.00</div>{note}'
                f'<pre>【中文】{esc(m["prompt_zh"])}\n\n【English】{esc(m["prompt_en"])}</pre>'
                f'<button class="copy">复制双语提示词</button>')
        out.append({"search": " ".join([m["id"], m["name_zh"], m["name_en"], m["desc_zh"]]),
                    "html": f'<div class="id">{esc(m["id"])}</div><div class="t">{esc(m["name_zh"])}'
                            f' <span class="en">{esc(m["name_en"])}</span></div>{rows}'})
    return out


def spec_cards():
    out = []
    for s in lib.load("specs"):
        rgb = s.get("bg_rgb")
        sw = swatch(rgb) + f'rgb({", ".join(map(str, rgb))}) ±{s.get("bg_tolerance")}' if rgb else esc(s["bg_name"])
        head = f'{lib.pct(s["head_height_ratio"][0])}–{lib.pct(s["head_height_ratio"][1])}'
        eye = f'底部起 {lib.pct(s["eye_line_ratio"][0])}–{lib.pct(s["eye_line_ratio"][1])}'
        size = f'{s["px"][0]}×{s["px"][1]}px / {s["dpi"]}dpi' + (f' · {s["size_mm"][0]}×{s["size_mm"][1]}mm'
                                                                 if s.get("size_mm") else '')
        warn = '<div class="row warn">⚠ needs_verification：提交前复核官方最新公告</div>' \
            if s["status"] == "needs_verification" else ''
        rows = (f'<div class="row"><b>尺寸</b> {esc(size)} · 比例 1:{esc(s["aspect"])}（{esc(s.get("px_rule", ""))}）</div>'
                f'<div class="row"><b>底色</b> {sw} <span class="en">{esc(s["bg_name"])}</span></div>'
                f'<div class="row"><b>头部占比</b> {esc(head)} · <b>瞳孔线</b> {esc(eye)}</div>'
                f'<div class="row"><b>表情</b> {esc(s["expression"])}</div>'
                f'<div class="row"><b>文件</b> ≤{s["max_kb"]}KB · {esc("/".join(s["formats"]))}</div>'
                f'<div class="row"><b>校验项</b> {esc(", ".join(s["checks"]))}</div>'
                f'<div class="row"><b>用途</b> {esc(s["use_for"])}</div>{warn}'
                f'<div class="row mut">{esc(s.get("notes_zh", ""))}</div>')
        out.append({"search": " ".join([s["id"], s["name_zh"], s["name_en"], s["bg_name"], s["use_for"],
                                        ", ".join(s["checks"])]),
                    "html": f'<div class="id">{esc(s["id"])}</div><div class="t">{esc(s["name_zh"])}'
                            f' <span class="en">{esc(s["name_en"])}</span></div>{rows}'})
    return out


def main():
    lib.force_utf8()
    counts = {k: len(lib.load(k)) for k in ("personas", "wear", "backdrops", "moods", "specs")}
    data = {"p": persona_cards(), "w": wear_cards(), "b": backdrop_cards(),
            "e": mood_cards(), "s": spec_cards()}
    out = (PAGE
           .replace("__DATA__", json.dumps(data, ensure_ascii=False))
           .replace("__OBJ__", "{{对象描述}}")
           .replace("__NP__", str(counts["personas"]))
           .replace("__NW__", str(counts["wear"]))
           .replace("__NB__", str(counts["backdrops"]))
           .replace("__NE__", str(counts["moods"]))
           .replace("__NS__", str(counts["specs"])))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as handle:
        handle.write(out)
    total = sum(len(v) for v in data.values())
    print(f"已生成 {os.path.relpath(OUT, lib.ROOT)}  （{total} 张卡片，{len(out) // 1024}KB）")


if __name__ == "__main__":
    main()
