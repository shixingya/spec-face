#!/usr/bin/env python3
"""花名册 → 整批提示词 + 批次一致性体检 + 复核表。

    python scripts/batch_roster.py --template out/roster.csv
    python scripts/batch_roster.py out/roster.csv --spec S-09 --out out/batch
    python scripts/batch_roster.py out/roster.csv --uniform --wear W-03 --backdrop B-01 --mood E-02

这是本项目真正收费的那一层：一个人的提示词是知识，两百个人的提示词是劳动。
脚本做的事和甲方 HR 催你交表时你要做的事一致——认编号、补默认、查冲突、出复核表。

隐私：花名册含员工姓名，输出全部落在 out/ 下（.gitignore 已屏蔽）。本脚本不读也不传任何照片。
"""

import argparse
import collections
import csv
import html
import json
import os
import re
import sys
from argparse import Namespace

import lib
from lib import build_prompt, checklist, pick

ID_RE = re.compile(r"^[PWBES]-\d{2,3}$")

COLUMNS = {
    "name": ["姓名", "名字", "员工姓名", "name"],
    "emp_no": ["工号", "员工编号", "编号", "emp_no"],
    "dept": ["部门", "门店", "组", "dept", "department"],
    "persona": ["岗位", "职位", "职务", "persona", "role"],
    "subject": ["对象描述", "特征", "外貌", "subject", "description"],
    "subject_en": ["对象描述EN", "英文描述", "subject_en", "description_en"],
    "spec": ["规格", "目标规格", "spec"],
    "wear": ["着装", "wear"],
    "backdrop": ["背景", "光型", "backdrop"],
    "mood": ["神态", "表情", "mood"],
    "note": ["备注", "note", "remark"],
}

TEMPLATE = """姓名,工号,部门,岗位,规格,着装,背景,神态,对象描述,对象描述EN,备注
张伟,A001,望京店,P-018,S-09,,,,"32岁男性，方圆脸，短发","32-year-old man, square-round face, short black hair",
李静,A002,望京店,门店店长,S-09,,,,"27岁女性，鹅蛋脸，扎马尾","27-year-old woman, oval face, ponytail",微笑幅度须与张伟一致
王强,A003,国贸店,仓储主管,S-11,,B-01,,"41岁男性，国字脸，寸头，肤色偏深","41-year-old man, square jaw, buzz cut, deeper skin tone",
"""


def resolve(section, table, value):
    """编号直接认；中文岗位名先查名字再查关键词；查不动就报错，绝不猜。"""
    value = (value or "").strip()
    if not value:
        return None, None
    items = lib.load(table)
    if ID_RE.match(value):
        found = {i["id"]: i for i in items}.get(value.upper())
        if found:
            return found["id"], None
        return None, f"{value} 不在{section}编号库里"
    lowered = value.lower()
    for i in items:
        if lowered in (str(i.get("name_zh", "")).lower(), str(i.get("name_en", "")).lower()):
            return i["id"], None
    if table == "personas":
        for i in items:
            if lowered in [str(a).lower() for a in i.get("aliases_zh", [])]:
                return i["id"], None
        hits = []
        for i in items:
            pool = i.get("aliases_zh", []) + i.get("keywords_zh", []) + i.get("keywords_en", [])
            for kw in pool:
                if lowered and (kw.lower() in lowered or lowered in kw.lower()):
                    hits.append(i)
                    break
        if len(hits) == 1:
            return hits[0]["id"], None
        if len(hits) > 1:
            return None, (f"「{value}」命中多个岗位（"
                          + "、".join(f"{h['id']} {h['name_zh']}" for h in hits[:5]) + "），请写编号")
    options = "、".join(f"{i['id']}={i.get('name_zh', i.get('name_en', ''))}" for i in items)
    return None, f"「{value}」认不出属于{section}。可用：{options}"


