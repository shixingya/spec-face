#!/usr/bin/env python3
"""从 references/*.json 生成可 grep 的 Markdown 图鉴（PERSONAS.md / SPECS.md）。

    python scripts/build_docs.py
"""

import os

import lib

PERSONAS_OUT = os.path.join(lib.ROOT, "PERSONAS.md")
SPECS_OUT = os.path.join(lib.ROOT, "SPECS.md")


def w(handle, line=""):
    handle.write(line + "\n")


def join(items, sep="、"):
    return sep.join(items)


def rgb_text(values, tolerance=None):
    if not values:
        return "不限"
    base = "rgb({})".format(", ".join(str(v) for v in values))
    return base if tolerance is None else f"{base} ±{tolerance}"


def build_personas():
    personas = lib.load("personas")
    wear, backdrops, moods = lib.index("wear"), lib.index("backdrops"), lib.index("moods")
    with open(PERSONAS_OUT, "w", encoding="utf-8") as f:
        w(f, "# 岗位气质 · 着装 · 背景光型 · 神态 编号图鉴")
        w(f)
        w(f, "> 本文件由 `scripts/build_docs.py` 从 `references/*.json` 生成，**不要手工编辑**。")
        w(f)
        w(f, "- 岗位 `P`：决定「像个干这行的人」")
        w(f, "- 着装 `W`：决定「穿什么」")
        w(f, "- 背景光型 `B`：决定「在什么环境、什么光」")
        w(f, "- 神态 `E`：决定「什么表情」")
        w(f, "- 合规规格 `S`：见 [SPECS.md](SPECS.md)")
        w(f)
        w(f, "组装一条提示词：")
        w(f)
        w(f, "```bash")
        w(f, 'python scripts/prompt_spec.py --spec S-09 --persona P-001 --subject "30岁男性，圆脸，短寸发，自然肤色"')
        w(f, "```")
        w(f)

        w(f, "## 一、岗位气质（P）")
        w(f)
        w(f, "| 编号 | 岗位 | 行业 | 气质 | 眼神 | 姿态 |")
        w(f, "| :-- | :-- | :-- | :-- | :-- | :-- |")
        for p in personas:
            w(f, f"| **{p['id']}** | {p['name_zh']} / {p['name_en']} | {p['industry']} "
                 f"| {p['impression_zh']} | {p['gaze']} | {p['posture']} |")
        w(f)
        w(f, "### 风格描述原文")
        w(f)
        for p in personas:
            name = f"{p['name_zh']}（{p['name_en']}）"
            w(f, f"#### {p['id']} · {name}")
            w(f)
            w(f, f"- 关键词：{join(p['keywords_zh'])} / {join(p['keywords_en'], ', ')}")
            w(f, f"- 中文：{p['prompt_zh']}")
            w(f, f"- English: {p['prompt_en']}")
            w(f, f"- 推荐组合：着装 {join(p['wears'], '/')} · 背景 {join(p['backdrops'], '/')} "
                 f"· 神态 {join(p['moods'], '/')}")
            w(f, f"- ⚠ 易翻车：{p['pitfalls']}")
            w(f)

        w(f, "## 二、着装仪容（W）")
        w(f)
        w(f, "| 编号 | 名称 | 说明 | 适配行业 |")
        w(f, "| :-- | :-- | :-- | :-- |")
        for x in lib.load("wear"):
            w(f, f"| **{x['id']}** | {x['name_zh']} / {x['name_en']} | {x['desc_zh']} "
                 f"| {join(x['suitable_for'])} |")
        w(f)

        w(f, "## 三、背景与光型（B）")
        w(f)
        w(f, "| 编号 | 名称 | 目标底色 | 光型 | 适用 |")
        w(f, "| :-- | :-- | :-- | :-- | :-- |")
        for x in lib.load("backdrops"):
            color = rgb_text(x.get("bg_rgb"), x.get("bg_tolerance"))
            w(f, f"| **{x['id']}** | {x['name_zh']} / {x['name_en']} | {color} | {x['light_zh']} | {x['use_for']} |")
        w(f)

        w(f, "## 四、神态表情（E）")
        w(f)
        w(f, "| 编号 | 名称 | 微笑幅度 | 说明 | 合规提示 |")
        w(f, "| :-- | :-- | :-- | :-- | :-- |")
        for x in lib.load("moods"):
            note = x.get("compliance_note", "—")
            w(f, f"| **{x['id']}** | {x['name_zh']} / {x['name_en']} | {x['smile_intensity']:.2f} "
                 f"| {x['desc_zh']} | {note} |")
        w(f)

        w(f, "## 五、批量出图的一致性约定")
        w(f)
        w(f, "同一岗位、同一批人必须锁定同一组编号（尤其是背景与光型），否则整批一眼就能看出不齐：")
        w(f)
        for p in personas[:5]:
            cmd = (f"--spec S-09 --persona {p['id']} --wear {p['wears'][0]} "
                   f"--backdrop {p['backdrops'][0]} --mood {p['moods'][0]}")
            w(f, f"- {p['name_zh']}（批量）：`{cmd}`")
        w(f)
        w(f, "> 批量场景避开 `B-07 办公室轻度虚化`（环境光无法统一）。需要品牌背景请用 `B-08` 并先录入客户 RGB。")
        w(f)


