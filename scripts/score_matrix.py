#!/usr/bin/env python3
"""把盲测打分表聚合成 identity_matrix.json 的分数，并且拒绝没有证据的结论。

    python scripts/score_matrix.py research/score-sheet-template.csv --dry-run
    python scripts/score_matrix.py 我的实测.csv --evidence "issue#12" --write

为什么要有这个脚本：矩阵里任何一个数字都可能被拿去当销售话术，所以写入必须过三道门——
样本量达门槛、写清模型版本号与日期、给出可复核的证据。缺一条就只出报告、不落库。
"""

import argparse
import csv
import json
import os
import statistics
import sys
from collections import defaultdict

import lib

REQUIRED_COLS = ["model_key", "model_version", "tested_at", "subject_id"]
NUMERIC = {
    "identity_fidelity": (1, 5),
    "beauty_drift": (0, 3),
    "batch_consistency": (1, 5),
    "judge_1": (0, 1), "judge_2": (0, 1), "judge_3": (0, 1),
    "embedding_cosine": (0, 1),
    "spec_check_pass": (0, 1),
}


def p10(values):
    """第 10 百分位（线性插值）。工牌场景看的是最差那批人像不像。"""
    data = sorted(values)
    if not data:
        return None
    if len(data) == 1:
        return round(data[0], 4)
    pos = (len(data) - 1) * 0.10
    lo = int(pos)
    hi = min(lo + 1, len(data) - 1)
    return round(data[lo] + (data[hi] - data[lo]) * (pos - lo), 4)


