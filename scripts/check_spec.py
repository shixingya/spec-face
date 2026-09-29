#!/usr/bin/env python3
"""本地规格自检：把成图拉回目标规格做客观校验，不上传任何图片。

    python scripts/check_spec.py 成图.jpg --spec S-09
    python scripts/check_spec.py *.jpg --spec S-01 --json

依赖 Pillow（可选 opencv-python 用于头部占比自动测量）。缺依赖时对应项标记 SKIP，不谎报通过。
"""

import argparse
import glob
import json
import os
import sys

import lib
from lib import pick, pct

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


def measure_head_ratio(path):
    """用 OpenCV 正脸检测估算头部高度占比。返回 None 表示无法测量。"""
    try:
        import cv2
    except ImportError:
        return None
    cascade = os.path.join(os.path.dirname(cv2.__file__), "data", "haarcascade_frontalface_default.xml")
    if not os.path.exists(cascade):
        return None
    img = cv2.imread(path)
    if img is None:
        return None
    faces = cv2.CascadeClassifier(cascade).detectMultiScale(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), 1.15, 5)
    if len(faces) != 1:
        return None
    _x, _y, w, h = faces[0]
    # haar 框只覆盖眉毛到下巴，换算整头高度约需放大 1.25 倍
    return {"head_ratio": round(h * 1.25 / img.shape[0], 3), "faces": len(faces)}


def border_color(path):
    img = Image.open(path).convert("RGB")
    w, h = img.size
    strip, step = [], max(1, (w * h) // 400)
    for x in range(0, w, step):
        strip.append(img.getpixel((x, 0)))
        strip.append(img.getpixel((x, h - 1)))
    for y in range(0, h, step):
        strip.append(img.getpixel((0, y)))
        strip.append(img.getpixel((w - 1, y)))
    n = len(strip)
    return tuple(round(sum(c[i] for c in strip) / n) for i in range(3))


def check(path, spec):
    results = []

    def add(name, ok, detail):
        results.append({"check": name, "result": ok, "detail": detail})

    kb = round(os.path.getsize(path) / 1024, 1)
    ext = os.path.splitext(path)[1].lstrip(".").lower()

    add("format", ext in spec["formats"], f"实际 .{ext}，允许 {'/'.join(spec['formats'])}")
    add("max_kb", kb <= spec["max_kb"], f"实际 {kb}KB，上限 {spec['max_kb']}KB")

    if not HAS_PIL:
        add("px", "SKIP", "未安装 Pillow，无法读取像素尺寸")
        return results
    img = Image.open(path)
    w, h = img.size

    if "px_rule" in spec:
        min_w, min_h = spec["px"]
        add("px", w >= min_w and h >= min_h, f"实际 {w}×{h}，要求不低于 {min_w}×{min_h}")
    else:
        tw, th = spec["px"]
        tol = 0.02
        add("px", abs(w - tw) / tw <= tol and abs(h - th) / th <= tol,
            f"实际 {w}×{h}，目标 {tw}×{th}（±2%）")

    num, den = (float(i) for i in spec["aspect"].split(":"))
    actual = round(w / h, 3)
    want = round(num / den, 3)
    add("aspect", abs(actual - want) <= 0.02, f"实际 1:{actual}，目标 1:{want}")

    dpi = (img.info.get("dpi") or (None, None))[0]
    if dpi:
        add("dpi", round(dpi) >= spec["dpi"] * 0.99, f"元数据 {round(dpi)}dpi，要求 {spec['dpi']}dpi")
    else:
        add("dpi", "SKIP", "图片无 DPI 元数据；印刷用途请由导出工具写入，而非只改像素数")

    if spec.get("bg_rgb"):
        rgb = border_color(path)
        target = tuple(spec["bg_rgb"])
        tol = spec.get("bg_tolerance") or 12
        worst = max(abs(a - b) for a, b in zip(rgb, target))
        add("bg_color", worst <= tol, f"边框均色 rgb{rgb}，目标 rgb{target}±{tol}，最大偏差 {worst}")
    else:
        add("bg_color", "SKIP", f"本规格不限定底色（{spec['bg_name']}）")

    measured = measure_head_ratio(path)
    if measured and measured["faces"] == 1:
        lo, hi = spec["head_height_ratio"]
        add("head_ratio", lo - 0.03 <= measured["head_ratio"] <= hi + 0.03,
            f"检测头部占比 {measured['head_ratio']:.0%}，要求 {pct(lo)}–{pct(hi)}（haar 粗估，误差 ±3%）")
        eye = spec["eye_line_ratio"]
        add("eye_line", "SKIP", f"瞳孔线要求 底部起 {pct(eye[0])}–{pct(eye[1])}；haar 不足以定位瞳孔，请目视或换检测器")
    else:
        why = "未检测到人脸或检测到多张脸" if measured else "未安装 opencv-python"
        add("head_ratio", "SKIP", f"{why}；头部占比 {pct(spec['head_height_ratio'][0])}–{pct(spec['head_height_ratio'][1])} 需目视确认")
        add("eye_line", "SKIP", "同上")

    return results


def main(argv=None):
    lib.force_utf8()
    ap = argparse.ArgumentParser(description="spec-face 本地规格校验（图片不出本机）")
    ap.add_argument("images", nargs="+", help="待检查图片，支持通配符")
    ap.add_argument("--spec", required=True, help="合规规格编号，如 S-01")
    ap.add_argument("--json", dest="as_json", action="store_true")
    args = ap.parse_args(argv if argv is not None else sys.argv[1:])

    paths = []
    for pattern in args.images:
        hits = glob.glob(pattern)
        paths.extend(hits if hits else [pattern])
    spec = pick("specs", args.spec)
    report = {}
    for path in paths:
        if not os.path.exists(path):
            report[path] = [{"check": "file", "result": "FAIL", "detail": "文件不存在"}]
            continue
        report[path] = check(path, spec)

    if args.as_json:
        print(json.dumps({"spec": spec["id"], "files": report}, ensure_ascii=False, indent=2))
    else:
        print(f"规格 {spec['id']} {spec['name_zh']}  目标 {spec['px']}  {spec['dpi']}dpi  {spec['bg_name']}")
        if spec["status"] == "needs_verification":
            print("⚠ 本规格 needs_verification：正式提交前请比对受理方最新公告")
        if not HAS_PIL:
            print("⚠ 未安装 Pillow，仅做文件大小与格式检查：pip install pillow")
        print("-" * 64)
        for path, rows in report.items():
            print(f"\n{path}")
            for row in rows:
                mark = {"PASS": "✓", "FAIL": "✗", "SKIP": "-", True: "✓", False: "✗"}[row["result"]]
                print(f"  [{mark}] {row['check']:<12} {row['detail']}")

    failed = [f for rows in report.values() for r in rows if r["result"] in (False, "FAIL")]
    skipped = [r for rows in report.values() for r in rows if r["result"] == "SKIP"]
    if not args.as_json and skipped:
        print(f"\n{len(skipped)} 项跳过：本工具不谎报通过。人工目视确认后再交付。")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
