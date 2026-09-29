#!/usr/bin/env python3
"""选一张本人照片 → 按编号出词 → 交给我本机跑的开源服务出图 → 拉回规格做校验。

    python scripts/gen_portrait.py --list-providers
    python scripts/gen_portrait.py --scan ./相册
    python scripts/gen_portrait.py --photo me.jpg --spec S-09 --persona P-001 \
        --subject "30岁男性，方脸，短寸发" --provider G-01 \
        --confirm-authorized 本人 --n 3
    同一条命令加 --dry-run：只写请求体，一个字节都不发出去

默认只连 127.0.0.1，照片不出本机；身份注入是硬门——没有身份节点的工作流一律拒跑。
本仓库不训练模型、不托管模型、不代跑 torch。
"""

import argparse
import base64
import glob
import json
import os
import random
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

import lib
import prompt_spec
from lib import build_prompt, pick

try:
    from PIL import Image, ImageOps
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

IMAGE_EXT = (".jpg", ".jpeg", ".png", ".webp", ".bmp")
NEGATIVE = ("text, watermark, logo, signature, extra person, background clutter, glasses glare, "
            "skin smoothing, beauty retouch, heavy makeup, face slimming, eye enlargement, "
            "different person, cartoon, anime, 3d render, lowres, deformed hands")

WORKFLOW_NOTE = (
    "未给 --workflow：本仓库不预置 ComfyUI 工作流模板。节点名随插件版本变，硬编码的模板在你机器上"
    "大概率加载失败——与其给一份看起来能跑的假模板，不如你在 ComfyUI 里『Save (API Format)』导出自己"
    "那份，把提示词位置写成 {{prompt}}、负向 {{negative}}、种子 {{seed}}、宽 {{width}}、高 {{height}}、"
    "步数 {{steps}}、CFG {{cfg}}、参考图文件名 {{image_name}}，再用 --workflow 传进来。")


def provider_meta():
    with open(os.path.join(lib.REFS, lib.FILES["providers"]), encoding="utf-8") as handle:
        return json.load(handle)


# --------------------------------------------------------------------------- 登记表 / 选片

def list_providers():
    items = provider_meta()["providers"]
    print(f"生成后端 G-01~G-{len(items):02d}：全部设计为本机开源服务。"
          f"status=unverified 表示本仓库没在真实 GPU 上跑通过这条链路，只保证协议形状与合规红线正确。")
    print("-" * 74)
    for p in items:
        print(f"{p['id']}  {p['name_zh']}")
        vram = f"≥{p['vram_gb']}GB" if p["vram_gb"] else "无本地显存要求"
        print(f"      协议 {p['kind']}   默认端点 {p['endpoint_default'] or '—'}   "
              f"{vram}   状态 {p['status']}")
        print(f"      身份来源：{p['identity_method']}")
        for need in p["requires"]:
            print(f"      需要：{need}")
        print(f"      许可：{p['license']}")
        print(f"      说明：{p['notes_zh']}")
        if p.get("upstream"):
            print(f"      上游：{p['upstream']}")
        print()
    print("把照片递给别人之前先想清楚：G-01~G-03 在你本机；G-05 若指向云端，等于上传人脸。")


def photo_candidates(directory):
    return sorted(p for p in glob.glob(os.path.join(directory, "**", "*"), recursive=True)
                  if p.lower().endswith(IMAGE_EXT) and os.path.isfile(p))


def scan_photos(directory):
    if not os.path.isdir(directory):
        raise SystemExit(f"目录不存在：{directory}")
    paths = photo_candidates(directory)
    if not paths:
        raise SystemExit(f"{directory} 下没有找到图片（支持 {'/'.join(IMAGE_EXT)}）")
    print(f"{directory} 下 {len(paths)} 张图，用 --photo <编号> 选一张：")
    for i, path in enumerate(paths, 1):
        dims = ""
        if HAS_PIL:
            try:
                with Image.open(path) as img:
                    dims = f"{img.width}×{img.height}  "
            except OSError:
                dims = "读不出尺寸  "
        print(f"  [{i:>3}] {dims}{os.path.getsize(path) / 1024:>7.0f}KB  {os.path.relpath(path)}")
    return paths