def read_roster(path):
    with open(path, encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader, [])
        alias = {}
        for idx, col in enumerate(header):
            key = col.strip().lstrip("﻿")
            for field, names in COLUMNS.items():
                if key in names or key.lower() in [n.lower() for n in names]:
                    alias[field] = idx
        rows = []
        for number, raw in enumerate(reader, start=2):
            if not any(cell.strip() for cell in raw):
                continue
            rows.append({field: (raw[idx].strip() if idx < len(raw) else "")
                         for field, idx in alias.items()} | {"_row": number})
    return rows, alias


def apply_uniform(rows, args):
    """批次统一：显式值只能有一个，没显式值就按岗位默认补，并告诉你默认是否真的统一。"""
    batch = {}
    for dim, table in (("wear", "wear"), ("backdrop", "backdrops"), ("mood", "moods")):
        cli = getattr(args, dim)
        explicit = {r.get(dim) for r in rows if r.get(dim)}
        if cli:
            explicit = {cli}
        if len(explicit) > 1:
            errors.append((0, "-", f"{dim} 在批次内出现多个编号（{'、'.join(sorted(explicit))}）；"
                                   f"要么删掉表里的差异值，要么用 --{dim} 指定统一值"))
            batch[dim] = sorted(explicit)[0]
        else:
            batch[dim] = next(iter(explicit), None)
    return batch


def build_rows(rows, args, batch, errors, warns):
    default_notes = {}
    en_missing = []
    out = []
    for row in rows:
        row_no = row["_row"]
        name = row.get("name") or f"第{row_no}行"
        persona_id, err = resolve("岗位", "personas", row.get("persona"))
        if err:
            errors.append((row_no, name, err))
            continue
        if not persona_id:
            errors.append((row_no, name, "缺「岗位」列，无法定位气质编号"))
            continue
        spec_id, err = resolve("规格", "specs", row.get("spec") or args.spec)
        if err:
            errors.append((row_no, name, err))
            continue
        if not spec_id:
            errors.append((row_no, name, "缺「规格」列：批次必须先把合规规格定下来（用 --spec 兜底或表内填写）"))
            continue
        subject = row.get("subject") or ""
        if not subject:
            errors.append((row_no, name, "缺「对象描述」：脸型发型肤色不写，出图只能靠模型想象"))
            continue
        if not row.get("subject_en"):
            en_missing.append(name)

        codes = {}
        for dim, table, label in (("wear", "wear", "着装"), ("backdrop", "backdrops", "背景"),
                                  ("mood", "moods", "神态")):
            value = row.get(dim) or batch.get(dim)
            if args.uniform and row.get(dim) and batch.get(dim) and row[dim] != batch[dim]:
                # 统一批次里留一个异类，比整批不整齐更糟：这一行不出词，等表改对再来
                errors.append((row_no, name, f"--uniform 下 {label}={row[dim]} 与批次统一值 {batch[dim]} 冲突"))
                codes[dim] = None
                continue
            if not value and args.locked:
                errors.append((row_no, name, f"--locked 要求显式给出{label}编号"))
                codes[dim] = None
                continue
            code, err = resolve(label, table, value)
            if err:
                errors.append((row_no, name, err))
                code = None
            if code is None and not err:
                persona = pick("personas", persona_id)
                key = {"wear": "wears", "backdrop": "backdrops", "mood": "moods"}[dim]
                code = persona[key][0]
                default_notes.setdefault((label, persona["name_zh"], code), []).append(name)
            codes[dim] = code
        if any(v is None for v in codes.values()):
            continue

        ns = Namespace(spec=spec_id, persona=persona_id, subject=subject,
                       subject_en=row.get("subject_en"), wear=codes["wear"],
                       backdrop=codes["backdrop"], mood=codes["mood"], locked=args.locked)
        zh, en, persona, wear, backdrop, mood, spec = build_prompt(ns, subject, row.get("subject_en"))
        combo = (spec_id, persona_id, codes["wear"], codes["backdrop"], codes["mood"])
        out.append({
            "row": row_no, "name": name, "emp_no": row.get("emp_no", ""), "dept": row.get("dept", ""),
            "note": row.get("note", ""), "subject": subject, "combo": combo,
            "codes": {"spec": spec_id, "persona": persona_id, **codes},
            "names": {"persona": persona["name_zh"], "wear": wear["name_zh"],
                      "backdrop": backdrop["name_zh"], "mood": mood["name_zh"], "spec": spec["name_zh"]},
            "prompt_zh": "".join(zh), "prompt_en": " ".join(en),
            "checklist": checklist(spec, persona, mood),
            "smile_intensity": mood.get("smile_intensity"),
        })
    by_label = {}
    for (label, pname, code), names in default_notes.items():
        shown = "、".join(names[:4]) + ("…" if len(names) > 4 else "")
        by_label.setdefault(label, []).append(f"{pname}→{code}（{shown}）")
    for label in ("着装", "背景", "神态"):
        if label in by_label:
            warns.append((0, label, "表内未填，按岗位默认补全：" + "；".join(sorted(by_label[label]))))
    if en_missing:
        shown = "、".join(en_missing[:6]) + ("…" if len(en_missing) > 6 else "")
        warns.append((0, "英文描述", f"{len(en_missing)} 人缺「对象描述EN」，English Prompt 里会保留中文"
                                    f"（{shown}）；国内模型无碍，接境外模型或双语交付时会串语"))
    return out


