#!/usr/bin/env python3
"""资产库自检：字段完整性、编号规范、交叉引用、数值合理性。改数据后必跑。

    python scripts/validate_library.py
"""

import json
import os
import re
import sys

import lib

ID_RE = re.compile(r"^[PWBES]-\d{2,3}$")
KNOWN_CHECKS = {
    "px", "px_min", "aspect", "dpi", "max_kb", "format", "bg_color",
    "head_ratio", "eye_line", "safe_circle",
}

REQUIRED = {
    "personas": ["id", "name_zh", "name_en", "industry", "gaze", "posture", "prompt_zh", "prompt_en",
                 "keywords_zh", "keywords_en", "wears", "backdrops", "moods", "pitfalls"],
    "wear": ["id", "name_zh", "name_en", "desc_zh", "desc_en", "prompt_zh", "prompt_en", "suitable_for"],
    "backdrops": ["id", "name_zh", "name_en", "light_zh", "light_en", "prompt_zh", "prompt_en", "use_for"],
    "moods": ["id", "name_zh", "name_en", "desc_zh", "desc_en", "prompt_zh", "prompt_en", "smile_intensity"],
    "specs": ["id", "name_zh", "name_en", "use_for", "px", "dpi", "aspect", "head_height_ratio",
              "eye_line_ratio", "bg_name", "bg_name_en", "max_kb", "formats", "expression", "expression_en",
              "checks", "status"],
}


def err(errors, where, item_id, msg):
    errors.append(f"{where} {item_id}: {msg}")


def validate_sections(errors):
    ids = {}
    for section in ("personas", "wear", "backdrops", "moods", "specs"):
        items = lib.load(section)
        ids[section] = {i["id"] for i in items}
        seen = set()
        for item in items:
            where, iid = section, item.get("id", "<无 id>")
            for field in REQUIRED[section]:
                if field not in item or item[field] in (None, "", [], {}):
                    if field not in item:
                        err(errors, where, iid, f"缺必填字段 {field}")
            if not ID_RE.match(str(iid)):
                err(errors, where, iid, f"编号不符合 前缀-数字 规范")
            if iid in seen:
                err(errors, where, iid, "编号重复")
            seen.add(iid)
            for lang in ("zh", "en"):
                key = f"prompt_{lang}"
                if key in item and len(str(item[key]).strip()) < 12:
                    err(errors, where, iid, f"{key} 过短，不足以驱动生图")

    for p in lib.load("personas"):
        for target, table in (("wears", "wear"), ("backdrops", "backdrops"), ("moods", "moods")):
            for ref in p.get(target, []):
                if ref not in ids[table]:
                    err(errors, "personas", p["id"], f"{target} 引用了不存在的 {ref}")
        if not p.get("wears") or not p.get("backdrops") or not p.get("moods"):
            err(errors, "personas", p["id"], "推荐组合为空，智能推荐模式会失败")

    for w in lib.load("wear"):
        industry_ids = {p["industry"] for p in lib.load("personas")}
        for name in w.get("suitable_for", []):
            if name not in industry_ids:
                err(errors, "wear", w["id"], f"suitable_for 含未知行业「{name}」")


def validate_specs(errors):
    for s in lib.load("specs"):
        where, iid = "specs", s["id"]
        for key in ("head_height_ratio", "eye_line_ratio"):
            lo, hi = s[key]
            if not (0 < lo < hi < 1):
                err(errors, where, iid, f"{key} 需满足 0<下限<上限<1，实际 {s[key]}")
        if len(s["px"]) != 2 or not all(isinstance(v, int) and v > 0 for v in s["px"]):
            err(errors, where, iid, f"px 需为两个正整数，实际 {s['px']}")
        if not isinstance(s["max_kb"], int) or s["max_kb"] < 20:
            err(errors, where, iid, f"max_kb 不合理：{s['max_kb']}")
        for c in s["checks"]:
            if c not in KNOWN_CHECKS:
                err(errors, where, iid, f"checks 含未知项 {c}（check_spec.py 不会执行它）")
        if s["status"] not in ("stable", "needs_verification"):
            err(errors, where, iid, f"status 非法：{s['status']}")
        if s.get("bg_rgb") is not None:
            if len(s["bg_rgb"]) != 3 or not all(0 <= v <= 255 for v in s["bg_rgb"]):
                err(errors, where, iid, f"bg_rgb 需为 3 个 0-255 整数，实际 {s['bg_rgb']}")
            if s.get("bg_tolerance") is None:
                err(errors, where, iid, "给了 bg_rgb 却没给 bg_tolerance，无法做色差校验")
        elif s.get("bg_tolerance") is not None:
            err(errors, where, iid, "给了 bg_tolerance 却没有 bg_rgb")
        num, den = s["aspect"].split(":")
        if abs(float(num) / float(den) - s["px"][0] / s["px"][1]) > 0.05:
            err(errors, where, iid,
                f"aspect {s['aspect']} 与 px {s['px']} 不匹配（差 >5%），出图会被裁歪")


def validate_identity(errors):
    path = os.path.join(lib.REFS, "identity_matrix.json")
    data = json.load(open(path, encoding="utf-8"))
    if data["status"] not in ("untested-scaffold", "partially-tested", "tested"):
        err(errors, "identity", "matrix", f"status 非法：{data['status']}")
    for m in data["models"]:
        iid = m["key"]
        for field in ("label", "tested", "identity_strategy", "identity_fidelity", "beauty_drift",
                      "batch_consistency", "spec_compliance", "notes"):
            if field not in m:
                err(errors, "identity", iid, f"缺字段 {field}")
        if m.get("tested") and any(m.get(k) is None for k in
                                   ("identity_fidelity", "beauty_drift", "batch_consistency")):
            err(errors, "identity", iid, "tested=true 但分数为空，属于虚假声明")
        if m.get("tested") and not (m.get("tested_with_version") and m.get("tested_at")):
            err(errors, "identity", iid, "tested=true 必须写明 tested_with_version 与 tested_at")
    return data


def main():
    lib.force_utf8()
    errors = []
    validate_sections(errors)
    validate_specs(errors)
    matrix = validate_identity(errors)

    counts = {s: len(lib.load(s)) for s in ("personas", "wear", "backdrops", "moods", "specs")}
    tested = sum(1 for m in matrix["models"] if m["tested"])
    print("资产统计  " + "  ".join(f"{k}={v}" for k, v in counts.items()))
    print(f"模型矩阵  共 {len(matrix['models'])} 个，已实测 {tested} 个"
          + ("（v1 全部待测，符合预期）" if tested == 0 else ""))

    if errors:
        print(f"\n发现 {len(errors)} 个问题：")
        for e in errors:
            print("  ✗ " + e)
        return 1
    print("\n✓ 资产库校验通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