def resolve_photo(value, scan_dir):
    """--photo 既接受路径，也接受 --scan 打出来的编号，省一次复制粘贴。"""
    if value.strip().isdigit() and scan_dir:
        paths = photo_candidates(scan_dir)
        idx = int(value)
        if not 1 <= idx <= len(paths):
            raise SystemExit(f"编号 {idx} 超出范围：{scan_dir} 下共 {len(paths)} 张")
        return paths[idx - 1]
    if value.strip().isdigit():
        raise SystemExit("--photo 用编号时必须同时给 --scan 目录")
    hits = sorted(glob.glob(value))
    path = hits[0] if hits else value
    if not os.path.exists(path):
        raise SystemExit(f"照片不存在：{value}")
    return path


# --------------------------------------------------------------------------- 参考图预处理

def prep_source(path, spec, outdir, max_edge=1536):
    """EXIF 转正 + 按规格比例居中裁切。身份适配器吃的是「和成片同构图」的参考图；
    原图 3:4 而目标 1:1.4 时，模型会顺手把构图也重画一遍。"""
    info = {"source": path, "prepared": path, "notes": []}
    if not HAS_PIL:
        info["notes"].append("未安装 Pillow：参考图原样递出，构图比例差异由模型自己猜")
        return info
    with Image.open(path) as handle:
        img = ImageOps.exif_transpose(handle).convert("RGB")
    w, h = img.size
    info["original"] = [w, h]
    num, den = (float(i) for i in spec["aspect"].split(":"))
    want = num / den
    if abs(w / h - want) > 0.02:
        # 相对更宽就裁宽、相对更高就裁高；搞反了会裁出负数边距，PIL 拿黑边补上
        target_h, target_w = (h, round(h * want)) if w / h > want else (round(w / want), w)
        x0, y0 = (w - target_w) // 2, (h - target_h) // 2
        img = img.crop((x0, y0, x0 + target_w, y0 + target_h))
        lost = round((1 - (target_w * target_h) / (w * h)) * 100)
        note = f"按 {spec['id']} 的 1:{want:.3f} 居中裁切，丢弃 {lost}% 画面"
        if lost > 30:
            note += "——丢得偏多，头顶或肩膀可能已被切掉，建议先手动裁好再传"
        info["notes"].append(note)
    w, h = img.size
    if max(w, h) > max_edge:
        scale = max_edge / max(w, h)
        img = img.resize((round(w * scale), round(h * scale)), Image.LANCZOS)
        info["notes"].append(f"长边压到 {max_edge}px 再递给本机服务（不影响成片尺寸，成片按目标像素归位）")
    os.makedirs(outdir, exist_ok=True)
    stem = re.sub(r"\W+", "_", os.path.splitext(os.path.basename(path))[0])
    target = os.path.join(outdir, f"reference_{stem}.png")
    img.save(target, "PNG")
    info["prepared"] = target
    info["prepared_size"] = [img.width, img.height]
    return info


def round_mult(value, m=8):
    return max(m, round(value / m) * m)


def gen_size(spec):
    """扩散模型吃 8 的倍数；目标像素由后续校验与排版归位，这里只负责跑得动。"""
    w, h = spec["px"]
    return round_mult(w), round_mult(h)


# --------------------------------------------------------------------------- HTTP

def is_loopback(url):
    host = (urllib.parse.urlparse(url).hostname or "").lower()
    return host in ("localhost", "::1") or host.startswith("127.")


