# MANIFEST

版本 `0.1.0` · 2026-09-29 · 首个可用版本。

## 目录与职责

| 路径 | 职责 | 是否手工维护 |
| :-- | :-- | :-- |
| `references/personas.json` | 岗位气质 P-001~020 | ✅ 唯一真源 |
| `references/wear.json` | 着装仪容 W-01~12 | ✅ 唯一真源 |
| `references/backdrops.json` | 背景与光型 B-01~08（含可校验目标色） | ✅ 唯一真源 |
| `references/moods.json` | 神态表情 E-01~08（含微笑幅度） | ✅ 唯一真源 |
| `references/specs.json` | 合规规格 S-01~12 | ✅ 唯一真源 |
| `references/identity_matrix.json` | 模型身份保真评测矩阵（v1 全为待测） | ✅ 唯一真源 |
| `PERSONAS.md` | P/W/B/E 图鉴 | ❌ 由 `build_docs.py` 生成 |
| `SPECS.md` | S 规格图鉴 | ❌ 由 `build_docs.py` 生成 |
| `skills/portrait-prompter/SKILL.md` | Agent Skill 定义：工作流、三种模式、合规红线 | ✅ 手工维护 |
| `skills/portrait-prompter/gallery/index.html` | 离线画廊单页 | ❌ 由 `build_gallery.py` 生成 |
| `scripts/lib.py` | 资产加载与双语提示词组装 | ✅ |
| `scripts/prompt_spec.py` | CLI：五元编号 → 双语提示词 + 自检清单 | ✅ |
| `scripts/check_spec.py` | CLI：本地规格校验，图片不出本机 | ✅ |
| `scripts/validate_library.py` | CLI：资产库完整性与虚假声明检查 | ✅ |
| `scripts/build_gallery.py` | 构建离线画廊 | ✅ |
| `scripts/build_docs.py` | 构建 Markdown 图鉴 | ✅ |
| `images/` | README 配图 | 截图/示例 |

## 改动流程

```bash
python scripts/validate_library.py     # 必须先过
python scripts/build_gallery.py
python scripts/build_docs.py
```

## v1 已知未完成

- `identity_matrix.json` 全部 `tested: false`，尚无真人实测数据
- `check_spec.py` 的头部占比依赖 OpenCV haar 粗估，瞳孔线无法自动判定（标 `SKIP`）
- 多数规格标 `needs_verification`，尚未逐条比对官方最新公告
- 尚无 CMYK 印刷文件导出、尚无圆形安全区预览
