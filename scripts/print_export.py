#!/usr/bin/env python3
"""印刷交付：把成图按毫米级尺寸排到相纸上，一并给出 RGB 冲印稿与 CMYK 印刷稿。

    python scripts/print_export.py --list-papers
    python scripts/print_export.py 照片.jpg --spec S-01 --paper T-02 --dry-run
    python scripts/print_export.py *.jpg --spec S-02 --paper T-03 --cmyk --cut-marks --out out/print

设计取向：打印店返工只有三个原因——尺寸不对、偏色、裁切留白边。这个脚本一次把三条都堵掉：
按 mm×dpi 反算像素、同时产出 RGB（冲印）与 CMYK（印刷/卡厂）、出血由边缘像素复制补足。
所有能排几张都是实算，不写「6寸一般排8张」这种经验数字。

依赖 Pillow。缺依赖时直接退出，不做假排版。
"""

import argparse
import glob
import json
import os
import sys

import lib
from lib import mm_to_px, pick

try:
    from PIL import Image, ImageOps
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


def resolve_cell_mm(spec):
    """规格里能落到纸面上的尺寸：证件照是整张照片，工卡是卡面上的头像窗。"""
    mm = spec.get("size_mm")
    if mm:
        return list(mm), "整张照片"
    area = spec.get("portrait_area_mm")
    if area:
        return list(area), "卡面头像区"
    return None, None


def edge_bleed(img, bleed_px):
    """出血用边缘像素复制补齐，比纯色填充更不容易在裁切后露白边。"""
    if bleed_px <= 0:
        return img
    b = bleed_px
    w, h = img.size
    canvas = Image.new("RGB", (w + 2 * b, h + 2 * b))
    canvas.paste(img, (b, b))
    canvas.paste(img.crop((0, 0, 1, h)).resize((b, h)), (0, b))
    canvas.paste(img.crop((w - 1, 0, w, h)).resize((b, h)), (b + w, b))
    canvas.paste(img.crop((0, 0, w, 1)).resize((w, b)), (b, 0))
    canvas.paste(img.crop((0, h - 1, w, h)).resize((w, b)), (b, b + h))
    for box, pos in (
        ((0, 0, 1, 1), (0, 0)),
        ((w - 1, 0, w, 1), (b + w, 0)),
        ((0, h - 1, 1, h), (0, b + h)),
        ((w - 1, h - 1, w, h), (b + w, b + h)),
    ):
        canvas.paste(img.crop(box).resize((b, b)), pos)
    return canvas