def http(url, method="GET", data=None, headers=None, timeout=90):
    req = urllib.request.Request(url, data=data, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read(), resp.headers.get("Content-Type", "")
    except urllib.error.HTTPError as exc:
        detail = exc.read()[:600].decode("utf-8", "replace")
        raise SystemExit(f"服务返回 {exc.code}：{url}\n{detail}\n"
                         "常见原因：节点/扩展名与你本机不一致、显存不足、参考图字段没被识别。")
    except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as exc:
        raise SystemExit(f"连不上 {url}（{exc}）\n"
                         "先确认开源服务已启动并监听该端口：ComfyUI 默认 8188；SD WebUI 需加 --api，默认 7860。")


def get_json(url, timeout=30):
    _, body, _ = http(url, timeout=timeout)
    return json.loads(body.decode("utf-8"))


def post_json(url, payload, timeout=90, extra_headers=None):
    headers = {"Content-Type": "application/json"}
    if extra_headers:
        headers.update(extra_headers)
    _, body, _ = http(url, "POST", json.dumps(payload).encode("utf-8"), headers, timeout)
    return json.loads(body.decode("utf-8"))


def multipart(url, field, path, fields, timeout=120):
    """ComfyUI 的 /upload/image 收的是 multipart，参考图先落到它的 input 目录。"""
    name = os.path.basename(path)
    ctype = "image/png" if path.lower().endswith(".png") else "image/jpeg"
    boundary = "specface" + format(random.getrandbits(48), "012x")
    with open(path, "rb") as handle:
        content = handle.read()
    parts = []
    for key, value in fields.items():
        parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{key}\"\r\n\r\n{value}\r\n"
                     .encode("utf-8"))
    parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{field}\"; "
                 f"filename=\"{name}\"\r\nContent-Type: {ctype}\r\n\r\n".encode("utf-8"))
    parts.append(content + f"\r\n--{boundary}--\r\n".encode("utf-8"))
    _, resp, _ = http(url, "POST", b"".join(parts),
                      {"Content-Type": f"multipart/form-data; boundary={boundary}"}, timeout)
    return json.loads(resp.decode("utf-8"))


def substitute(obj, tokens):
    """替换用户工作流里的占位符。整串等于占位符时按原类型替换——种子必须是数字，不能是字符串。"""
    if isinstance(obj, str):
        if obj in tokens:
            return tokens[obj]
        for key, value in tokens.items():
            if isinstance(value, str) and key in obj:
                obj = obj.replace(key, value)
        return obj
    if isinstance(obj, list):
        return [substitute(i, tokens) for i in obj]
    if isinstance(obj, dict):
        return {k: substitute(v, tokens) for k, v in obj.items()}
    return obj


# --------------------------------------------------------------------------- 请求体

def build_request(args, provider, spec, prompt, seed, image_name, n, width, height):
    """返回 (label, request, note)；request 为 None 表示这条后端不需要请求体。"""
    if provider["kind"] == "http-comfyui":
        if not args.workflow:
            return "comfyui-workflow", None, WORKFLOW_NOTE
        tokens = {"{{prompt}}": prompt, "{{negative}}": NEGATIVE, "{{seed}}": seed,
                  "{{width}}": width, "{{height}}": height, "{{steps}}": args.steps,
                  "{{cfg}}": args.cfg, "{{image_name}}": image_name}
        with open(args.workflow, encoding="utf-8") as handle:
            return "comfyui-workflow", substitute(json.loads(handle.read()), tokens), None

    if provider["kind"] == "http-webui":
        payload = {"prompt": prompt, "negative_prompt": NEGATIVE, "width": width, "height": height,
                   "steps": args.steps, "cfg_scale": args.cfg, "seed": seed,
                   "batch_size": n, "n_iter": 1, "alwayson_scripts": {}, "override_settings": {}}
        note = ("未给 --payload-extra：请求体里没有身份注入扩展的参数，WebUI 多半直接文生图——那必然不像本人。"
                "把你那套扩展的参数写成 JSON 传进来（会原样并进 alwayson_scripts）。")
        if args.payload_extra:
            with open(args.payload_extra, encoding="utf-8") as handle:
                extra = json.load(handle)
            payload["alwayson_scripts"] = extra.get("alwayson_scripts", payload["alwayson_scripts"])
            payload.update({k: v for k, v in extra.items() if k != "alwayson_scripts"})
            note = f"已并入 {args.payload_extra}"
        return "webui-txt2img", payload, note

    if provider["kind"] == "http-openai-images":
        payload = {"model": args.model_name, "prompt": prompt, "n": n,
                   "size": f"{width}x{height}", "response_format": "b64_json"}
        return ("openai-images", payload,
                "OpenAI 兼容的 /v1/images/generations 只带文字、不带参考图：这条协议本身不做身份注入。"
                "要身份请走 G-01/G-02/G-03；确实只做背景与着装重绘，加 --allow-no-identity 明确承担。")

    return "none", None, None