def consistency(person_records, warns):
    """批次体检：同一批人看起来像不像同一家公司的人，是甲方付钱的理由。"""
    report = []
    by_spec = collections.defaultdict(list)
    for r in person_records:
        by_spec[r["codes"]["spec"]].append(r)
    for spec_id, group in sorted(by_spec.items()):
        spec = pick("specs", spec_id)
        dims = spec.get("batch_uniform", [])
        for dim in dims:
            counter = collections.Counter(r["codes"][dim] for r in group)
            if len(counter) > 1:
                detail = "、".join(f"{code}×{n}" for code, n in counter.most_common())
                warns.append((0, f"{spec_id} {spec['name_zh']}",
                              f"{dim} 在 {len(group)} 人批次里出现 {len(counter)} 种（{detail}）："
                              f"该规格要求岗位统一，建议取 {counter.most_common(1)[0][0]} 后重出"))
            report.append({"spec": spec_id, "spec_name": spec["name_zh"], "people": len(group),
                           "dimension": dim, "distinct": len(counter),
                           "distribution": dict(counter)})
        smiles = [r["smile_intensity"] for r in group if r.get("smile_intensity") is not None]
        if len(set(smiles)) > 1:
            warns.append((0, f"{spec_id} 微笑幅度", f"批次内 smile_intensity 跨度 {min(smiles)}–{max(smiles)}，"
                                                  f"同一批工牌上会出现有人笑有人不笑"))
    return report


def sanitize(name):
    return re.sub(r'[\\/:*?"<>|\s]', "_", name)[:40] or "row"