def build_specs():
    with open(SPECS_OUT, "w", encoding="utf-8") as f:
        w(f, "# 合规规格编号图鉴（S）")
        w(f)
        w(f, "> 本文件由 `scripts/build_docs.py` 从 `references/specs.json` 生成，**不要手工编辑**。")
        w(f)
        w(f, "这是本项目和普通「AI 写真提示词库」最不一样的地方：一张工牌头像合不合格，先看它**能不能过规格**，"
             "再看它好不好看。头部占比、瞳孔线位置、底色、DPI、文件大小，任何一项超标，这张图就是废的。")
        w(f)
        w(f, "| 编号 | 规格 | 尺寸 | 比例 | 底色 | 头部占比 | 瞳孔线（自底部） | 体积上限 | 状态 |")
        w(f, "| :-- | :-- | :-- | :-- | :-- | :-- | :-- | :-- | :-- |")
        for s in lib.load("specs"):
            mm = f"{s['size_mm'][0]}×{s['size_mm'][1]}mm" if s.get("size_mm") else "—"
            px = f"{s['px'][0]}×{s['px'][1]}px @{s['dpi']}dpi"
            color = rgb_text(s.get("bg_rgb")) if s.get("bg_rgb") else s["bg_name"]
            head = f"{lib.pct(s['head_height_ratio'][0])}–{lib.pct(s['head_height_ratio'][1])}"
            eye = f"{lib.pct(s['eye_line_ratio'][0])}–{lib.pct(s['eye_line_ratio'][1])}"
            w(f, f"| **{s['id']}** | {s['name_zh']} / {s['name_en']} | {mm} · {px} | 1:{s['aspect']} "
                 f"| {color} | {head} | {eye} | {s['max_kb']}KB | {s['status']} |")
        w(f)
        w(f, "## 每个规格的完整约束")
        w(f)
        for s in lib.load("specs"):
            name = f"{s['name_zh']}（{s['name_en']}）"
            w(f, f"### {s['id']} · {name}")
            w(f)
            w(f, f"- 用途：{s['use_for']}")
            w(f, f"- 表情要求：{s['expression']}")
            w(f, f"- 底色：{s['bg_name']}（目标 {rgb_text(s.get('bg_rgb'), s.get('bg_tolerance'))}）")
            w(f, f"- 头部高度占比：{lib.pct(s['head_height_ratio'][0])}–{lib.pct(s['head_height_ratio'][1])}")
            w(f, f"- 瞳孔线位置：自底部 {lib.pct(s['eye_line_ratio'][0])}–{lib.pct(s['eye_line_ratio'][1])}")
            w(f, f"- 格式：{join(s['formats'], '/')}，≤{s['max_kb']}KB")
            w(f, f"- 自动校验项：`{join(s['checks'], ', ')}`")
            if s.get("px_rule"):
                w(f, f"- 像素规则：{s['px_rule']}")
            if s.get("card_size_mm"):
                w(f, f"- 卡片本体：{s['card_size_mm'][0]}×{s['card_size_mm'][1]}mm，"
                     f"头像区 {s['portrait_area_mm'][0]}×{s['portrait_area_mm'][1]}mm")
            w(f, f"- 备注：{s.get('notes_zh', '—')}")
            if s["status"] == "needs_verification":
                w(f, "- ⚠ **needs_verification**：以上为常用工程参考值，正式提交前必须比对受理方"
                     "（使领馆 / 出入境 / 交管 / 平台）的最新公告。")
            w(f)

        w(f, "## 本地自检")
        w(f)
        w(f, "```bash")
        w(f, "pip install pillow              # 必需：读取尺寸、底色、DPI")
        w(f, "pip install opencv-python       # 可选：自动估算头部占比")
        w(f, "python scripts/check_spec.py 成图.jpg --spec S-01")
        w(f, "python scripts/check_spec.py batch/*.jpg --spec S-09 --json")
        w(f, "```")
        w(f)
        w(f, "校验器只报告它能客观判定的项；无法自动判定的会标 `SKIP` 而不是「通过」。"
             "**本项目不谎报结果**——这也是商业版和免费模板最本质的区别。")
        w(f)

        w(f, "## 打印载体（T）与实算可排张数")
        w(f)
        w(f, "> 由 `scripts/build_docs.py` 用与 `print_export.py` 相同的排版函数算出，"
             "不是「6 寸一般排 8 张」这类经验数字。改留白或间距后请重算。")
        w(f)
        w(f, "| 编号 | 载体 | 尺寸 | @300dpi | 排版 | 出血/间距/留白 | 常用规格实算 |")
        w(f, "| :-- | :-- | :-- | :-- | :-- | :-- | :-- |")
        specs = lib.index("specs")
        for t in lib.load("papers"):
            tw, th = t["size_mm"]
            px = f"{lib.mm_to_px(tw, t['dpi_default'])}×{lib.mm_to_px(th, t['dpi_default'])}px"
            fits = []
            for sid in t["common_specs"]:
                s = specs.get(sid)
                if not s:
                    continue
                count = lib.print_fit(t, s)
                if count is None:
                    continue
                fits.append(f"{sid} {s['name_zh']} {count} 张/版" if count else f"{sid} 排不下")
            layout = "整版单张" if t["layout"] == "single" else "多联"
            w(f, f"| **{t['id']}** | {t['name_zh']} | {tw}×{th}mm | {px} | {layout} "
                 f"| {t['bleed_mm_default']}/{t['gap_mm_default']}/{t['margin_mm_default']}mm "
                 f"| {join(fits)} |")
        w(f)
        w(f, "```bash")
        w(f, "python scripts/print_export.py --list-papers")
        w(f, "python scripts/print_export.py 成图/*.jpg --spec S-01 --paper T-02 --cut-marks --out out/print")
        w(f, "python scripts/print_export.py 成图/*.jpg --spec S-09 --paper T-06 --cmyk")
        w(f, "```")
        w(f)
        w(f, "送件口径：**冲印店收 `.jpg`（RGB），印刷厂/卡厂收 `_cmyk.tif`，自助照片机收 `.jpg` 且不要出血。**")
        w(f)


if __name__ == "__main__":
    lib.force_utf8()
    build_personas()
    build_specs()
    print("已生成 " + os.path.relpath(PERSONAS_OUT, lib.ROOT) + " 与 " + os.path.relpath(SPECS_OUT, lib.ROOT))
