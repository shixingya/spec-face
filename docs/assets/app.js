/* spec-face 网页试用台
 * 提示词组装逐句对应 scripts/lib.py 的 build_prompt / checklist，
 * 规格校验对应 scripts/check_spec.py。数据只来自 references/（见 scripts/build_site.py）。
 * 本页面不发任何网络请求：图片读自本地，校验算在本地。
 */
(function () {
  "use strict";

  var D = window.SPECFACE;
  if (!D) { document.getElementById("app").textContent = "数据文件 data/library.js 缺失。"; return; }

  var IDX = {};
  ["personas", "wear", "backdrops", "moods", "specs", "papers", "providers"].forEach(function (k) {
    IDX[k] = {};
    D[k].forEach(function (i) { IDX[k][i.id] = i; });
  });

  var $ = function (id) { return document.getElementById(id); };
  var esc = function (s) { return String(s).replace(/[&<>"]/g, function (c) {
    return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); };
  var pct = function (r) { return Math.round(r * 100) + "%"; };
  var targetPx = function (s) { return s.px[0] + "×" + s.px[1] + "px"; };

  /* ---------- 选择器 ---------- */

  function opt(select, value, text) {
    var o = document.createElement("option");
    o.value = value; o.textContent = text;
    select.appendChild(o);
    return o;
  }

  function fillSpecs() {
    var sel = $("spec");
    var groups = {};
    D.specs.forEach(function (s) {
      var g = s.use_for.split(/[、,]/)[0].slice(0, 12) || "其他";
      (groups[g] = groups[g] || []).push(s);
    });
    Object.keys(groups).forEach(function (g) {
      var og = document.createElement("optgroup");
      og.label = g;
      groups[g].forEach(function (s) {
        var o = document.createElement("option");
        o.value = s.id;
        o.textContent = s.id + " " + s.name_zh + " · " + targetPx(s);
        og.appendChild(o);
      });
      sel.appendChild(og);
    });
  }

  function fillPersonas() {
    var sel = $("persona");
    D.personas.forEach(function (p) {
      opt(sel, p.id, p.id + " " + p.name_zh + "（" + p.industry + "）");
    });
  }

  /* 页面字段名 → 数据里的复数表名 */
  var TABLE = { wear: "wear", backdrop: "backdrops", mood: "moods" };
  var PERSONA_KEY = { wear: "wears", backdrop: "backdrops", mood: "moods" };

  function fillCombos() {
    Object.keys(TABLE).forEach(function (k) {
      var sel = $("w-" + k);
      opt(sel, "", "按岗位推荐");
      D[TABLE[k]].forEach(function (i) {
        opt(sel, i.id, i.id + " " + i.name_zh);
      });
    });
  }

  function fillProviders() {
    var sel = $("provider");
    D.providers.forEach(function (p) {
      var need = p.vram_gb ? "≥" + p.vram_gb + "GB" : "无显存要求";
      opt(sel, p.id, p.id + " " + p.name_zh + " · " + need + " · " +
        (p.status === "verified" ? "本机实测通过" : "未在真实 GPU 实测"));
    });
  }

  /* ---------- 缺省补全：对应 prompt_spec.auto_fill ---------- */

  function autoFill(persona, chosen) {
    var out = {}, reasons = [];
    Object.keys(TABLE).forEach(function (field) {
      if (chosen[field]) {
        out[field] = chosen[field];
      } else {
        out[field] = persona[PERSONA_KEY[field]][0];
        reasons.push("· " + field + " 未指定，按「" + persona.name_zh + "」推荐 " +
          out[field] + " " + IDX[TABLE[field]][out[field]].name_zh);
      }
    });
    return { ids: out, reasons: reasons };
  }

  /* ---------- 组装：对应 lib.build_prompt ---------- */

  function buildPrompt(spec, persona, wear, backdrop, mood, subject, subjectEn) {
    var head = spec.head_height_ratio, eye = spec.eye_line_ratio;
    var bgNameEn = spec.bg_name_en || spec.bg_name;
    var exprEn = spec.expression_en || spec.expression;

    var zh = [
      "职业形象照 / 工牌头像。拍摄对象：" + subject + "。",
      "气质定位（" + persona.id + " " + persona.name_zh + "）：" + persona.prompt_zh + "。",
      "着装（" + wear.id + " " + wear.name_zh + "）：" + wear.prompt_zh + "。",
      "背景与光型（" + backdrop.id + " " + backdrop.name_zh + "）：" +
        backdrop.prompt_zh + "；" + backdrop.light_zh + "。",
      "神态（" + mood.id + " " + mood.name_zh + "）：" + mood.prompt_zh + "。",
      "构图与规格（" + spec.id + " " + spec.name_zh + "，" + targetPx(spec) + " / " +
        spec.dpi + "dpi / " + spec.bg_name + "）：" + spec.expression + "；" +
        "头部高度占画面 " + pct(head[0]) + "–" + pct(head[1]) + "；" +
        "瞳孔线位于画面底部起 " + pct(eye[0]) + "–" + pct(eye[1]) + " 之间；" +
        "背景为" + spec.bg_name + "，均匀无色斑与意外阴影。",
      "画面内不得出现文字、标识、其他人物、无关物体与镜面反射。",
      "身份保真是唯一通过条件：以上传的参考照片作为人脸的唯一来源，" +
        "禁止磨皮、瘦脸、放大眼睛、改变五官比例与肤色基调；宁可素净，不可失真。"
    ];

    var en = [
      "Professional headshot for employee badge. Subject: " + (subjectEn || subject) + ".",
      "Persona (" + persona.id + " " + persona.name_en + "): " + persona.prompt_en + ".",
      "Wardrobe (" + wear.id + " " + wear.name_en + "): " + wear.prompt_en + ".",
      "Backdrop and lighting (" + backdrop.id + " " + backdrop.name_en + "): " +
        backdrop.prompt_en + "; " + backdrop.light_en + ".",
      "Expression (" + mood.id + " " + mood.name_en + "): " + mood.prompt_en + ".",
      "Composition and spec (" + spec.id + " " + spec.name_en + ", " + targetPx(spec) +
        " / " + spec.dpi + "dpi / " + bgNameEn + "): " + exprEn + "; " +
        "head height " + pct(head[0]) + "-" + pct(head[1]) + " of frame; " +
        "eye line " + pct(eye[0]) + "-" + pct(eye[1]) + " measured from the bottom edge; " +
        "backdrop even and free of patches or accidental shadow.",
      "No text, logos, other people, props or reflections in frame.",
      "Identity fidelity is the only pass condition: use the uploaded reference photo as the " +
        "sole source of facial identity. No skin smoothing, face slimming, eye enlargement, " +
        "proportion changes or skin-tone shift. Plain and accurate beats pretty."
    ];
    return { zh: zh.join(""), en: en.join(" ") };
  }

  /* ---------- 自检清单：对应 lib.checklist ---------- */

  function checklist(spec, persona, mood) {
    var items = [
      { t: "目标规格 " + spec.id + " " + spec.name_zh + "：" + targetPx(spec) + " / " +
        spec.dpi + "dpi / " + spec.bg_name },
      { t: "头部高度占比 " + pct(spec.head_height_ratio[0]) + "–" + pct(spec.head_height_ratio[1]) },
      { t: "瞳孔线位置 底部起 " + pct(spec.eye_line_ratio[0]) + "–" + pct(spec.eye_line_ratio[1]) },
      { t: "表情约束：" + spec.expression },
      { t: "文件大小上限 " + spec.max_kb + "KB，格式 " + spec.formats.join("/") },
      { t: "本机自检：python scripts/check_spec.py 图片 --spec " + spec.id }
    ];
    if (spec.status === "needs_verification") {
      items.push({ t: "⚠ 本规格标记为 needs_verification，正式提交前请比对受理方最新公告", warn: true });
    }
    if (persona.pitfalls) items.push({ t: "岗位易翻车点：" + persona.pitfalls });
    if (mood.compliance_note) items.push({ t: "表情合规提示：" + mood.compliance_note });
    if (spec.notes_zh) items.push({ t: "规格备注：" + spec.notes_zh });
    return items;
  }

  /* ---------- 当前选择 ---------- */

  function current() {
    var spec = IDX.specs[$("spec").value];
    var persona = IDX.personas[$("persona").value];
    var filled = autoFill(persona, {
      wear: $("w-wear").value, backdrop: $("w-backdrop").value, mood: $("w-mood").value
    });
    return {
      spec: spec,
      persona: persona,
      wear: IDX.wear[filled.ids.wear],
      backdrop: IDX.backdrops[filled.ids.backdrop],
      mood: IDX.moods[filled.ids.mood],
      reasons: filled.reasons,
      subject: $("subject").value.trim(),
      subjectEn: $("subject-en").value.trim()
    };
  }

  function specFacts() {
    var s = IDX.specs[$("spec").value];
    var rows = [
      ["尺寸", targetPx(s) + " · " + s.aspect + " · " + s.dpi + "dpi"],
      ["头部占比", pct(s.head_height_ratio[0]) + "–" + pct(s.head_height_ratio[1])],
      ["瞳孔线", "底部起 " + pct(s.eye_line_ratio[0]) + "–" + pct(s.eye_line_ratio[1])],
      ["底色", s.bg_rgb ? "rgb(" + s.bg_rgb.join(", ") + ")±" + (s.bg_tolerance || 12) : s.bg_name],
      ["体积上限", s.max_kb + "KB · " + s.formats.join("/")],
      ["用途", s.use_for]
    ];
    $("facts").innerHTML = rows.map(function (r) {
      return "<div><b>" + esc(r[0]) + "</b>" + esc(r[1]) + "</div>";
    }).join("");
    $("spec-flag").hidden = s.status !== "needs_verification";
    $("spec-name").textContent = s.id + " " + s.name_zh;
  }

  function render() {
    specFacts();
    var c = current();
    var box = $("prompt-out");
    if (!c.subject) {
      box.innerHTML = '<p class="why" style="margin-left:0">填写拍摄对象的客观描述后出词。' +
        "只写外貌：性别年龄段、脸型、发型、肤色、胖瘦——不写气质形容词，那些由编号负责。</p>";
      $("cmd").textContent = "";
      return;
    }
    var p = buildPrompt(c.spec, c.persona, c.wear, c.backdrop, c.mood, c.subject, c.subjectEn);
    var list = checklist(c.spec, c.persona, c.mood);
    box.innerHTML =
      '<div class="blk"><h3>组合</h3><div class="combo">' +
      [c.spec.id, c.persona.id, c.wear.id, c.backdrop.id, c.mood.id].join(" × ") + "</div>" +
      (c.reasons.length ? '<p class="why" style="margin:8px 0 0">' +
        c.reasons.map(esc).join("<br>") + "</p>" : "") + "</div>" +
      block("中文提示词", "zh", p.zh) +
      block("English Prompt", "en", p.en) +
      '<div class="blk"><h3>交付前自检清单</h3><ul class="list">' +
      list.map(function (i) { return '<li class="' + (i.warn ? "warn" : "") + '">' + esc(i.t) + "</li>"; }).join("") +
      "</ul></div>";
    bindCopy();
    buildCommand(c);
  }

  function block(label, id, text) {
    return '<div class="blk"><h3><span>' + esc(label) + '</span>' +
      '<button class="copy" data-copy="' + id + '">复制</button></h3>' +
      '<textarea id="' + id + '" readonly>' + esc(text) + "</textarea></div>";
  }

  function bindCopy() {
    Array.prototype.forEach.call(document.querySelectorAll(".copy"), function (btn) {
      btn.onclick = function () {
        var el = $(btn.getAttribute("data-copy"));
        if (!el) return;
        el.select();
        try { document.execCommand("copy"); } catch (e) { /* 老浏览器 */ }
        btn.textContent = "已复制";
        setTimeout(function () { btn.textContent = "复制"; }, 1200);
      };
    });
  }

  /* ---------- 本机出图命令：对应 gen_portrait.py 的参数面 ---------- */

  function buildCommand(c) {
    var pid = $("provider").value;
    var p = IDX.providers[pid];
    var parts = ["python scripts/gen_portrait.py",
      "  --photo 我的照片.jpg",
      "  --spec " + c.spec.id + " --persona " + c.persona.id,
      "  --subject \"" + c.subject + "\""];
    if (c.subjectEn) parts.push("  --subject-en \"" + c.subjectEn + "\"");
    parts.push("  --wear " + c.wear.id + " --backdrop " + c.backdrop.id + " --mood " + c.mood.id);
    parts.push("  --provider " + p.id + " --n 3 --seed 20260929");
    parts.push("  --confirm-authorized 本人");
    if (p.kind === "http-comfyui") parts.push("  --workflow 我的工作流.json");
    if (p.kind === "http-webui") parts.push("  --payload-extra 我的扩展参数.json");
    $("cmd").textContent = parts.join(" \\\n");
    $("g-note").innerHTML = esc(p.notes_zh || "") +
      (p.status === "verified" ? "" : ' <span class="tag warn">未在真实 GPU 实测</span>');
    $("g-need").innerHTML = (p.requires || []).map(function (r) { return "<li>" + esc(r) + "</li>"; }).join("");
  }

  /* ---------- 浏览器本地校验：对应 check_spec.py 的可客观判定项 ---------- */

  function median(seq) {
    seq.sort(function (a, b) { return a - b; });
    var mid = Math.floor(seq.length / 2);
    return seq.length % 2 ? seq[mid] : Math.round((seq[mid - 1] + seq[mid]) / 2);
  }

  function borderColor(img) {
    var w = img.naturalWidth, h = img.naturalHeight;
    var scale = Math.min(1, 1200 / Math.max(w, h));
    var cw = Math.max(1, Math.round(w * scale)), ch = Math.max(1, Math.round(h * scale));
    var cv = document.createElement("canvas");
    cv.width = cw; cv.height = ch;
    var ctx = cv.getContext("2d", { willReadFrequently: true });
    ctx.drawImage(img, 0, 0, cw, ch);
    var d = ctx.getImageData(0, 0, cw, ch).data;
    var step = Math.max(1, Math.floor((cw * ch) / 400));
    var px = function (x, y) {
      var i = (y * cw + x) * 4;
      return [d[i], d[i + 1], d[i + 2]];
    };
    var samples = [];
    for (var x = 0; x < cw; x += step) {
      samples.push(px(x, 0));
      samples.push(px(x, Math.min(ch - 1, Math.floor(ch * 0.04))));
    }
    for (var y = 0; y < Math.floor(ch * 0.35); y += Math.max(1, Math.floor(step / 2))) {
      samples.push(px(0, y));
      samples.push(px(cw - 1, y));
    }
    return [
      median(samples.map(function (s) { return s[0]; })),
      median(samples.map(function (s) { return s[1]; })),
      median(samples.map(function (s) { return s[2]; }))
    ];
  }

  function checkImage(img, fileName, bytes, spec) {
    var rows = [];
    var add = function (name, ok, detail, cls) { rows.push({ name: name, ok: ok, detail: detail, cls: cls }); };

    var kb = Math.round(bytes / 1024 * 10) / 10;
    var ext = (fileName.split(".").pop() || "").toLowerCase();
    add("format", spec.formats.indexOf(ext) >= 0, "实际 ." + ext + "，允许 " + spec.formats.join("/"));
    add("max_kb", kb <= spec.max_kb, "实际 " + kb + "KB，上限 " + spec.max_kb + "KB");

    var w = img.naturalWidth, h = img.naturalHeight;
    if (spec.px_rule) {
      add("px", w >= spec.px[0] && h >= spec.px[1],
        "实际 " + w + "×" + h + "，要求不低于 " + spec.px[0] + "×" + spec.px[1]);
    } else {
      add("px", Math.abs(w - spec.px[0]) / spec.px[0] <= 0.02 && Math.abs(h - spec.px[1]) / spec.px[1] <= 0.02,
        "实际 " + w + "×" + h + "，目标 " + spec.px[0] + "×" + spec.px[1] + "（±2%）");
    }

    var ab = spec.aspect.split(":");
    var actual = Math.round(w / h * 1000) / 1000, want = Math.round(ab[0] / ab[1] * 1000) / 1000;
    add("aspect", Math.abs(actual - want) <= 0.02, "实际 1:" + actual + "，目标 1:" + want);

    add("dpi", null, "浏览器读不到 DPI 元数据；印刷用途请由本机 print_export.py 写入，而非只改像素数", "skip");

    if (spec.bg_rgb) {
      var rgb = borderColor(img), target = spec.bg_rgb, tol = spec.bg_tolerance || 12;
      var worst = Math.max(Math.abs(rgb[0] - target[0]), Math.abs(rgb[1] - target[1]), Math.abs(rgb[2] - target[2]));
      add("bg_color", worst <= tol, "背景取样中位色 rgb(" + rgb.join(", ") + ")（顶边+侧边上部），目标 rgb(" +
        target.join(", ") + ")±" + tol + "，最大偏差 " + worst);
    } else {
      add("bg_color", null, "本规格不限定底色（" + spec.bg_name + "）", "skip");
    }

    add("head_ratio", null, "本页不做人脸检测（刻意不引入第三方模型）；头部占比 " +
      pct(spec.head_height_ratio[0]) + "–" + pct(spec.head_height_ratio[1]) + " 需目视，或用本机 check_spec.py", "skip");
    add("eye_line", null, "同上", "skip");
    return rows;
  }

  function paint(rows) {
    var mark = function (r) {
      if (r.cls === "skip") return { c: "p-skip", t: "−" };
      return r.ok ? { c: "p-ok", t: "✓" } : { c: "p-bad", t: "✗" };
    };
    $("check-body").innerHTML = rows.map(function (r) {
      var m = mark(r);
      return '<tr class="' + (r.cls || "") + '"><td class="mark ' + m.c + '">' + m.t + "</td><td>" +
        esc(r.name) + "</td><td>" + esc(r.detail) + "</td></tr>";
    }).join("");
    var bad = rows.filter(function (r) { return r.cls !== "skip" && !r.ok; }).length;
    var skip = rows.filter(function (r) { return r.cls === "skip"; }).length;
    var sum = $("check-sum");
    sum.className = "summary " + (bad ? "bad" : "good");
    sum.innerHTML = bad
      ? "✗ " + bad + " 项不通过" + (skip ? "，" + skip + " 项本机未测" : "") +
        "——按规格重出图或用 print_export.py 归位像素后再交付。"
      : "✓ 可测项全部通过" + (skip ? "；另有 " + skip + " 项在浏览器里测不了，标 − 不算通过，请用本机脚本复核。" : "。");
  }

  function onFile(file) {
    if (!file || !/^image\//.test(file.type)) { return; }
    $("file-name").textContent = file.name + " · " + Math.round(file.size / 1024) + "KB";
    var url = URL.createObjectURL(file);
    var img = new Image();
    img.onload = function () {
      $("check-preview").innerHTML = "";
      img.style.cssText = "max-height:220px;border-radius:8px;border:1px solid #e5e7eb";
      $("check-preview").appendChild(img);
      paint(checkImage(img, file.name, file.size, IDX.specs[$("spec").value]));
      $("check-card").hidden = false;
      URL.revokeObjectURL(url);
    };
    img.onerror = function () { $("check-sum").textContent = "这张图浏览器读不出来，可能已损坏。"; };
    img.src = url;
  }

  /* ---------- 启动 ---------- */

  function boot() {
    fillSpecs(); fillPersonas(); fillCombos(); fillProviders();
    $("spec").value = "S-09";
    $("persona").value = "P-001";
    $("v-count").textContent =
      D.personas.length + " 岗位 · " + D.wear.length + " 着装 · " + D.backdrops.length + " 背景光型 · " +
      D.moods.length + " 神态 · " + D.specs.length + " 规格 · " + D.papers.length + " 打印载体 · " +
      D.providers.length + " 生成后端";
    $("v-tag").textContent = "v" + D.version.version;

    ["spec", "persona", "w-wear", "w-backdrop", "w-mood", "provider"].forEach(function (id) {
      $(id).addEventListener("change", render);
    });
    ["subject", "subject-en"].forEach(function (id) {
      $(id).addEventListener("input", render);
    });
    $("reset").onclick = function () {
      $("w-wear").value = $("w-backdrop").value = $("w-mood").value = "";
      $("subject").value = ""; $("subject-en").value = "";
      render();
    };
    $("file").addEventListener("change", function (e) { onFile(e.target.files[0]); });
    var dz = $("drop");
    ["dragenter", "dragover"].forEach(function (ev) {
      dz.addEventListener(ev, function (e) { e.preventDefault(); dz.classList.add("on"); });
    });
    ["dragleave", "drop"].forEach(function (ev) {
      dz.addEventListener(ev, function (e) { e.preventDefault(); dz.classList.remove("on"); });
    });
    dz.addEventListener("drop", function (e) { onFile(e.dataTransfer.files[0]); });

    render();
  }

  boot();
})();