def identity_hits(request, keywords):
    if request is None:
        return []
    text = json.dumps(request, ensure_ascii=False).lower()
    return sorted({kw for kw in keywords if kw in text})


# --------------------------------------------------------------------------- 出图

def render_comfyui(endpoint, workflow, timeout):
    resp = post_json(endpoint + "/prompt", {"prompt": workflow}, timeout)
    if resp.get("error") or resp.get("node_errors"):
        raise SystemExit("ComfyUI 拒绝了这份工作流：\n" + json.dumps(resp, ensure_ascii=False)[:1200]
                         + "\n多半是节点名或权重路径与你本机不一致。")
    prompt_id = resp["prompt_id"]
    deadline = time.time() + timeout
    history = {}
    while time.time() < deadline:
        history = get_json(endpoint + "/history/" + prompt_id)
        if history.get(prompt_id):
            break
        time.sleep(1.5)
    else:
        raise SystemExit(f"等了 {timeout}s 还没出图。是否在排队？用 --timeout 加大等待。")
    images = []
    for node in history[prompt_id].get("outputs", {}).values():
        for img in node.get("images", []):
            qs = urllib.parse.urlencode({"filename": img["filename"],
                                         "subfolder": img.get("subfolder", ""),
                                         "type": img.get("type", "output")})
            _, body, _ = http(endpoint + "/view?" + qs, timeout=timeout)
            images.append((img["filename"], body))
    if not images:
        raise SystemExit("ComfyUI 报成功但没有任何图片输出：工作流里大概缺 SaveImage 节点。")
    return images


def render_webui(endpoint, payload, timeout):
    resp = post_json(endpoint + "/sdapi/v1/txt2img", payload, timeout)
    items = resp.get("images") or []
    if not items:
        raise SystemExit("WebUI 返回空 images：多半是启动没加 --api，或扩展在服务端报错了，去看服务日志。")
    return [(f"webui-{i:02d}.png", base64.b64decode(b64)) for i, b64 in enumerate(items, 1)]


def render_openai(endpoint, payload, timeout, api_key):
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else None
    resp = post_json(endpoint + "/v1/images/generations", payload, timeout, headers)
    data = resp.get("data") or []
    if not data:
        raise SystemExit("服务端返回空 data：" + json.dumps(resp, ensure_ascii=False)[:400])
    return [(f"openai-{i:02d}.png", base64.b64decode(d["b64_json"]))
            for i, d in enumerate(data, 1) if d.get("b64_json")]


def probe(endpoint):
    endpoint = endpoint.rstrip("/")
    for path, label in (("/system_stats", "ComfyUI"), ("/sdapi/v1/options", "SD WebUI"),
                        ("/v1/models", "OpenAI 兼容")):
        try:
            _, body, _ = http(endpoint + path, timeout=10)
        except SystemExit:
            continue
        print(f"  ✓ {endpoint}{path} 有响应（{label} 形状，{len(body)} 字节）：{body[:160].decode('utf-8', 'replace')}")
        if not is_loopback(endpoint):
            print("    ⚠ 这不是回环地址：连上它之后，你的照片会离开本机")
        return 0
    print(f"  ✗ {endpoint} 上三种已知协议都没应答。确认服务已启动、端口没记错。")
    return 1


# --------------------------------------------------------------------------- 主流程

