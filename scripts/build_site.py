#!/usr/bin/env python3
"""把 references/ 的资产打包成网页可直接读的数据文件，并同步离线画廊。

    python scripts/build_site.py

docs/ 是 GitHub Pages 站点。它只跑静态文件，所以编号库必须在构建期注入：
网页里的提示词组装逻辑与 lib.build_prompt 逐句对应，数据也只从 references/ 生成，
避免"网页写的和脚本算的不一样"。
"""

import json
import os
import shutil

import lib

DOCS = os.path.join(lib.ROOT, "docs")
GALLERY_SRC = os.path.join(lib.ROOT, "skills", "portrait-prompter", "gallery", "index.html")


def provider_meta():
    path = os.path.join(lib.REFS, lib.FILES["providers"])
    with open(path, encoding="utf-8") as handle:
        raw = json.load(handle)
    return {"keywords": raw["identity_keywords"], "note": raw.get("note", ""),
            "conventions": raw.get("conventions", {})}


def main():
    lib.force_utf8()
    os.makedirs(os.path.join(DOCS, "data"), exist_ok=True)
    payload = {
        "version": json.load(open(os.path.join(lib.ROOT, "version.json"), encoding="utf-8")),
        "built": lib.today(),
        "personas": lib.load("personas"),
        "wear": lib.load("wear"),
        "backdrops": lib.load("backdrops"),
        "moods": lib.load("moods"),
        "specs": lib.load("specs"),
        "papers": lib.load("papers"),
        "providers": lib.load("providers"),
        "providerMeta": provider_meta(),
    }
    out = os.path.join(DOCS, "data", "library.js")
    with open(out, "w", encoding="utf-8") as handle:
        handle.write("/* 由 scripts/build_site.py 从 references/*.json 生成，请勿手改 */\n")
        handle.write("window.SPECFACE = ")
        json.dump(payload, handle, ensure_ascii=False, separators=(",", ":"))
        handle.write(";\n")

    if os.path.exists(GALLERY_SRC):
        shutil.copyfile(GALLERY_SRC, os.path.join(DOCS, "gallery.html"))
        print(f"已同步画廊 docs/gallery.html")

    kb = os.path.getsize(out) / 1024
    print(f"已生成 docs/data/library.js（{kb:.0f}KB，"
          + "  ".join(f"{k}={len(payload[k])}" for k in
                      ("personas", "wear", "backdrops", "moods", "specs", "papers", "providers")) + "）")
    print("下一步：python -m http.server -d docs 8000 本地预览；"
          "确认后按 MANIFEST.md「试用站发布」把 docs/ 全量同步到 gh-pages 分支，Pages 读的是那个分支而不是 main")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
