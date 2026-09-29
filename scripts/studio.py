#!/usr/bin/env python3
"""头像工作台：在浏览器里选自己的照片 → 挑编号 → 看辅助线 → 一键交给本机开源服务出图。

    python scripts/studio.py --dir ./相册 --port 8765

只监听 127.0.0.1。页面不上传任何地方：照片读自你指定的目录，出图请求由本机
gen_portrait.py 转给你本机的开源服务（ComfyUI / SD WebUI）。所有产物落在 out/ 下。
"""

import json
import os
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import lib
import gen_portrait

ROOT = lib.ROOT
STATE = {"dir": os.getcwd(), "out": os.path.join(ROOT, "out"), "page": None}

PAGE = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>spec-face · 头像工作台</title>
<style>
:root{--bg:#15171a;--panel:#1e2126;--line:#2c3037;--fg:#e8eaed;--dim:#9aa0a6;--ok:#3ddc97;--bad:#ff6b6b;--warn:#ffc857;--acc:#6ea8fe}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.6 -apple-system,"Segoe UI","Microsoft YaHei",sans-serif}
header{padding:16px 22px;border-bottom:1px solid var(--line);display:flex;gap:14px;align-items:baseline;flex-wrap:wrap}
h1{font-size:17px;margin:0}
header span{color:var(--dim);font-size:12px}
main{display:grid;grid-template-columns:230px 1fr 1fr;gap:16px;padding:16px 22px;align-items:start}
@media(max-width:1080px){main{grid-template-columns:1fr}}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px}
.card h2{font-size:13px;margin:0 0 10px;color:var(--dim);letter-spacing:.06em;text-transform:uppercase}
#photos{max-height:62vh;overflow:auto;display:grid;grid-template-columns:repeat(2,1fr);gap:6px}
.thumb{border:2px solid transparent;border-radius:6px;cursor:pointer;overflow:hidden;background:#0e1013;aspect-ratio:1/1.2}
.thumb.on{border-color:var(--acc)}
.thumb img{width:100%;height:100%;object-fit:cover;display:block}
label{display:block;font-size:12px;color:var(--dim);margin:10px 0 3px}
select,input[type=text],input[type=number]{width:100%;background:#12141a;color:var(--fg);border:1px solid var(--line);border-radius:6px;padding:7px 8px;font:inherit}
button{background:var(--acc);color:#0b0d10;border:0;border-radius:7px;padding:9px 16px;font-weight:600;font-size:14px;cursor:pointer;margin-top:14px}
button:disabled{opacity:.45;cursor:default}
.row{display:grid;grid-template-columns:1fr 1fr;gap:10px}
canvas{max-width:100%;border-radius:8px;display:block;background:#0e1013}
pre{white-space:pre-wrap;word-break:break-word;background:#12141a;border:1px solid var(--line);border-radius:8px;padding:10px;font-size:12px;max-height:34vh;overflow:auto}
.chk{display:flex;gap:8px;align-items:flex-start;margin-top:12px;font-size:12.5px;color:var(--fg)}
.chk input{margin-top:3px}
.res{border-top:1px solid var(--line);margin-top:12px;padding-top:12px}
.res img{width:100%;border-radius:8px;margin-bottom:6px}
table{width:100%;border-collapse:collapse;font-size:12px}
td{padding:3px 6px;border-bottom:1px solid var(--line);vertical-align:top}
td.m{width:34px;font-weight:700}
.ok{color:var(--ok)}.bad{color:var(--bad)}.skip{color:var(--dim)}
code{background:#12141a;padding:1px 5px;border-radius:4px;font-size:12px}
.hint{font-size:12px;color:var(--dim);margin-top:8px}
details{margin-top:12px;border:1px solid var(--line);border-radius:8px;padding:8px 10px}
summary{cursor:pointer;font-size:12.5px;color:var(--dim)}
</style></head><body>
<header><h1>spec-face · 头像工作台</h1><span id="where"></span>
<span>照片只从本机目录读取，出图只发往本机开源服务；产物落在 <code>out/</code>。</span></header>
<main>
<section class="card"><h2>1 · 选一张本人照片</h2>
  <div id="photos"></div>
  <div class="hint" id="photocount"></div>
</section>

<section class="card"><h2>2 · 编号与构图预览</h2>
  <div class="row"><div><label>合规规格 S（先定这个）</label><select id="spec"></select></div>
  <div><label>岗位气质 P</label><select id="persona"></select></div></div>
  <div class="row"><div><label>着装 W</label><select id="wear"></select></div>
  <div><label>背景光型 B</label><select id="backdrop"></select></div></div>
  <div class="row"><div><label>神态 E</label><select id="mood"></select></div>
  <div><label>候选张数 n</label><input type="number" id="n" value="3" min="1" max="6"></div></div>
  <label>客观外貌描述（性别年龄段 / 脸型 / 发型 / 肤色）</label>
  <input type="text" id="subject" placeholder="28岁女性，圆脸，齐肩发，自然肤色">
  <div id="preview"><canvas id="cv"></canvas></div>
  <div class="hint">辅助线是按规格比例画的容差带，不是人脸检测结果。要客观判定请用 <code>check_spec.py</code>。</div>
</section>

<section class="card"><h2>3 · 生成与校验</h2>
  <label>生成后端 G（全部为本机开源服务）</label><select id="provider"></select>
  <label>端点</label><input type="text" id="endpoint" placeholder="留空用后端默认（127.0.0.1）">
  <details><summary>高级：工作流 / 扩展参数 / 种子</summary>
    <label>ComfyUI 工作流 JSON（自己导出的 API 格式）</label>
    <input type="text" id="workflow" placeholder="out/my-pulid-workflow.json">
    <label>WebUI 扩展参数 JSON</label><input type="text" id="extra" placeholder="out/extra.json">
    <div class="row"><div><label>种子（批量请锁）</label><input type="number" id="seed" value=""></div>
    <div><label>步数</label><input type="number" id="steps" value="30"></div></div>
  </details>
  <div class="chk"><input type="checkbox" id="auth"><span>我确认这张照片是<b>本人</b>，或我已获得<b>书面授权</b>。
  我理解生成结果只用于工牌/头像等展示，<b>不得</b>用于通过人脸识别、活体检测、实名认证。</span></div>
  <button id="go">生成本人头像</button>
  <pre id="log" hidden></pre>
  <div id="results"></div>
</section>
</main>
<script>
let LIB={}, PH=[], CUR=null;
const $=id=>document.getElementById(id);
const opt=(s,v,t)=>{const o=document.createElement('option');o.value=v;o.textContent=t;s.appendChild(o)};

async function boot(){
  LIB=await (await fetch('/api/library')).json();
  $('where').textContent='照片目录 '+LIB.dir;
  for(const [k,sel] of [['specs','spec'],['personas','persona'],['wear','wear'],['backdrops','backdrop'],['moods','mood']]){
    for(const it of LIB[k]) opt($(sel), it.id, it.id+' '+it.name_zh);
  }
  for(const p of LIB.providers) opt($('provider'), p.id, p.id+' '+p.name_zh+'（'+p.status+'）');
  ['spec','persona','wear','backdrop','mood','provider'].forEach(s=>$(s).onchange=()=>{draw();});
  $('spec').value='S-09'; $('persona').value='P-001'; draw();
  PH=await (await fetch('/api/photos')).json();
  $('photocount').textContent=PH.length+' 张候选 · 点选一张';
  const box=$('photos');
  PH.forEach((p,i)=>{
    const d=document.createElement('div'); d.className='thumb';
    d.innerHTML='<img loading="lazy" src="/media?path='+encodeURIComponent(p.path)+'">';
    d.title=p.path+'  '+p.w+'×'+p.h;
    d.onclick=()=>{document.querySelectorAll('.thumb').forEach(t=>t.classList.remove('on'));
      d.classList.add('on'); CUR=p; draw();};
    box.appendChild(d);
  });
}

function specOf(){return LIB.specs.find(s=>s.id==$('spec').value)}

function draw(){
  const cv=$('cv'), ctx=cv.getContext('2d');
  if(!CUR){cv.width=320;cv.height=400;ctx.fillStyle='#0e1013';ctx.fillRect(0,0,320,400);
    ctx.fillStyle='#9aa0a6';ctx.fillText('← 先选一张照片',110,200);return}
  const im=new Image();
  im.onload=()=>{
    // 与 gen_portrait.prep_source 同口径：居中裁到规格比例，再等比缩到预览宽
    const want=parseFloat(im.width)/parseFloat(im.height);
    const sp=specOf(), num=+sp.aspect.split(':')[0], den=+sp.aspect.split(':')[1], target=num/den;
    let cw,ch; if(want>target){ch=im.height;cw=ch*target}else{cw=im.width;ch=cw/target}
    const x0=(im.width-cw)/2, y0=(im.height-ch)/2;
    const scale=Math.min(340/cw, 460/ch);
    cv.width=Math.round(cw*scale); cv.height=Math.round(ch*scale);
    ctx.drawImage(im,x0,y0,cw,ch,0,0,cv.width,cv.height);
    const W=cv.width,H=cv.height, [lo,hi]=sp.eye_line_ratio;
    const top=H*(1-hi), bot=H*(1-lo);
    ctx.fillStyle='rgba(255,90,90,.22)'; ctx.fillRect(0,top,W,bot-top);
    ctx.strokeStyle='#ff5a5a'; ctx.lineWidth=1.5;
    ctx.strokeRect(0,top,W,bot-top);
    const hh=sp.head_height_ratio[1], mid=(top+bot)/2;
    ctx.strokeRect(W/2-hh*H*.38, mid-hh*H/2, hh*H*.76, hh*H);
    ctx.fillStyle='#ff8a8a'; ctx.font='12px system-ui';
    ctx.fillText('瞳孔线带 '+Math.round(lo*100)+'–'+Math.round(hi*100)+'%（距底边）', 6, bot+15);
    if((sp.checks||[]).includes('safe_circle')){
      const d=Math.min(W,H)*0.70;
      ctx.strokeStyle='#6ea8fe'; ctx.lineWidth=2; ctx.beginPath();
      ctx.arc(W/2,H/2,d/2,0,Math.PI*2); ctx.stroke();
      ctx.fillStyle='#6ea8fe'; ctx.fillText('70% 圆形安全区', W/2-d/2, H/2+d/2+16);
    }
  };
  im.src='/media?path='+encodeURIComponent(CUR.path);
}

async function generate(){
  $('go').disabled=true; $('log').hidden=false; $('log').textContent='请求中…（本机出图可能要几十秒到几分钟）';
  const body={photo:CUR&&CUR.path, spec:$('spec').value, persona:$('persona').value,
    wear:$('wear').value, backdrop:$('backdrop').value, mood:$('mood').value,
    subject:$('subject').value, provider:$('provider').value, n:+$('n').value,
    endpoint:$('endpoint').value, workflow:$('workflow').value, extra:$('extra').value,
    seed:$('seed').value, steps:$('steps').value, authorized:$('auth').checked?'本人':''};
  const r=await fetch('/api/generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  const d=await r.json();
  $('log').textContent=d.log;
  const box=$('results'); box.innerHTML='';
  (d.outputs||[]).forEach(o=>{
    const w=document.createElement('div'); w.className='res';
    let rows='';
    (o.checks||[]).forEach(c=>{
      const cls=c.result===true?'ok':(c.result===false?'bad':'skip');
      const mark=c.result===true?'✓':(c.result===false?'✗':'-');
      rows+='<tr><td class="m '+cls+'">'+mark+'</td><td>'+c.check+'</td><td>'+c.detail+'</td></tr>';
    });
    w.innerHTML='<img src="/media?path='+encodeURIComponent(o.path)+'&t='+Date.now()+'">'+
      '<div class="hint">'+o.path+'</div><table>'+rows+'</table>';
    box.appendChild(w);
  });
  $('go').disabled=false;
  if(CUR) draw();
}

$('go').onclick=()=>{ if(!CUR){alert('先选一张照片');return} if(!$('subject').value.trim())
  {alert('请填客观外貌描述');return} if(!$('auth').checked)
  {alert('请先确认照片归属与用途授权');return} generate(); };
boot();
</script></body></html>
"""


def library():
    return {
        "dir": STATE["dir"],
        "specs": lib.load("specs"),
        "personas": lib.load("personas"),
        "wear": lib.load("wear"),
        "backdrops": lib.load("backdrops"),
        "moods": lib.load("moods"),
        "providers": lib.load("providers"),
    }


def photos():
    out = []
    for path in gen_portrait.photo_candidates(STATE["dir"]):
        w = h = 0
        if gen_portrait.HAS_PIL:
            try:
                from PIL import Image
                with Image.open(path) as img:
                    w, h = img.size
            except Exception:
                pass
        out.append({"path": os.path.abspath(path), "w": w, "h": h})
    return out


def allowed(path):
    """只允许读照片目录、out/、images/ 下的文件——挡掉 /media?path=../../Windows/win.ini。"""
    real = os.path.realpath(path)
    roots = [os.path.realpath(r) for r in (STATE["dir"], STATE["out"], os.path.join(ROOT, "images"))]
    return any(real == r or real.startswith(r + os.sep) for r in roots)


def run_generate(body):
    if not body.get("authorized"):
        return {"log": "拒跑：未确认照片归属与用途授权。", "outputs": []}
    if not body.get("photo") or not allowed(body["photo"]):
        return {"log": "拒跑：照片路径不在允许的目录内。", "outputs": []}
    args = ["--photo", body["photo"], "--spec", body["spec"], "--persona", body["persona"],
            "--subject", body.get("subject") or "本人", "--provider", body["provider"],
            "--confirm-authorized", body["authorized"], "--n", str(body.get("n") or 3)]
    for key, flag in (("wear", "--wear"), ("backdrop", "--backdrop"), ("mood", "--mood"),
                      ("endpoint", "--endpoint"), ("workflow", "--workflow"),
                      ("extra", "--payload-extra"), ("steps", "--steps")):
        if body.get(key):
            args += [flag, str(body[key])]
    if str(body.get("seed") or "").strip():
        args += ["--seed", str(body["seed"])]
    import contextlib
    import io
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            gen_portrait.main(args)
    except SystemExit as exc:
        buf.write(str(exc.code or ""))
    except Exception as exc:
        buf.write(f"\n{type(exc).__name__}: {exc}")
    log = buf.getvalue()
    outputs = []
    marker = "产物："
    for line in log.splitlines():
        if marker in line:
            outdir = line.split(marker, 1)[1].split("（")[0].strip()
            manifest = os.path.join(outdir, "render_manifest.json")
            if os.path.exists(manifest):
                with open(manifest, encoding="utf-8") as handle:
                    data = json.load(handle)
                for path in data.get("outputs", []):
                    outputs.append({"path": path, "checks": data.get("spec_check", {}).get(path, [])})
            break
    return {"log": log, "outputs": [o for o in outputs if allowed(o["path"])]}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _send(self, body, ctype="application/json; charset=utf-8", code=200):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed.query)
        if parsed.path == "/":
            return self._send(PAGE.encode("utf-8"), "text/html; charset=utf-8")
        if parsed.path == "/api/library":
            return self._send(json.dumps(library(), ensure_ascii=False).encode("utf-8"))
        if parsed.path == "/api/photos":
            return self._send(json.dumps(photos(), ensure_ascii=False).encode("utf-8"))
        if parsed.path == "/media":
            path = (qs.get("path") or [""])[0]
            if not path or not allowed(path) or not os.path.isfile(path):
                return self._send(b'{"error":"forbidden"}', code=403)
            ctype = "image/png" if path.lower().endswith(".png") else "image/jpeg"
            with open(path, "rb") as handle:
                return self._send(handle.read(), ctype)
        return self._send(b'{"error":"not found"}', code=404)

    def do_POST(self):
        if urllib.parse.urlparse(self.path).path != "/api/generate":
            return self._send(b'{"error":"not found"}', code=404)
        length = int(self.headers.get("Content-Length") or 0)
        if length > 1_000_000:
            return self._send(b'{"error":"too large"}', code=413)
        try:
            body = json.loads(self.rfile.read(length).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return self._send(b'{"error":"bad json"}', code=400)
        result = run_generate(body)
        # 出图可能几十秒到几分钟，前端会一直等；这里同步返回，避免半后台状态
        self._send(json.dumps(result, ensure_ascii=False).encode("utf-8"))


def main(argv=None):
    lib.force_utf8()
    import argparse
    ap = argparse.ArgumentParser(description="spec-face 头像工作台（仅监听 127.0.0.1）")
    ap.add_argument("--dir", default=os.getcwd(), help="照片目录，默认当前目录")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--no-browser", dest="browser", action="store_false", default=True)
    args = ap.parse_args(argv if argv is not None else sys.argv[1:])
    if not os.path.isdir(args.dir):
        raise SystemExit(f"照片目录不存在：{args.dir}")
    STATE["dir"] = os.path.abspath(args.dir)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    url = f"http://127.0.0.1:{args.port}/"
    print(f"头像工作台已启动：{url}")
    print(f"  照片目录 {STATE['dir']}   产物目录 {STATE['out']}（已 gitignore）")
    print("  只监听回环地址；关闭这个终端窗口即停。Ctrl+C 退出。")
    if args.browser:
        try:
            import webbrowser
            webbrowser.open(url)
        except Exception:
            pass
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已退出。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