def write_review_html(path, person_records, errors, warns, stats):
    def esc(v):
        return html.escape(str(v))
    rows_html = []
    for r in person_records:
        codes = " × ".join(r["codes"][k] for k in ("spec", "persona", "wear", "backdrop", "mood"))
        rows_html.append(
            "<tr><td>{row}</td><td>{name}</td><td>{dept}</td><td>{codes}</td><td>{combo}</td>"
            "<td class=ok>待出图</td></tr>".format(
                row=r["row"], name=esc(r["name"]), dept=esc(r["dept"] or "-"), codes=esc(codes),
                combo=esc("、".join(r["names"][k] for k in ("persona", "wear", "backdrop", "mood")))))
    warn_html = "".join(f"<li>第 {row} 行 {esc(who)}：{esc(msg)}</li>" for row, who, msg in warns) or "<li>无</li>"
    err_html = "".join(f"<li>第 {row} 行 {esc(who)}：{esc(msg)}</li>" for row, who, msg in errors) or "<li>无</li>"
    doc = f"""<!doctype html><html lang=zh><meta charset=utf-8>
<title>spec-face 批次复核表</title>
<style>
body{{font:14px/1.7 -apple-system,"Microsoft YaHei",sans-serif;margin:32px;color:#1a1a1a}}
h1{{font-size:20px}} h2{{font-size:16px;margin-top:28px;border-left:4px solid #2b6cb0;padding-left:8px}}
table{{border-collapse:collapse;width:100%;font-size:13px}}
th,td{{border:1px solid #d8d8d8;padding:6px 8px;text-align:left}} th{{background:#f5f7fa}}
.ok{{color:#2f855a}} .bad{{color:#c53030}} .muted{{color:#666;font-size:12px}}
code{{background:#f2f2f2;padding:1px 4px;border-radius:3px}}
</style>
<h1>工牌头像批次复核表</h1>
<p class=muted>共 {stats['people']} 人可出图，{stats['errors']} 行待补，{stats['warns']} 条一致性提醒。
规格 {esc('、'.join(stats['specs']))}。表内不含任何照片与证件信息。</p>
<h2>一、名单与编号</h2>
<table><tr><th>行</th><th>姓名</th><th>部门</th><th>五元编号</th><th>含义</th><th>状态</th></tr>
{''.join(rows_html)}
{''.join(f'<tr class=bad><td>{row}</td><td>{esc(who)}</td><td colspan=4>—</td><td>{esc(msg)}</td></tr>' for row, who, msg in errors)}
</table>
<h2>二、一致性提醒（这批看起来像不像是同一家公司的人）</h2>
<ul>{warn_html}</ul>
<h2>三、待补信息</h2>
<ul>{err_html}</ul>
<h2>四、下一步</h2>
<ol>
<li>把 <code>prompts/</code> 里的文本逐条发给生图模型，一人一条，不要中途改词。</li>
<li>每张成图跑 <code>python scripts/check_spec.py 成图.jpg --spec 规格编号</code>。</li>
<li>整批送印：<code>python scripts/print_export.py *.jpg --spec 规格编号 --paper T-02 --cmyk --cut-marks</code>。</li>
</ol>
</body></html>"""
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(doc)


