# MANIFEST

版本 `0.2.0` · 2026-09-29 · 新增批量与印刷交付层（`T` 载体编号库 + 四个交付脚本 + 盲测套件）。

## 目录与职责

| 路径 | 职责 | 是否手工维护 |
| :-- | :-- | :-- |
| `references/personas.json` | 岗位气质 P-001~020，含 `aliases_zh` HR 岗位名映射 | ✅ 唯一真源 |
| `references/wear.json` | 着装仪容 W-01~12 | ✅ 唯一真源 |
| `references/backdrops.json` | 背景与光型 B-01~08（含可校验目标色） | ✅ 唯一真源 |
| `references/moods.json` | 神态表情 E-01~08（含微笑幅度） | ✅ 唯一真源 |
| `references/specs.json` | 合规规格 S-01~12（含 `batch_uniform` 批次统一维度） | ✅ 唯一真源 |
| `references/papers.json` | 打印载体 T-01~06（相纸 / A4 / CR80 卡面） | ✅ 唯一真源 |
| `references/identity_matrix.json` | 模型身份保真评测矩阵（含 `evidence` 与 `sample_size` 门槛） | ✅ 唯一真源 |
| `PERSONAS.md` | P/W/B/E 图鉴 | ❌ 由 `build_docs.py` 生成 |
| `SPECS.md` | S 规格图鉴 + T 载体实算可排张数 | ❌ 由 `build_docs.py` 生成 |
| `COMMERCIAL.md` | 价目、交付口径、需求表、拒绝清单 | ✅ 手工维护 |
| `skills/portrait-prompter/SKILL.md` | Agent Skill 定义：工作流、四种模式、合规红线 | ✅ 手工维护 |
| `skills/portrait-prompter/gallery/index.html` | 离线画廊单页（含打印载体标签页） | ❌ 由 `build_gallery.py` 生成 |
| `scripts/lib.py` | 资产加载、双语提示词组装、排版实算（`print_fit`） | ✅ |
| `scripts/prompt_spec.py` | CLI：五元编号 → 双语提示词 + 自检清单 | ✅ |
| `scripts/batch_roster.py` | CLI：花名册 → 整批提示词 + 一致性体检 + 复核表 | ✅ |
| `scripts/check_spec.py` | CLI：本地规格校验，图片不出本机 | ✅ |
| `scripts/guide_overlay.py` | CLI：瞳孔线带 / 头部框 / 圆形安全区可视化 | ✅ |
| `scripts/print_export.py` | CLI：mm×dpi 反算、多联排版、出血、CMYK、裁切线 | ✅ |
| `scripts/score_matrix.py` | CLI：盲测打分表 → 矩阵入库（无证据则拒写） | ✅ |
| `scripts/validate_library.py` | CLI：资产库完整性、交叉引用、虚假声明检查 | ✅ |
| `scripts/build_gallery.py` | 构建离线画廊 | ✅ |
| `scripts/build_docs.py` | 构建 Markdown 图鉴 | ✅ |
| `research/README.md` | 身份保真盲测协议：门槛、七步流程、列定义、作弊清单 | ✅ |
| `research/consent-form.md` | 肖像授权书模板（含撤回权与删除期限） | ✅ |
| `research/score-sheet-template.csv` | 打分表模板 | ✅ |
| `research/data/` | 志愿者素材目录（**已 gitignore，永不提交**） | — |
| `images/` | README 配图：画廊截图 + `sample-headshot.jpg`（本项目提示词生成的 AI 示例人像，含生成标识，非真人）+ `guide-preview.png` | 示例，非真人素材 |
| `out/` | 所有生成物：提示词、排版稿、复核表（**已 gitignore**） | — |

## 改动流程

```bash
python scripts/validate_library.py     # 必须先过
python scripts/build_gallery.py
python scripts/build_docs.py
```

排版可排张数在 `SPECS.md`、离线画廊、`print_export.py` 三处共用 `lib.print_fit()`，
所以不会出现"文档写 12 张、脚本算出 8 张"这种打脸。

## 已知未完成

- `identity_matrix.json` 全部 `tested: false`——协议、授权书、聚合脚本都齐了，缺的就是真人实测那一步
- `check_spec.py` 的头部占比依赖 OpenCV haar 粗估，瞳孔线无法自动判定（标 `SKIP`）；`guide_overlay.py` 只画容差带，不做检测
- 多数规格标 `needs_verification`，尚未逐条比对官方最新公告
- `print_export.py` 的 CMYK 是无 ICC 的近似换算，能避免 RGB 直印偏色，但专色/VI 硬要求仍需印厂数码打样
- 卡面（T-06）只输出头像窗，不做卡面版式设计
- 花名册的 `对象描述` 仍需人工填写，未接入任何人脸属性识别（刻意不做：那会把敏感信息处理引入本地工具链）
