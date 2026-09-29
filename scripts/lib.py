"""spec-face 资产加载与提示词组装的公共库。"""

import json
import os
import sys


def force_utf8():
    """Windows 控制台默认 GBK，✓/✗ 与中文会炸；统一切到 UTF-8。"""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REFS = os.path.join(ROOT, "references")

FILES = {
    "personas": "personas.json",
    "wear": "wear.json",
    "backdrops": "backdrops.json",
    "moods": "moods.json",
    "specs": "specs.json",
    "identity": "identity_matrix.json",
}

PLURAL_KEY = {
    "personas": "personas",
    "wear": "wear",
    "backdrops": "backdrops",
    "moods": "moods",
    "specs": "specs",
}


def load(section):
    path = os.path.join(REFS, FILES[section])
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    if section == "identity":
        return data
    return data[PLURAL_KEY[section]]


def index(section):
    return {item["id"]: item for item in load(section)}


def pick(section, item_id):
    found = index(section).get(item_id)
    if found is None:
        valid = ", ".join(sorted(index(section)))
        raise SystemExit(f"编号错误：{item_id} 不是有效的{section}编号。可用：{valid}")
    return found


def pct(ratio):
    return f"{round(ratio * 100)}%"


def target_px(spec):
    w, h = spec["px"]
    return f"{w}×{h}px"


def build_prompt(args, subject, subject_en=None):
    persona = pick("personas", args.persona)
    wear = pick("wear", args.wear)
    backdrop = pick("backdrops", args.backdrop)
    mood = pick("moods", args.mood)
    spec = pick("specs", args.spec)

    head = spec["head_height_ratio"]
    eye = spec["eye_line_ratio"]
    bg_name = spec["bg_name"]
    bg_name_en = spec.get("bg_name_en", bg_name)
    expr_en = spec.get("expression_en", spec["expression"])

    zh = [
        f"职业形象照 / 工牌头像。拍摄对象：{subject}。",
        f"气质定位（{persona['id']} {persona['name_zh']}）：{persona['prompt_zh']}。",
        f"着装（{wear['id']} {wear['name_zh']}）：{wear['prompt_zh']}。",
        f"背景与光型（{backdrop['id']} {backdrop['name_zh']}）：{backdrop['prompt_zh']}；{backdrop['light_zh']}。",
        f"神态（{mood['id']} {mood['name_zh']}）：{mood['prompt_zh']}。",
        (
            f"构图与规格（{spec['id']} {spec['name_zh']}，{target_px(spec)} / {spec['dpi']}dpi / {bg_name}）："
            f"{spec['expression']}；"
            f"头部高度占画面 {pct(head[0])}–{pct(head[1])}；"
            f"瞳孔线位于画面底部起 {pct(eye[0])}–{pct(eye[1])} 之间；"
            f"背景为{bg_name}，均匀无色斑与意外阴影。"
        ),
        "画面内不得出现文字、标识、其他人物、无关物体与镜面反射。",
        "身份保真是唯一通过条件：以上传的参考照片作为人脸的唯一来源，"
        "禁止磨皮、瘦脸、放大眼睛、改变五官比例与肤色基调；宁可素净，不可失真。",
    ]

    en = [
        f"Professional headshot for employee badge. Subject: {subject_en or subject}.",
        f"Persona ({persona['id']} {persona['name_en']}): {persona['prompt_en']}.",
        f"Wardrobe ({wear['id']} {wear['name_en']}): {wear['prompt_en']}.",
        f"Backdrop and lighting ({backdrop['id']} {backdrop['name_en']}): {backdrop['prompt_en']}; {backdrop['light_en']}.",
        f"Expression ({mood['id']} {mood['name_en']}): {mood['prompt_en']}.",
        (
            f"Composition and spec ({spec['id']} {spec['name_en']}, {target_px(spec)} / {spec['dpi']}dpi / {bg_name_en}): "
            f"{expr_en}; "
            f"head height {pct(head[0])}-{pct(head[1])} of frame; "
            f"eye line {pct(eye[0])}-{pct(eye[1])} measured from the bottom edge; "
            "backdrop even and free of patches or accidental shadow."
        ),
        "No text, logos, other people, props or reflections in frame.",
        "Identity fidelity is the only pass condition: use the uploaded reference photo as the sole source of facial identity. "
        "No skin smoothing, face slimming, eye enlargement, proportion changes or skin-tone shift. "
        "Plain and accurate beats pretty.",
    ]
    return zh, en, persona, wear, backdrop, mood, spec


def checklist(spec, persona, mood):
    items = [
        f"目标规格 {spec['id']} {spec['name_zh']}：{target_px(spec)} / {spec['dpi']}dpi / {spec['bg_name']}",
        f"头部高度占比 {pct(spec['head_height_ratio'][0])}–{pct(spec['head_height_ratio'][1])}",
        f"瞳孔线位置 底部起 {pct(spec['eye_line_ratio'][0])}–{pct(spec['eye_line_ratio'][1])}",
        f"表情约束：{spec['expression']}",
        f"文件大小上限 {spec['max_kb']}KB，格式 {'/'.join(spec['formats'])}",
        "本机自检：python scripts/check_spec.py 图片 --spec " + spec["id"],
    ]
    if spec["status"] == "needs_verification":
        items.append("⚠ 本规格标记为 needs_verification，正式提交前请比对受理方最新公告")
    if persona.get("pitfalls"):
        items.append("岗位易翻车点：" + persona["pitfalls"])
    if mood.get("compliance_note"):
        items.append("表情合规提示：" + mood["compliance_note"])
    if spec.get("notes_zh"):
        items.append("规格备注：" + spec["notes_zh"])
    return items
