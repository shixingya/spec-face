#!/usr/bin/env python3
"""把规格画到照片上：头部高度带、瞳孔线带、背景取样区、圆形安全区。

    python scripts/guide_overlay.py 成图.jpg --spec S-09
    python scripts/guide_overlay.py *.jpg --spec S-11 --out out/guide --json

check_spec.py 给的是过/不过，这个脚本给的是「差在哪」。眼睛线该落在哪一条、
头该占多高、哪一圈裁成头像会被切掉耳朵——看图比看数字快得多。
纯本地处理，不上传任何图片。
"""

import argparse
import glob
import json
import os
import sys

import lib
from lib import pct, pick

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

SAFE_CIRCLE_RATIO = 0.70
LINE = (225, 60, 60, 255)
BAND = (225, 60, 60, 60)
CIRCLE = (30, 120, 220, 255)
SAMPLE = (250, 180, 20, 70)
# 中文字形只有 CJK 字体有；arial 画中文会出一排方框，所以优先试雅黑/黑体
FONT_CANDIDATES = ("msyh.ttc", "simhei.ttf", "C:/Windows/Fonts/msyh.ttc",
                   "/System/Library/Fonts/PingFang.ttc",
                   "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                   "arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")


def load_font(size):
    for name in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def geometry(size, spec):
    """把规格换算成这张图上的像素位置。所有比例都按「距底边」定义，绘图要翻到左上角原点。"""
    w, h = size
    head_lo, head_hi = spec["head_height_ratio"]
    eye_lo, eye_hi = spec["eye_line_ratio"]
    eye_band_top = h * (1 - eye_hi)
    eye_band_bottom = h * (1 - eye_lo)
    head_h_lo = h * head_lo
    head_h_hi = h * head_hi
    eye_mid = (eye_band_top + eye_band_bottom) / 2
    return {
        "frame_px": [w, h],
        "eye_line_band_y": [round(eye_band_top, 1), round(eye_band_bottom, 1)],
        "head_height_px": [round(head_h_lo, 1), round(head_h_hi, 1)],
        "head_box": [round(w / 2 - head_h_hi * 0.38, 1), round(eye_mid - head_h_hi / 2, 1),
                     round(w / 2 + head_h_hi * 0.38, 1), round(eye_mid + head_h_hi / 2, 1)],
        "safe_circle": None,
        "bg_sample_strips": spec.get("bg_rgb") is not None,
    }


def label(dr, xy, text, font, fill, canvas_w, canvas_h=None):
    """标注不许越界，也不许糊在照片上看不清：贴右边缘就整体左移，压到上下边界就收回来，
    并且先垫一层半透明白底再写字。"""
    x, y = xy
    box = dr.textbbox((x, y), text, font=font)
    tw, th = box[2] - box[0], box[3] - box[1]
    x = max(4, min(x, canvas_w - tw - 8))
    if canvas_h:
        y = max(2, min(y, canvas_h - th - 6))
    box = dr.textbbox((x, y), text, font=font)
    dr.rectangle([box[0] - 4, box[1] - 3, box[2] + 4, box[3] + 3], fill=(255, 255, 255, 205))
    dr.text((x, y), text, fill=fill, font=font)


def draw_overlay(img, spec, geo, font):
    w, h = img.size
    base = img.convert("RGBA")
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dr = ImageDraw.Draw(layer)

    top, bottom = geo["eye_line_band_y"]
    strip = max(2, int(min(w, h) * 0.03))
    if geo["bg_sample_strips"]:
        # 先铺取色区再画线和字，否则半透明黄条会把顶部的标注盖掉一半
        for box in ([0, 0, w, strip], [0, h - strip, w, h], [0, 0, strip, h], [w - strip, 0, w, h]):
            dr.rectangle(box, fill=SAMPLE)

    dr.rectangle([0, top, w, bottom], fill=BAND)
    dr.line([0, top, w, top], fill=LINE, width=2)
    dr.line([0, bottom, w, bottom], fill=LINE, width=2)
    lo, hi = spec["eye_line_ratio"]
    label(dr, (6, bottom + 4), f"瞳孔线带 {pct(lo)}–{pct(hi)}（距底边）", font, LINE, w, h)

    x0, y0, x1, y1 = geo["head_box"]
    dr.rectangle([x0, y0, x1, y1], outline=LINE, width=2)
    dr.line([x0 - 14, (y0 + y1) / 2, x0, (y0 + y1) / 2], fill=LINE, width=2)
    hl, hh = spec["head_height_ratio"]
    label(dr, (x0, y0 - 22), f"头部高度 {pct(hl)}–{pct(hh)}", font, LINE, w, h)

    if "safe_circle" in spec.get("checks", []):
        d = min(w, h) * SAFE_CIRCLE_RATIO
        cx, cy = w / 2, h / 2
        dr.ellipse([cx - d / 2, cy - d / 2, cx + d / 2, cy + d / 2], outline=CIRCLE, width=3)
        label(dr, (cx - d / 2, cy + d / 2 + 6), f"圆形安全区 {int(SAFE_CIRCLE_RATIO * 100)}%，五官须落在圈内",
              font, CIRCLE, w, h)
        geo["safe_circle"] = {"center": [round(cx, 1), round(cy, 1)], "diameter_px": round(d, 1)}

    if geo["bg_sample_strips"]:
        label(dr, (strip + 6, h - strip - 22), "背景取色区（check_spec 在此取样）", font,
              (170, 110, 0, 255), w, h)

    if spec.get("bg_rgb") is not None:
        sw = 26
        dr.rectangle([w - sw - 6, 6, w - 6, 6 + sw], fill=tuple(spec["bg_rgb"]) + (255,), outline=(0, 0, 0, 255))
        label(dr, (w - sw - 6, 6 + sw + 4), f"目标底色 {tuple(spec['bg_rgb'])}", font, (0, 0, 0, 255), w, h)

    return Image.alpha_composite(base, layer).convert("RGB")


def aspect_warn(size, spec):
    """比例不对时，按高度换算出来的辅助线位置对真实成图没有参考意义，先说清楚。"""
    num, den = (float(i) for i in spec["aspect"].split(":"))
    want = num / den
    actual = size[0] / size[1]
    if abs(actual - want) <= 0.02:
        return None
    return (f"原图 1:{actual:.3f} 与本规格 1:{want:.3f} 不符；"
            f"辅助线按原图高度换算，先裁到目标比例再看位置才准")


def annotate(path, spec, outdir, font_size):
    with Image.open(path) as handle:
        img = handle.convert("RGB")
    geo = geometry(img.size, spec)
    geo["aspect_warning"] = aspect_warn(img.size, spec)
    font = load_font(font_size)
    out = draw_overlay(img, spec, geo, font)
    os.makedirs(outdir, exist_ok=True)
    target = os.path.join(outdir, os.path.splitext(os.path.basename(path))[0] + "_guide.jpg")
    out.save(target, "JPEG", quality=92)
    return target, geo


def main(argv=None):
    lib.force_utf8()
    ap = argparse.ArgumentParser(description="规格辅助线与安全区预览")
    ap.add_argument("images", nargs="*", help="成图路径，支持通配符")
    ap.add_argument("--spec", help="规格编号，如 S-09 / S-11")
    ap.add_argument("--out", default=os.path.join("out", "guide"), help="输出目录")
    ap.add_argument("--font-size", type=int, default=16, help="标注字号，默认 16")
    ap.add_argument("--json", dest="as_json", action="store_true", help="输出像素级几何数据")
    args = ap.parse_args(argv)

    if not (args.images and args.spec):
        print("用法：python scripts/guide_overlay.py 成图.jpg --spec S-09")
        return 2
    if not HAS_PIL:
        raise SystemExit("绘图需要 Pillow：python -m pip install pillow")

    spec = pick("specs", args.spec)
    paths = []
    for pattern in args.images:
        hits = sorted(glob.glob(pattern))
        paths.extend(hits if hits else [pattern])

    results, failed = [], []
    for path in paths:
        try:
            target, geo = annotate(path, spec, args.out, args.font_size)
        except Exception as exc:
            failed.append((path, str(exc)))
            continue
        results.append({"image": path, "guide": target, **geo})

    if args.as_json:
        print(json.dumps({"spec": spec["id"], "results": results}, ensure_ascii=False, indent=2))
    else:
        print(f"规格 {spec['id']} {spec['name_zh']}：{spec['px'][0]}×{spec['px'][1]}px 目标")
        for r in results:
            print(f"  ✓ {r['image']} → {r['guide']}")
            if r.get("aspect_warning"):
                print(f"      ! {r['aspect_warning']}")
            print(f"      瞳孔线应落在 y {r['eye_line_band_y'][0]}–{r['eye_line_band_y'][1]}px；"
                  f"头部高度 {r['head_height_px'][0]}–{r['head_height_px'][1]}px")
            if r["safe_circle"]:
                print(f"      圆形安全区 直径 {r['safe_circle']['diameter_px']}px，圆心 {r['safe_circle']['center']}")
    for path, reason in failed:
        print(f"  ✗ {path} — {reason}")
    if not results:
        return 1
    print("说明：辅助线是按规格比例画的容差带，不是人脸检测结果。要客观判定请用 check_spec.py。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