def main(argv=None):
    lib.force_utf8()
    ap = argparse.ArgumentParser(description="花名册批量出词与一致性体检",
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("roster", nargs="?", help="花名册 CSV（Excel 另存为 CSV UTF-8 即可）")
    ap.add_argument("--spec", help="表内未填规格时的兜底规格编号")
    ap.add_argument("--uniform", action="store_true", help="整批锁定着装/背景/神态，表内差异视为错误")
    ap.add_argument("--wear", help="--uniform 时的批次统一着装编号")
    ap.add_argument("--backdrop", help="--uniform 时的批次统一背景编号")
    ap.add_argument("--mood", help="--uniform 时的批次统一神态编号")
    ap.add_argument("--locked", action="store_true", help="盲测模式：输出固定措辞，不接受推荐补全")
    ap.add_argument("--out", default=os.path.join("out", "batch"), help="输出目录")
    ap.add_argument("--template", help="写一份花名册模板到指定路径后退出")
    args = ap.parse_args(argv)

    if args.template:
        os.makedirs(os.path.dirname(os.path.abspath(args.template)), exist_ok=True)
        with open(args.template, "w", encoding="utf-8-sig", newline="") as handle:
            handle.write(TEMPLATE)
        print(f"模板已写入 {args.template}：岗位列可写 P-009，也可直接写「门店店长」这类中文岗位名。")
        return 0
    if not args.roster:
        print("缺少花名册。先看模板：python scripts/batch_roster.py --template out/roster.csv")
        return 2

    rows, alias = read_roster(args.roster)
    missing_cols = [f for f in ("name", "persona") if f not in alias]
    if missing_cols:
        print("花名册缺必要列：" + "、".join(missing_cols) + "。用 --template 生成标准表头。")
        return 1

    errors, warns = [], []
    batch = apply_uniform(rows, args) if args.uniform else {}
    if args.locked:
        for row in rows:
            if not all(row.get(d) or batch.get(d) for d in ("wear", "backdrop", "mood")):
                errors.append((row["_row"], row.get("name", "?"), "--locked 要求表内写全 着装/背景/神态"))
    records = build_rows(rows, args, batch, errors, warns)
    report = consistency(records, warns)

    stamp = collections.Counter(r["codes"]["spec"] for r in records)
    os.makedirs(args.out, exist_ok=True)
    prompts_dir = os.path.join(args.out, "prompts")
    os.makedirs(prompts_dir, exist_ok=True)
    for idx, r in enumerate(records, start=1):
        fname = f"{idx:03d}_{sanitize(r['name'])}_{r['codes']['spec']}.txt"
        r["file"] = os.path.join("prompts", fname)
        body = [
            "=" * 68,
            f"{r['name']}  {r['emp_no']}  {r['dept']}",
            f"组合  {' × '.join(r['codes'][k] for k in ('spec', 'persona', 'wear', 'backdrop', 'mood'))}",
            f"规格  {r['names']['spec']} · 对象 {r['subject']}",
            "=" * 68,
            "【中文提示词】\n" + r["prompt_zh"],
            "【English Prompt】\n" + r["prompt_en"],
            "【交付前自检】",
            "\n".join(f"  [ ] {c}" for c in r["checklist"]),
        ]
        if r["note"]:
            body.insert(4, f"备注  {r['note']}")
        with open(os.path.join(args.out, r["file"]), "w", encoding="utf-8") as handle:
            handle.write("\n\n".join(body) + "\n")

    jsonl_path = os.path.join(args.out, "prompts.jsonl")
    with open(jsonl_path, "w", encoding="utf-8") as handle:
        for r in records:
            handle.write(json.dumps({k: v for k, v in r.items() if k != "checklist"},
                                    ensure_ascii=False) + "\n")

    manifest_path = os.path.join(args.out, "batch_manifest.json")
    manifest = {
        "roster": os.path.abspath(args.roster).replace(os.getcwd(), "."),
        "people_ready": len(records), "rows_skipped": len(errors),
        "specs": dict(stamp), "uniform_batch": batch or None, "locked": args.locked,
        "consistency": report,
        "warnings": [{"row": row, "who": who, "msg": msg} for row, who, msg in warns],
        "errors": [{"row": row, "who": who, "msg": msg} for row, who, msg in errors],
        "people": [{k: v for k, v in r.items() if k not in ("prompt_zh", "prompt_en", "checklist")}
                   for r in records],
        "privacy": "本清单只含姓名与编号，不含照片。out/ 已在 .gitignore 中，不要提交、不要转发到公开群。",
    }
    with open(manifest_path, "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=2)
    write_review_html(os.path.join(args.out, "review.html"), records, errors, warns,
                      {"people": len(records), "errors": len(errors), "warns": len(warns),
                       "specs": sorted(stamp) or ["-"]})

    print(f"花名册 {args.roster}：{len(rows)} 行 → {len(records)} 人可出图，{len(errors)} 行待补")
    for spec_id, count in sorted(stamp.items()):
        print(f"  {spec_id} {pick('specs', spec_id)['name_zh']}：{count} 人")
    if warns:
        print("一致性提醒：")
        for row, who, msg in warns:
            print(f"  ! 第 {row} 行 {who}：{msg}" if row else f"  ! {who}：{msg}")
    if errors:
        print("待补信息（这些行不会出现在 prompts/ 里）：")
        for row, who, msg in errors:
            print(f"  ✗ 第 {row} 行 {who}：{msg}" if row else f"  ✗ {who}：{msg}")
    print(f"\n输出：{args.out}/prompts/*.txt（{len(records)} 条）、prompts.jsonl、review.html、batch_manifest.json")
    print("下一步：逐条出图 → python scripts/check_spec.py 成图.jpg --spec 编号 → print_export.py 排版送印")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