def fit_into(img, cell_px, mode, bg_rgb):
    """crop=居中裁切（会丢画面）；pad=按比例缩进并补背景色（不丢画面但多一条边）。"""
    warnings = []
    target_w, target_h = cell_px
    src_w, src_h = img.size
    src_ratio, tgt_ratio = src_w / src_h, target_w / target_h
    scale = max(target_w / src_w, target_h / src_h)
    if abs(src_ratio - tgt_ratio) / tgt_ratio > 0.02:
        warnings.append(f"原图宽高比 {src_ratio:.3f} 与目标 {tgt_ratio:.3f} 不符，按 {mode} 处理")
    if scale > 1.5:
        warnings.append(f"原图 {src_w}×{src_h}px 需放大 {scale:.2f} 倍才够 {target_w}×{target_h}px，"
                        f"冲印出来会糊；建议回 prompt_spec.py 按本规格目标像素重新出图")
    if mode == "pad":
        fitted = ImageOps.contain(img, (target_w, target_h), Image.LANCZOS)
        canvas = Image.new("RGB", (target_w, target_h), bg_rgb)
        canvas.paste(fitted, ((target_w - fitted.size[0]) // 2, (target_h - fitted.size[1]) // 2))
        return canvas, warnings

    cover = img.resize((max(target_w, round(src_w * scale)), max(target_h, round(src_h * scale))),
                       Image.LANCZOS)
    left = (cover.size[0] - target_w) // 2
    top = (cover.size[1] - target_h) // 2
    cropped = cover.crop((left, top, left + target_w, top + target_h))
    lost = 1 - (target_w * target_h) / (cover.size[0] * cover.size[1])
    if lost > 0.12:
        warnings.append(f"居中裁切会丢掉约 {round(lost * 100)}% 画面，头顶或肩线有风险，建议改 --fit pad")
    return cropped, warnings


def sheet_size_mm(paper):
    mm = list(paper["size_mm"])
    if paper["orientation"] == "landscape":
        mm = [mm[1], mm[0]]
    return mm


def plan(spec, paper, args):
    cell_mm, cell_kind = resolve_cell_mm(spec)
    if not cell_mm:
        raise SystemExit(f"{spec['id']} {spec['name_zh']} 没有物理尺寸（纯数字规格），不能排版打印。")
    dpi = args.dpi or paper["dpi_default"]
    bleed = paper["bleed_mm_default"] if args.bleed is None else args.bleed
    gap = paper["gap_mm_default"] if args.gap is None else args.gap
    margin = paper["margin_mm_default"] if args.margin is None else args.margin

    sheet_mm = sheet_size_mm(paper)
    cell_total = [cell_mm[0] + 2 * bleed, cell_mm[1] + 2 * bleed]
    if paper.get("layout") == "single":
        # 卡面/放大件：整版只放一张，不做多联，也绝不为了排得下而转人物朝向
        if cell_total[0] > sheet_mm[0] - 2 * margin or cell_total[1] > sheet_mm[1] - 2 * margin:
            raise SystemExit(f"{spec['id']} 的{cell_kind} {cell_total[0]}×{cell_total[1]}mm（含出血）"
                             f"大于 {paper['name_zh']} 可用区域，无法输出。")
        grid = {"cols": 1, "rows": 1, "count": 1, "cell_mm": cell_mm, "rotated": False, "used_area": 0}
    else:
        grid = lib.best_grid(sheet_mm, cell_total, gap, margin, allow_rotate=args.allow_rotate)
        if grid is None:
            raise SystemExit(
                f"{spec['id']} 的 {cell_total[0]}×{cell_total[1]}mm（含出血 {bleed}mm）在 {paper['id']} {paper['name_zh']} "
                f"{sheet_mm[0]}×{sheet_mm[1]}mm 上排不下，留白 {margin}mm/间距 {gap}mm。减小留白或换纸。")
    return {
        "cell_mm": cell_mm, "cell_kind": cell_kind, "dpi": dpi,
        "bleed_mm": bleed, "gap_mm": gap, "margin_mm": margin,
        "sheet_mm": sheet_mm, "grid": grid,
        "cell_px": (mm_to_px(cell_mm[0], dpi), mm_to_px(cell_mm[1], dpi)),
        "sheet_px": (mm_to_px(sheet_mm[0], dpi), mm_to_px(sheet_mm[1], dpi)),
        "bleed_px": mm_to_px(bleed, dpi), "gap_px": mm_to_px(gap, dpi), "margin_px": mm_to_px(margin, dpi),
        "cell_total_mm": [cell_mm[0] + 2 * bleed, cell_mm[1] + 2 * bleed],
    }


def draw_cut_marks(canvas, origin, size, bleed_px, line_px):
    """裁切线画在成品尺寸边界上：出血在外、刀口在内，师傅一眼能看到切哪里。"""
    x, y = origin[0] + bleed_px, origin[1] + bleed_px
    w, h = size
    color = (120, 120, 120)
    for dx, dy, dw, dh in ((0, 0, w, line_px), (0, h - line_px, w, line_px),
                           (0, 0, line_px, h), (w - line_px, 0, line_px, h)):
        for px in range(x + dx, x + dx + dw):
            for py in range(y + dy, y + dy + dh):
                if 0 <= px < canvas.size[0] and 0 <= py < canvas.size[1]:
                    canvas.putpixel((px, py), color)


def compose(photos, p, args, sheet_no):
    dpi = p["dpi"]
    cols, rows = p["grid"]["cols"], p["grid"]["rows"]
    rotated = p["grid"]["rotated"]
    canvas = Image.new("RGB", p["sheet_px"], (245, 245, 245))
    capacity = cols * rows
    placed = 0

    cell_total_px = (mm_to_px(p["cell_total_mm"][0], dpi), mm_to_px(p["cell_total_mm"][1], dpi))
    if rotated:
        cell_total_px = (cell_total_px[1], cell_total_px[0])
    step_x = cell_total_px[0] + p["gap_px"]
    step_y = cell_total_px[1] + p["gap_px"]
    used_w = cols * cell_total_px[0] + (cols - 1) * p["gap_px"]
    used_h = rows * cell_total_px[1] + (rows - 1) * p["gap_px"]
    start_x = p["margin_px"] + (p["sheet_px"][0] - 2 * p["margin_px"] - used_w) // 2
    start_y = p["margin_px"] + (p["sheet_px"][1] - 2 * p["margin_px"] - used_h) // 2

    for row in range(rows):
        for col in range(cols):
            if placed >= len(photos):
                break
            item = photos[placed]
            target_cell_px = (p["cell_px"][1], p["cell_px"][0]) if rotated else p["cell_px"]
            fitted, warns = fit_into(item["image"], target_cell_px, args.fit, item["bg_rgb"])
            with_bleed = edge_bleed(fitted, p["bleed_px"])
            origin = (start_x + col * step_x, start_y + row * step_y)
            canvas.paste(with_bleed, origin)
            if args.cut_marks:
                draw_cut_marks(canvas, origin, with_bleed.size, p["bleed_px"], max(2, p["dpi"] // 100))
            item["warnings"].extend(warns)
            placed += 1

    label = f"sheet-{sheet_no:02d}"
    return canvas, {"label": label, "placed": placed, "capacity": capacity,
                    "start_xy_px": [start_x, start_y], "step_px": [step_x, step_y]}


def write_outputs(canvas, outdir, stem, args, dpi):
    written = []
    rgb_path = os.path.join(outdir, f"{stem}.jpg")
    canvas.save(rgb_path, "JPEG", quality=95, dpi=(dpi, dpi), optimize=True)
    written.append(("RGB 冲印稿（送照相馆/自助冲印机）", rgb_path))
    if args.cmyk:
        cmyk = canvas.convert("CMYK")
        tif_path = os.path.join(outdir, f"{stem}_cmyk.tif")
        cmyk.save(tif_path, dpi=(dpi, dpi))
        written.append(("CMYK 印刷稿（送印刷厂/卡厂）", tif_path))
    if args.pdf:
        pdf_path = os.path.join(outdir, f"{stem}.pdf")
        canvas.save(pdf_path, "PDF", resolution=dpi)
        written.append(("PDF 核对稿", pdf_path))
    return written


def main(argv=None):
    lib.force_utf8()
    ap = argparse.ArgumentParser(
        description="证件照/工牌头像的相纸排版导出",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "常用搭配：\n"
            "  一寸照送冲印： --spec S-01 --paper T-02\n"
            "  二寸照批量：   --spec S-02 --paper T-03 --cut-marks\n"
            "  工牌头像区：   --spec S-09 --paper T-06 --cmyk --bleed 1\n"
        ),
    )
    ap.add_argument("images", nargs="*", help="成图路径，支持通配符与多张，按顺序排")
    ap.add_argument("--spec", help="规格编号，如 S-01")
    ap.add_argument("--paper", default="T-02", help="纸张编号，默认 T-02（6寸）")
    ap.add_argument("--copies", type=int, default=1, help="每张照片印几份，默认 1")
    ap.add_argument("--dpi", type=int, help="覆盖默认 dpi（默认取纸张 dpi_default）")
    ap.add_argument("--bleed", type=float, help="出血 mm，默认取纸张 bleed_mm_default")
    ap.add_argument("--gap", type=float, help="刀口间距 mm，默认取纸张 gap_mm_default")
    ap.add_argument("--margin", type=float, help="整版留白 mm，默认取纸张 margin_mm_default")
    ap.add_argument("--fit", choices=["crop", "pad"], default="crop",
                    help="比例不符时的处理方式：crop 居中裁切（默认），pad 补背景色")
    ap.add_argument("--bg", default="auto", help="--fit pad 时的底色：auto 取规格 bg_rgb，或写 255,255,255")
    ap.add_argument("--allow-rotate", action="store_true",
                    help="允许把照片横过来排以提高纸张利用率。证件照默认绝不旋转——横向摆放的人像在冲印后是躺着的")
    ap.add_argument("--cmyk", action="store_true", help="额外产出 CMYK TIFF 印刷稿")
    ap.add_argument("--cut-marks", action="store_true", help="在成品边界画裁切线")
    ap.add_argument("--pdf", action="store_true", help="额外产出 RGB PDF 核对稿")
    ap.add_argument("--out", default=os.path.join("out", "print"), help="输出目录")
    ap.add_argument("--dry-run", action="store_true", help="只算排版方案，不读图、不出文件")
    ap.add_argument("--list-papers", action="store_true", help="列出纸张编号库")
    args = ap.parse_args(argv)

    if args.list_papers:
        for t in lib.load("papers"):
            print(f"{t['id']}  {t['name_zh']:<22} {t['size_mm'][0]}×{t['size_mm'][1]}mm  "
                  f"{t['dpi_default']}dpi  {t['layout']:<6} 出血{t['bleed_mm_default']}mm "
                  f"间距{t['gap_mm_default']}mm  常用 {','.join(t['common_specs'])}")
        return 0
    usage = ("用法：python scripts/print_export.py 图片 --spec S-01 --paper T-02\n"
             "只看排版方案：加 --dry-run\n"
             "先看纸张编号：python scripts/print_export.py --list-papers")
    if args.dry_run:
        if not args.spec:
            print("dry-run 也需要 --spec。\n" + usage)
            return 2
    elif not (args.spec and args.images):
        print("缺少参数。\n" + usage)
        return 2

    spec = pick("specs", args.spec)
    paper = lib.paper_index(args.paper)
    if not HAS_PIL:
        raise SystemExit("排版需要 Pillow：python -m pip install pillow")

    p = plan(spec, paper, args)
    grid = p["grid"]
    print(f"纸张 {paper['id']} {paper['name_zh']}：{p['sheet_mm'][0]}×{p['sheet_mm'][1]}mm "
          f"= {p['sheet_px'][0]}×{p['sheet_px'][1]}px @ {p['dpi']}dpi")
    print(f"单元 {spec['id']} {spec['name_zh']} 的{p['cell_kind']}：{p['cell_mm'][0]}×{p['cell_mm'][1]}mm"
          f" → {p['cell_px'][0]}×{p['cell_px'][1]}px；出血 {p['bleed_mm']}mm，间距 {p['gap_mm']}mm，留白 {p['margin_mm']}mm")
    print(f"可排 {grid['cols']}×{grid['rows']} = {grid['count']} 张/版"
          + ("（含横向摆放）" if grid["rotated"] else ""))
    if paper.get("layout") == "single":
        print(f"  {paper['name_zh']} 为整版单张载体：头像按目标尺寸居中放置，卡面其余区域留白，"
              f"由贵司卡面设计稿接管。")

    if args.dry_run:
        print("dry-run：未读取图片，未生成文件。")
        return 0

    paths = []
    for pattern in args.images:
        hits = sorted(glob.glob(pattern))
        paths.extend(hits if hits else [pattern])

    bg_rgb = None
    if args.bg == "auto":
        bg_rgb = spec.get("bg_rgb") or [255, 255, 255]
    else:
        try:
            bg_rgb = [int(v) for v in args.bg.split(",")]
        except ValueError:
            raise SystemExit(f"--bg 需要写成 255,255,255，实际 {args.bg}")
    if len(bg_rgb) != 3:
        raise SystemExit(f"--bg 需要 3 个通道值，实际 {bg_rgb}")

    photos, failed = [], []
    for path in paths:
        try:
            img = Image.open(path).convert("RGB")
        except Exception as exc:
            failed.append((path, str(exc)))
            continue
        photos.append({"path": path, "image": img, "bg_rgb": tuple(bg_rgb), "warnings": []})
    if not photos:
        print("没有读到任何图片：")
        for path, reason in failed:
            print(f"  ✗ {path} — {reason}")
        return 1

    expanded = []
    for item in photos:
        for _ in range(max(1, args.copies)):
            expanded.append(item)
    if failed:
        for path, reason in failed:
            print(f"  ! 跳过无法读取的 {path} — {reason}")

    os.makedirs(args.out, exist_ok=True)
    capacity = grid["count"]
    sheets = []
    index = 0
    sheet_no = 0
    stem_base = f"{spec['id']}_{paper['id']}"
    while index < len(expanded):
        sheet_no += 1
        batch = expanded[index:index + capacity]
        canvas, meta = compose(batch, p, args, sheet_no)
        written = write_outputs(canvas, args.out, f"{stem_base}_{meta['label']}", args, p["dpi"])
        sheets.append({"label": meta["label"], "placed": meta["placed"], "capacity": meta["capacity"],
                       "photos": [os.path.basename(i["path"]) for i in batch],
                       "outputs": [{"kind": k, "path": v} for k, v in written]})
        index += capacity

    all_warnings = []
    for item in photos:
        for w in item["warnings"]:
            all_warnings.append(f"{os.path.basename(item['path'])}: {w}")
    all_warnings = sorted(set(all_warnings))

    manifest = {
        "spec": {"id": spec["id"], "name_zh": spec["name_zh"]},
        "paper": {"id": paper["id"], "name_zh": paper["name_zh"], "size_mm": p["sheet_mm"]},
        "dpi": p["dpi"], "cell_mm": p["cell_mm"], "cell_kind": p["cell_kind"],
        "bleed_mm": p["bleed_mm"], "gap_mm": p["gap_mm"], "margin_mm": p["margin_mm"],
        "grid": {"cols": grid["cols"], "rows": grid["rows"], "count": grid["count"], "rotated": grid["rotated"]},
        "copies_per_photo": max(1, args.copies),
        "photos_requested": len(paths), "photos_placed": len(expanded),
        "sheets": sheets, "warnings": all_warnings,
        "cmyk_note": ("已产出 CMYK TIFF：无 ICC 色彩配置参与，属于通用近似换算，用于避免 RGB 直印偏色；"
                      "对色彩有硬要求（企业 VI 色、专色印刷）请让印厂用其 ICC 曲线或提供数码打样。"
                      ) if args.cmyk else "未做 CMYK 转换：只交了 RGB 冲印稿。送印刷厂前用 --cmyk 再导一次。",
        "lab_note": "冲印店：交 .jpg（RGB）。印刷厂/卡厂：交 _cmyk.tif。自助照片机：交 .jpg 且不要出血。",
    }
    manifest_path = os.path.join(args.out, f"{stem_base}_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=2)

    for sheet in sheets:
        print(f"  ✓ {sheet['label']}：{sheet['placed']}/{sheet['capacity']} 格  "
              f"→ {os.path.relpath(sheet['outputs'][0]['path'], os.getcwd())}")
    print(f"版式清单 {manifest_path}")
    if len(expanded) % capacity:
        print(f"提示：最后一版空 {capacity - len(expanded) % capacity} 格。"
              f"要么补 --copies，要么把它当核对稿。")
    if args.cmyk:
        print("CMYK 说明：" + manifest["cmyk_note"])
    else:
        print("配色说明：" + manifest["cmyk_note"])
    for w in all_warnings:
        print("  ! " + w)
    if spec["status"] == "needs_verification":
        print(f"  ⚠ {spec['id']} 标记 needs_verification，正式送印前请与受理方核对尺寸细则。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