def parse_args(argv):
    p = argparse.ArgumentParser(
        description="本人照片 + 编号 → 本机开源服务出图 → 本地规格校验",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="先跑 --list-providers 看清每个后端要什么；没有 GPU 也没有本地服务时，默认的 G-06 只导出产物不请求。")
    p.add_argument("--list-providers", dest="list_providers", action="store_true", help="列出生成后端后退出")
    p.add_argument("--scan", help="列出目录里的候选照片，供 --photo 按编号选择")
    p.add_argument("--probe", metavar="端点", help="探测某个服务在不在（依次试三种已知协议）")
    p.add_argument("--photo", help="本人照片路径或 --scan 里的编号（身份唯一来源）")
    p.add_argument("--spec", help="合规规格编号，如 S-09")
    p.add_argument("--persona", help="岗位气质编号，如 P-001")
    p.add_argument("--subject", help="客观外貌描述，补齐提示词里的主体段")
    p.add_argument("--subject-en", dest="subject_en", help="英文主体描述")
    p.add_argument("--wear", help="着装编号，缺省按岗位推荐")
    p.add_argument("--backdrop", help="背景光型编号，缺省按岗位推荐")
    p.add_argument("--mood", help="神态编号，缺省按岗位推荐")
    p.add_argument("--locked", action="store_true", help="批量锁定：必须显式给全 --wear/--backdrop/--mood")
    p.add_argument("--provider", default="G-06", help="生成后端编号，默认 G-06（只导出，不请求）")
    p.add_argument("--endpoint", help="覆盖后端默认端点；非回环地址需 --allow-remote")
    p.add_argument("--workflow", help="你自己从 ComfyUI 导出的 API 格式工作流 JSON")
    p.add_argument("--payload-extra", dest="payload_extra", help="JSON 文件，原样并入 WebUI 请求体（扩展参数）")
    p.add_argument("--model-name", dest="model_name", default="local", help="G-05 用的模型名")
    p.add_argument("--api-key-env", dest="api_key_env", help="从该环境变量读鉴权 key（密钥不进命令行、不进仓库）")
    p.add_argument("--prompt-lang", dest="prompt_lang", choices=("en", "zh"), default="en",
                   help="递给模型的提示词语言，默认英文")
    p.add_argument("--n", type=int, default=3, help="出几张候选，默认 3")
    p.add_argument("--seed", type=int, help="固定种子；批量生产必须锁")
    p.add_argument("--steps", type=int, default=30)
    p.add_argument("--cfg", type=float, default=4.5)
    p.add_argument("--timeout", type=int, default=300, help="等图超时秒数")
    p.add_argument("--out", default=os.path.join("out", "render"), help="输出目录（out/ 已在 .gitignore）")
    p.add_argument("--confirm-authorized", dest="authorized", metavar="关系",
                   help="确认照片归属：本人 / 已获书面授权的员工编号。不填不生成")
    p.add_argument("--allow-no-identity", dest="allow_no_identity", action="store_true",
                   help="允许没有身份注入的请求（等于承认成片可能不是本人，仅用于背景/着装重绘）")
    p.add_argument("--allow-remote", dest="allow_remote", action="store_true",
                   help="允许端点指向非本机地址（照片将离开本机）")
    p.add_argument("--dry-run", dest="dry_run", action="store_true", help="只写请求体，不发任何请求")
    return p.parse_args(argv)


def preflight(args):
    if not args.photo:
        raise SystemExit("必须给 --photo：工牌头像的身份只能来自一张真实照片。\n"
                         "只想凭文字生成一个『不存在的人』，那是写真需求，请用 prompt_spec.py，别用这个。")
    if not args.authorized:
        raise SystemExit(
            "必须加 --confirm-authorized 说明照片归属（本人 / 已授权员工编号）。\n"
            "人脸是敏感个人信息：未经授权处理他人照片可能构成侵权，用于身份认证场景可能触犯法律。\n"
            "本工具也拒绝一切『用生成照片去过门禁 / 活体检测 / 实名认证』的用法。")
    if not HAS_PIL:
        print("⚠ 未安装 Pillow：参考图不做 EXIF 转正与构图对齐，出片构图漂移概率明显上升（pip install pillow）")


