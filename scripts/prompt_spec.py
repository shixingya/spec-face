#!/usr/bin/env python3
"""编号 → 中英双语工牌头像提示词。

    python scripts/prompt_spec.py --spec S-09 --persona P-001 --subject "32岁男性，短发，方脸"
    python scripts/prompt_spec.py --spec S-07 --persona P-005 --wear W-08 --backdrop B-05 --mood E-03 \
        --model nano-banana --subject "28岁女性，齐肩发"

缺省 --wear/--backdrop/--mood 时，按岗位推荐组合自动补全并说明理由（智能推荐模式）。
--locked 输出用于盲测的固定措辞，禁止任何个性化描述。
"""

import argparse
import json
import os
import sys

import lib
from lib import build_prompt, checklist, pick


def parse_args(argv):
    p = argparse.ArgumentParser(
        description="spec-face 编号组装器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="编号范围：P 岗位 / W 着装 / B 背景光型 / E 神态 / S 合规规格。查看图鉴见 PERSONAS.md 与 SPECS.md。",
    )
    p.add_argument("--spec", help="合规规格编号，如 S-01 一寸 / S-09 企业工卡（必填）")
    p.add_argument("--persona", help="岗位气质编号，如 P-001 后端工程师（必填）")
    p.add_argument("--subject", help="拍摄对象描述：性别年龄段、脸型、发型、肤色等客观特征（必填）")
    p.add_argument("--subject-en", dest="subject_en", help="拍摄对象的英文描述，缺省沿用中文")
    p.add_argument("--wear", help="着装编号，缺省按岗位推荐")
    p.add_argument("--backdrop", help="背景光型编号，缺省按岗位推荐")
    p.add_argument("--mood", help="神态编号，缺省按岗位推荐")
    p.add_argument("--model", help="目标生图模型 key，见 references/identity_matrix.json")
    p.add_argument("--locked", action="store_true",
                   help="盲测模式：必须显式给全 --wear/--backdrop/--mood，输出固定措辞、不追加推荐")
    p.add_argument("--json", dest="as_json", action="store_true", help="以 JSON 输出，便于程序调用")
    p.add_argument("--list", dest="list_ids", action="store_true", help="列出全部编号后退出")
    return p.parse_args(argv)


def auto_fill(args):
    persona = pick("personas", args.persona)
    missing = [name for name in ("wear", "backdrop", "mood") if not getattr(args, name)]
    if args.locked:
        if missing:
            raise SystemExit("--locked 要求全部编号显式指定，缺：--" + " --".join(missing))
        return []

    reasons = []
    defaults = {"wear": "wears", "backdrop": "backdrops", "mood": "moods"}
    tables = {"wear": "wear", "backdrop": "backdrops", "mood": "moods"}
    for field, key in defaults.items():
        value = getattr(args, field)
        if value:
            continue
        value = persona[key][0]
        item = pick(tables[field], value)
        setattr(args, field, value)
        reasons.append(f"--{field} 缺省，按「{persona['name_zh']}」推荐 {value} {item['name_zh']}")
    return reasons


def identity_note(model_key):
    data = json.load(open(os.path.join(lib.REFS, "identity_matrix.json"), encoding="utf-8"))
    for m in data["models"]:
        if m["key"] != model_key:
            continue
        if m["tested"]:
            return (
                f"模型 {m['label']} 已实测：身份保真 {m['identity_fidelity']}/5，"
                f"美颜漂移 {m['beauty_drift']}/3，批次一致性 {m['batch_consistency']}/5。"
                f"策略：{m['identity_strategy']}"
            )
        return (
            f"模型 {m['label']} 尚未实测（identity_matrix.json: tested=false）。"
            f"建议策略：{m['identity_strategy']}。出图后必须逐张确认像不像本人，不要凭手感放行。"
        )
    keys = ", ".join(m["key"] for m in data["models"])
    return f"未知模型 key：{model_key}。可用：{keys}"


def main(argv=None):
    lib.force_utf8()
    args = parse_args(argv if argv is not None else sys.argv[1:])

    if args.list_ids:
        for section, label in (
            ("personas", "P 岗位气质"),
            ("wear", "W 着装仪容"),
            ("backdrops", "B 背景光型"),
            ("moods", "E 神态表情"),
            ("specs", "S 合规规格"),
        ):
            print(f"\n{label}")
            for item in lib.load(section):
                print(f"  {item['id']}  {item.get('name_zh', '')}  {item.get('name_en', '')}")
        return 0

    missing = [flag for flag, value in (("--spec", args.spec), ("--persona", args.persona),
                                        ("--subject", args.subject)) if not value]
    if missing:
        raise SystemExit("缺少必填参数：" + " ".join(missing) + "\n用 --list 查看全部编号。")

    reasons = auto_fill(args)
    zh, en, persona, wear, backdrop, mood, spec = build_prompt(args, args.subject, args.subject_en)
    notes = [identity_note(args.model)] if args.model else []

    if args.as_json:
        print(json.dumps(
            {
                "spec": spec["id"], "persona": persona["id"], "wear": wear["id"],
                "backdrop": backdrop["id"], "mood": mood["id"], "locked": args.locked,
                "prompt_zh": "".join(zh), "prompt_en": " ".join(en),
                "checklist": checklist(spec, persona, mood), "auto_fill": reasons, "notes": notes,
            },
            ensure_ascii=False, indent=2))
        return 0

    print("=" * 68)
    print(f"组合  {spec['id']} × {persona['id']} × {wear['id']} × {backdrop['id']} × {mood['id']}"
          + ("   [LOCKED 盲测措辞]" if args.locked else ""))
    print(f"规格  {spec['name_zh']} · {spec['px'][0]}×{spec['px'][1]}px · {spec['dpi']}dpi · {spec['bg_name']}")
    print("=" * 68)
    for reason in reasons:
        print(f"· {reason}")
    print("\n【中文提示词】\n" + "".join(zh))
    print("\n【English Prompt】\n" + " ".join(en))
    print("\n【交付前自检清单】")
    for item in checklist(spec, persona, mood):
        print(f"  [ ] {item}")
    for note in notes:
        print(f"\n【身份保真】{note}")
    print("\n出图后跑一次校验：python scripts/check_spec.py 成图.jpg --spec " + spec["id"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