def parse_rows(path):
    with open(path, encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        header = reader.fieldnames or []
        missing = [c for c in REQUIRED_COLS if c not in header]
        if missing:
            raise SystemExit(f"打分表缺列：{'、'.join(missing)}。用 research/score-sheet-template.csv 作模板。")
        rows, problems = [], []
        for number, raw in enumerate(reader, start=2):
            if not any((v or "").strip() for v in raw.values()):
                continue
            row = {k: (v or "").strip() for k, v in raw.items() if k}
            for col, (lo, hi) in NUMERIC.items():
                text = row.get(col, "")
                if text == "":
                    row[col] = None
                    continue
                try:
                    value = float(text)
                except ValueError:
                    problems.append(f"第 {number} 行 {col}={text} 不是数字")
                    row[col] = None
                    continue
                if not lo <= value <= hi:
                    problems.append(f"第 {number} 行 {col}={value} 超出 {lo}-{hi} 量程")
                    value = None
                row[col] = value
            for col in REQUIRED_COLS:
                if not row.get(col):
                    problems.append(f"第 {number} 行缺 {col}")
            rows.append(row)
    return rows, problems


def aggregate(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[(row["model_key"], row["model_version"])].append(row)
    results = []
    for (key, version), group in sorted(groups.items()):
        def values(col):
            return [r[col] for r in group if r.get(col) is not None]

        judges = values("judge_1") + values("judge_2") + values("judge_3")
        per_subject_runs = defaultdict(int)
        for r in group:
            per_subject_runs[r["subject_id"]] += 1
        modes = sorted({r["failure_mode"] for r in group if r.get("failure_mode")})
        embedding = values("embedding_cosine")
        results.append({
            "model_key": key,
            "model_version": version or "",
            "tested_at": max((r["tested_at"] for r in group if r.get("tested_at")), default=""),
            "tester": sorted({r["tester"] for r in group if r.get("tester")}),
            "identity_fidelity": round(statistics.median(values("identity_fidelity")), 2)
                                  if values("identity_fidelity") else None,
            "beauty_drift": round(statistics.median(values("beauty_drift")), 2)
                            if values("beauty_drift") else None,
            "batch_consistency": round(statistics.median(values("batch_consistency")), 2)
                                 if values("batch_consistency") else None,
            "blind_same_person_accuracy": round(statistics.mean(judges), 3) if judges else None,
            "embedding_cosine_mean": round(statistics.mean(embedding), 4) if embedding else None,
            "embedding_cosine_p10": p10(embedding),
            "spec_pass_rate": round(statistics.mean(values("spec_check_pass")), 3)
                              if values("spec_check_pass") else None,
            "spec_compliance": ("pass" if statistics.mean(values("spec_check_pass")) >= 0.8 else "fail")
                               if values("spec_check_pass") else None,
            "sample_size": {"subjects": len(per_subject_runs),
                            "runs_per_subject": max(per_subject_runs.values()) if per_subject_runs else 0,
                            "judges": len({c for c in ("judge_1", "judge_2", "judge_3") if values(c)})},
            "rows": len(group),
            "failure_modes": modes,
        })
    return results


def gate(result, args):
    """够不够格写进公开矩阵。门槛就是 protocol 里那几条。"""
    blockers = []
    size = result["sample_size"]
    if size["subjects"] < args.min_subjects:
        blockers.append(f"志愿者 {size['subjects']} 人，protocol 要求 ≥{args.min_subjects} 人")
    if size["runs_per_subject"] < args.min_runs:
        blockers.append(f"每人 {size['runs_per_subject']} 次出图，要求 ≥{args.min_runs} 次")
    if size["judges"] < args.min_judges:
        blockers.append(f"盲测评审 {size['judges']} 人，要求 ≥{args.min_judges} 人")
    if not result["model_version"]:
        blockers.append("缺 model_version，模型一更新分数就失效，必须写清版本")
    if not result["tested_at"]:
        blockers.append("缺 tested_at")
    for field in ("identity_fidelity", "beauty_drift", "batch_consistency"):
        if result[field] is None:
            blockers.append(f"缺 {field} 打分")
    if not args.evidence and not args.allow_internal:
        blockers.append("缺 --evidence（可复核的原始材料位置：PR / issue / 网盘目录链接）")
    return blockers


def write_back(results, args):
    path = os.path.join(lib.REFS, "identity_matrix.json")
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    index = {m["key"]: m for m in data["models"]}
    written, skipped = [], []
    for result in results:
        model = index.get(result["model_key"])
        if model is None:
            skipped.append((result["model_key"], "编号库里没有这个模型，请先在 identity_matrix.json 增行"))
            continue
        blockers = gate(result, args)
        if blockers and not args.allow_partial:
            skipped.append((result["model_key"], "；".join(blockers)))
            continue
        for field in ("identity_fidelity", "beauty_drift", "batch_consistency", "blind_same_person_accuracy",
                      "embedding_cosine_mean", "embedding_cosine_p10", "spec_pass_rate", "spec_compliance",
                      "sample_size", "failure_modes"):
            model[field] = result[field]
        model["tested"] = True
        model["tested_with_version"] = result["model_version"]
        model["tested_at"] = result["tested_at"]
        model["evidence"] = args.evidence or "internal（未公开，仅内部记录）"
        if blockers:
            model["notes"] = "样本未达 protocol 门槛：" + "；".join(blockers) + "。结论仅供内部参考，不得用于对外宣传。"
        else:
            model["notes"] = (f"盲测同认率 {result['blind_same_person_accuracy']}，"
                              f"embedding 相似度 mean {result['embedding_cosine_mean']} / P10 {result['embedding_cosine_p10']}，"
                              f"规格通过率 {result['spec_pass_rate']}，样本 {result['sample_size']['subjects']} 人 "
                              f"×{result['sample_size']['runs_per_subject']} 次。")
        written.append(result["model_key"])
    tested = sum(1 for m in data["models"] if m.get("tested"))
    data["status"] = "tested" if tested == len(data["models"]) else ("partially-tested" if tested else "untested-scaffold")
    data["updated"] = lib.today()
    if not args.dry_run:
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
    return written, skipped


def main(argv=None):
    lib.force_utf8()
    ap = argparse.ArgumentParser(description="盲测打分表 → identity_matrix.json")
    ap.add_argument("sheet", help="打分表 CSV")
    ap.add_argument("--evidence", help="可复核证据位置：PR 链接 / issue 编号 / 素材目录")
    ap.add_argument("--min-subjects", type=int, default=8)
    ap.add_argument("--min-runs", type=int, default=5)
    ap.add_argument("--min-judges", type=int, default=3)
    ap.add_argument("--allow-partial", action="store_true",
                    help="样本不足也写入，但会在 notes 里写明不得用于对外宣传")
    ap.add_argument("--allow-internal", action="store_true", help="不要求 --evidence（仅本地自测时用）")
    ap.add_argument("--write", action="store_true", help="写回 references/identity_matrix.json")
    ap.add_argument("--dry-run", action="store_true", help="只出报告不改库")
    ap.add_argument("--json", dest="as_json", action="store_true")
    args = ap.parse_args(argv)

    rows, problems = parse_rows(args.sheet)
    if problems:
        print("打分表问题：")
        for p in problems[:20]:
            print("  ✗ " + p)
        if len(problems) > 20:
            print(f"  …另有 {len(problems) - 20} 条")
        if not rows:
            return 1
        print("  以上行仍参与统计，但请回表修正。\n")
    if not rows:
        print("打分表是空的。模板见 research/score-sheet-template.csv。")
        return 1

    results = aggregate(rows)
    if args.as_json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return 0

    for result in results:
        size = result["sample_size"]
        print(f"{result['model_key']} @ {result['model_version'] or '未填版本'}  "
              f"{result['rows']} 行 / {size['subjects']} 人 ×{size['runs_per_subject']} 次 / {size['judges']} 评审")
        print(f"  身份保真 {result['identity_fidelity']}  美颜漂移 {result['beauty_drift']}  "
              f"批次一致 {result['batch_consistency']}")
        print(f"  盲测同认率 {result['blind_same_person_accuracy']}  "
              f"embedding mean {result['embedding_cosine_mean']} / P10 {result['embedding_cosine_p10']}")
        print(f"  规格通过率 {result['spec_pass_rate']} → {result['spec_compliance'] or '未测'}"
              + (f"  失败模式：{'、'.join(result['failure_modes'])}" if result['failure_modes'] else ""))
        blockers = gate(result, args)
        for b in blockers:
            print(f"  ✗ 不足以入库：{b}")
        print()

    if not args.write:
        print("未写库。确认无误后加 --write。")
        return 0
    written, skipped = write_back(results, args)
    for key in written:
        print(f"  ✓ 已写入 {key}" + ("（dry-run，未落盘）" if args.dry_run else ""))
    for key, why in skipped:
        print(f"  ✗ 跳过 {key}：{why}")
    print(f"\nidentity_matrix.json {'预演' if args.dry_run else '更新'}完成："
          f"写入 {len(written)} 个模型，跳过 {len(skipped)} 个。")
    print("记得跑 python scripts/validate_library.py 复核，并在 README 的矩阵表格里同步这几个结论。")
    return 0 if written else 1


if __name__ == "__main__":
    raise SystemExit(main())