def main(argv=None):
    lib.force_utf8()
    args = parse_args(argv if argv is not None else sys.argv[1:])

    if args.list_providers:
        list_providers()
        return 0
    if args.scan and not args.photo:
        scan_photos(args.scan)
        return 0
    if args.probe:
        return probe(args.probe)

    missing = [flag for flag, value in (("--spec", args.spec), ("--persona", args.persona),
                                        ("--subject", args.subject)) if not value]
    if missing:
        raise SystemExit("缺少必填参数：" + " ".join(missing) + "\n编号见 PERSONAS.md / SPECS.md，后端见 --list-providers。")

    provider = pick("providers", args.provider)
    preflight(args)
    reasons = prompt_spec.auto_fill(args)
    zh, en, persona, wear, backdrop, mood, spec = build_prompt(args, args.subject, args.subject_en)
    prompt_zh, prompt_en = "".join(zh), " ".join(en)
    prompt = prompt_en if args.prompt_lang == "en" else prompt_zh
    if args.prompt_lang == "en" and not args.subject_en and re.search(r"[\u4e00-\u9fff]", args.subject):
        reasons.append("--subject 是中文却递英文提示词：补一份 --subject-en，否则部分模型会把中文描述"
                       "连排版习惯一起带进画面")

    photo = resolve_photo(args.photo, args.scan)
    seed = args.seed if args.seed is not None else random.getrandbits(31)
    batch = time.strftime("%Y%m%d-%H%M%S")
    outdir = os.path.join(args.out, f"{spec['id']}_{provider['id']}_{batch}")
    prepared = prep_source(photo, spec, outdir)
    width, height = gen_size(spec)
    image_name = os.path.basename(prepared["prepared"])

    print("=" * 70)
    print(f"组合  {spec['id']} × {persona['id']} × {wear['id']} × {backdrop['id']} × {mood['id']}")
    print(f"后端  {provider['id']} {provider['name_zh']} · {provider['kind']} · 状态 {provider['status']}")
    tail = f" → {os.path.basename(prepared['prepared'])} {prepared.get('prepared_size')}" if HAS_PIL else ""
    print(f"参考  {prepared['source']}{tail}")
    print(f"目标  {spec['px'][0]}×{spec['px'][1]}px，生成用 {width}×{height}（就近取 8 的倍数）"
          f"  种子 {seed}  候选 {args.n} 张")
    for note in prepared["notes"] + reasons:
        print(f"· {note}")
    print("=" * 70)

    os.makedirs(outdir, exist_ok=True)
    for name, text in (("prompt_en.txt", prompt_en), ("prompt_zh.txt", prompt_zh), ("negative.txt", NEGATIVE)):
        with open(os.path.join(outdir, name), "w", encoding="utf-8") as handle:
            handle.write(text + "\n")

    label, request, note = build_request(args, provider, spec, prompt, seed, image_name,
                                         args.n, width, height)
    if note:
        print(f"· {note}")
    if request is not None:
        req_name = "workflow.json" if label == "comfyui-workflow" else "request.json"
        with open(os.path.join(outdir, req_name), "w", encoding="utf-8") as handle:
            json.dump(request, handle, ensure_ascii=False, indent=2)
        print(f"请求体已写出：{os.path.join(outdir, req_name)}")

    keywords = provider_meta()["identity_keywords"]
    hits = identity_hits(request, keywords)
    if request is not None and not hits and not args.allow_no_identity:
        raise SystemExit(
            "拒跑：请求体里找不到任何身份注入节点/扩展（关键词：" + "、".join(keywords) + "）。\n"
            "没有身份注入的文生图会画出一个『更好看但不是本人』的人，而这正是工牌头像唯一的不通过条件。\n"
            "两条路：① 按上面的提示给出 --workflow / --payload-extra；② 确实只做背景与着装重绘，加 --allow-no-identity。")
    if hits:
        print(f"✓ 身份注入检查：请求体里出现 {'、'.join(hits)}")

    endpoint = (args.endpoint or provider["endpoint_default"] or "").rstrip("/")
    if endpoint and not is_loopback(endpoint):
        if not args.allow_remote:
            raise SystemExit(f"端点 {endpoint} 不是本机地址。加 --allow-remote 才继续——"
                             "但那意味着把人脸上传给第三方，请先确认本人与客户知情同意。")
        print(f"⚠ 已确认发往非本机端点 {endpoint}：照片离开本机")

    manifest = {
        "batch": batch, "provider": provider["id"], "provider_status": provider["status"],
        "provider_kind": provider["kind"], "endpoint": endpoint or None,
        "codes": {"spec": spec["id"], "persona": persona["id"], "wear": wear["id"],
                  "backdrop": backdrop["id"], "mood": mood["id"]},
        "seed": seed, "gen_px": [width, height], "n": args.n, "requested": bool(request),
        "authorized_as": args.authorized, "identity_nodes": hits,
        "source_photo": os.path.abspath(photo), "outputs": [], "spec_check": {},
        "privacy": "本清单与全部成图都在 out/ 下（已 gitignore）。参考图与成图不要提交、不要转发。",
        "compliance": "生成结果只能用于工牌/头像等展示用途，不得用于通过人脸识别、活体检测、实名认证。",
    }

    if args.dry_run or request is None or provider["kind"] == "recipe":
        print("\n[dry-run / 该后端不代跑] 到此为止，没有发起任何请求。")
        if provider["kind"] == "recipe":
            print(f"下一步（{provider['id']}）：把 {os.path.join(outdir, 'prompt_en.txt')}、目标尺寸 "
                  f"{width}×{height}、种子 {seed} 填进上游官方脚本；本仓库不代跑 torch，也不替它的权重许可背书。")
        print(f"产物目录：{outdir}")
        manifest["mode"] = "export-only"
        with open(os.path.join(outdir, "render_manifest.json"), "w", encoding="utf-8") as handle:
            json.dump(manifest, handle, ensure_ascii=False, indent=2)
        return 0

    if provider["kind"] == "http-comfyui":
        uploaded = multipart(endpoint + "/upload/image", "image", prepared["prepared"],
                             {"type": "input", "overwrite": "true"}, args.timeout)
        server_name = uploaded.get("name") or image_name
        if server_name != image_name:
            print(f"· 参考图已上传到 ComfyUI input 目录，文件名 {server_name}")
            _, request, _ = build_request(args, provider, spec, prompt, seed, server_name,
                                          args.n, width, height)
        images = render_comfyui(endpoint, request, args.timeout)
    elif provider["kind"] == "http-webui":
        images = render_webui(endpoint, request, args.timeout)
    else:
        api_key = os.environ.get(args.api_key_env) if args.api_key_env else None
        images = render_openai(endpoint, request, args.timeout, api_key)

    import check_spec
    for i, (name, body) in enumerate(images, 1):
        ext = os.path.splitext(name)[1] or ".png"
        target = os.path.join(outdir, f"{spec['id']}_{persona['id']}_{seed}_{i:02d}{ext}")
        with open(target, "wb") as handle:
            handle.write(body)
        manifest["outputs"].append(target)
        print(f"  ✓ {os.path.basename(target)}")
        if HAS_PIL:
            rows = check_spec.check(target, spec)
            manifest["spec_check"][target] = rows
            print(f"      规格自检 {sum(1 for r in rows if r['result'] is True)} 过 / "
                  f"{sum(1 for r in rows if r['result'] is False)} 不过")
            for row in rows:
                mark = {True: "✓", False: "✗"}.get(row["result"], "-")
                print(f"      [{mark}] {row['check']:<11} {row['detail']}")
        else:
            print("      未安装 Pillow，跳过规格自检")
    manifest["mode"] = "rendered"

    with open(os.path.join(outdir, "render_manifest.json"), "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=2)

    first = manifest["outputs"][0] if manifest["outputs"] else "成图"
    print(f"\n产物：{outdir}（{len(manifest['outputs'])} 张候选 + render_manifest.json）")
    print("下一步：由本人或直属主管从候选里挑一张，不要由生成者单方面定稿")
    print(f"  python scripts/guide_overlay.py {first} --spec {spec['id']}     # 看差在哪")
    print(f"  python scripts/print_export.py {first} --spec {spec['id']} --paper T-02 --cut-marks")
    if provider["status"] != "verified":
        print(f"⚠ {provider['id']} 在本仓库标记为 unverified：这条链路我们没在真实 GPU 上跑通过。"
              "第一次跑请盯服务日志；跑通了欢迎提 PR 改成 verified 并附证据。")
    print("提醒：identity_matrix.json 里所有模型仍为待测——像不像本人这件事，目前只能靠人眼确认。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
