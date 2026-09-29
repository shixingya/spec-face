---
name: spec-face-portrait-prompter
description: 把「给我做张工牌头像」变成可交付的成图，一个人或两百人都一样。按岗位 P / 着装 W / 背景光型 B / 神态 E / 合规规格 S 五元编号组装中英双语生图提示词，读 HR 花名册整批出词并做批次一致性体检，用 check_spec.py 本地校验尺寸、底色、头部占比、DPI、文件大小，用 print_export.py 导出相纸多联排版与 CMYK 印刷稿。适用于企业工卡、门禁、考勤、企业 IM 头像、证件照构图参考、连锁门店批量头像交付。
---

# spec-face · 工牌头像提示词与规格 Skill

> 一句话：证件照和工牌不是"好看就行"，**过不了规格就是废图**。本 Skill 负责把抽象需求落成编号，把编号落成双语提示词，再把成图拉回规格做客观校验。

## 何时启用本 Skill

用户说到以下任何一类，都应启用：

- 工牌 / 工卡 / 门禁卡 / 员工卡 / 上岗证 头像、批量做员工照片
- 入职照、企业微信/飞书/钉钉头像统一、LinkedIn 或脉脉头像
- 证件照构图、一寸 / 二寸 / 小二寸 / 签证照 尺寸与底色要求
- "帮我写个 AI 生成职业照的提示词"、"我们的 AI 头像磨皮太重，不像本人"
- 连锁门店、物业、物流、诊所等**高流动率行业**的批量头像生产

## 数据在哪

| 文件 | 内容 |
| :-- | :-- |
| `references/personas.json` | 岗位气质 P-001~，含眼神、姿态、关键词、双语提示片段、易翻车点、推荐组合 |
| `references/wear.json` | 着装仪容 W-01~ |
| `references/backdrops.json` | 背景与光型 B-01~，含可校验目标色 `bg_rgb` 与容差 |
| `references/moods.json` | 神态 E-01~，含微笑幅度 `smile_intensity`（批量一致性用） |
| `references/specs.json` | **合规规格 S-01~**，尺寸/DPI/头部占比/瞳孔线/底色/体积/校验项/批次统一维度 |
| `references/papers.json` | 打印载体 T-01~，相纸/A4/CR80 卡面的尺寸、出血、间距、留白 |
| `references/identity_matrix.json` | 各生图模型在"像不像本人"上的实测矩阵 |
| `PERSONAS.md` / `SPECS.md` | 由 JSON 生成的图鉴，可直接 grep 选号 |
| `skills/portrait-prompter/gallery/index.html` | 离线单页画廊，双击可开、全文检索、一键复制 |
| `research/README.md` | 身份保真盲测协议（样本门槛、流程、作弊清单） |
| `research/consent-form.md` | 肖像授权书模板——**要处理别人的脸，先从这份文件开始** |

## 工作流

### 第 1 步：确定合规规格 S（必须最先定）

**先问用途，再谈审美。** 用途决定规格，规格决定构图，构图决定提示词。顺序颠倒就会返工。

向用户确认：这张图用在哪里？

| 用途 | 规格 |
| :-- | :-- |
| 简历 / 通用 | `S-01` 一寸 · `S-02` 二寸 |
| 驾驶证类 | `S-03` 小一寸 |
| 证书 / 护照类 | `S-04` 小二寸 · `S-05` 中国护照 |
| 欧美日签证 | `S-06` 美签 2×2 · `S-07` 申根 · `S-08` 日本 |
| **企业工卡印刷** | `S-09` CR80 头像区（记得转 CMYK + 3mm 出血） |
| 门禁 / 考勤人脸底库 | `S-10` |
| 飞书 / 企微 / 钉钉头像 | `S-11`（圆形裁切，关键内容锁在中心 70% 安全区） |
| LinkedIn / 脉脉 / 官网团队页 | `S-12` |

规格 `status` 为 `needs_verification` 的，**必须提醒用户**比对受理方（使领馆、出入境、交管、平台）最新公告，不得代替官方口径。

### 第 2 步：确定岗位气质 P

按用户的岗位/行业选号。不确定时读 `PERSONAS.md` 第一节表格，或跑：

```bash
python scripts/prompt_spec.py --list
```

### 第 3 步：组装

```bash
python scripts/prompt_spec.py \
  --spec S-09 --persona P-001 \
  --subject "30岁男性，方脸，短寸发，自然肤色，偏瘦" \
  --subject-en "30-year-old man, square face, buzz cut, natural skin tone, slim" \
  --model gpt-image
```

`--wear/--backdrop/--mood` 可省略，脚本会按该岗位的推荐组合自动补全并说明理由。用户明确指定编号时照用，不要自作主张替换。

### 第 4 步：交付成图后，本地校验

```bash
pip install pillow                 # 必需
pip install opencv-python          # 可选，自动估算头部占比
python scripts/check_spec.py 成图.jpg --spec S-09
python scripts/check_spec.py batch/*.jpg --spec S-11 --json   # 批量
```

**校验结果如实转述给用户。** `SKIP` 就是 SKIP，绝不能说成"通过"。缺依赖、检测不到人脸、规格需目视——都要讲清楚。

看不明白"差在哪"时，把辅助线画到图上再发给用户：

```bash
python scripts/guide_overlay.py 成图.jpg --spec S-11
```

### 第 5 步（批量任务）：读花名册，整批出词

人数 ≥ 10 或用户递来 Excel 时，不要逐条手写提示词，走 `batch_roster.py`：

```bash
python scripts/batch_roster.py --template out/roster.csv      # 先给人家模板
python scripts/batch_roster.py 花名册.csv --out out/batch      # 认编号、补默认、出复核表
python scripts/batch_roster.py 花名册.csv --uniform \
  --wear W-09 --backdrop B-01 --mood E-02                      # 整批锁风格
```

岗位列写 `P-018` 或 HR 嘴里的「仓储主管」「置业顾问」都能认（`aliases_zh`）；认不准时报错列候选，**不要替用户猜岗位**。
脚本会主动报告批次散掉的地方：同一 `S-09` 里出现两种 `mood`、微笑幅度跨度大、着装不统一——这些正是甲方验收时挑刺的点。
`review.html` 是给人力看的，`prompts.jsonl` 是给程序用的，两个都要交付。

### 第 6 步（要印刷）：导出交付件

```bash
python scripts/print_export.py --list-papers
python scripts/print_export.py 成图/*.jpg --spec S-01 --paper T-02 --cut-marks --out out/print
python scripts/print_export.py 成图/*.jpg --spec S-09 --paper T-06 --cmyk
```

送件口径必须说清：**冲印店收 `.jpg`（RGB）；印刷厂/卡厂收 `_cmyk.tif`；自助照片机收 `.jpg` 且不要出血。**
可排张数由 `lib.print_fit()` 实算，别凭"6 寸一般排 8 张"的手感答复客户。
证件照默认不旋转排版——横过来的人像冲出来是躺着的。

## 四种使用模式

**① 零门槛推荐**：用户只说"我是做销售的，给我们店員做头像"。→ 选 `P-008` 或 `P-009`，用默认规格 `S-09`，直接给提示词并说明推荐理由。

**② 精准指定**：用户给出编号（如 `S-07 P-005 W-08 B-01 E-01`）→ 原样组装，不改号，不换风格。用户只给部分编号时补全并说明。

**③ 批量锁定（B 端主战场）**：一批人用同一组编号出图。必须加 `--locked` 并把五元编号全部显式写出来，禁止逐次改词：

```bash
python scripts/prompt_spec.py --locked \
  --spec S-09 --persona P-018 --wear W-09 --backdrop B-01 --mood E-02 \
  --subject "员工姓名或编号 + 客观外貌描述"
```

批量场景两条铁律：
- **避开 `B-07` 办公室虚化**，环境光无法统一，整批一眼就看出不齐
- 需要品牌背景用 `B-08`，先向客户索取 VI 的 RGB 值再出图

**④ 整批交付（收费的那一层）**：用户给的是 Excel 而不是描述。→ 走第 5、6 步，交付 `prompts/` + `review.html` + 排版稿，并主动报告一致性风险与需要补填的行。一个人的提示词是知识，两百个人的提示词是劳动，劳动才收费。

## 身份保真：本 Skill 的第一红线

工牌头像和普通写真的根本差别：**像不像本人是唯一通过条件，好看是次要条件。**

- 必须以上传的真实照片作为人脸唯一来源；模型若不支持身份保持，宁可只做背景与着装重绘
- 禁止磨皮、瘦脸、放大眼睛、改五官比例、整体提亮肤色
- 出图前读 `identity_matrix.json`：`tested: false` 的模型**必须明确告知用户"该模型身份保真度未经实测"**，不得凭手感放行
- 建议同批出 3 张候选，由本人或直属主管确认，而不是由生成者单方面定稿

## 安全与合规红线（不可协商）

1. **只处理本人或已获书面授权的对象的图像。** 用户上传他人照片、名人照片、或要求"换成某个人的脸"用于证件、工牌、门禁时，**拒绝生成**，并说明：未经授权的换脸可能构成侵权，用于身份认证场景可能触犯法律。
2. **不用于绕过身份核验。** 明确拒绝"用 AI 照片过人脸门禁/活体检测/实名认证"的请求，这类用途一律不做，并提供正当替代（现场采集、官方渠道补办）。
3. **不宣称通过率。** 涉及签证、护照、驾照等官方证件，只提供规格参考，永远不承诺"能用"。多数国家不接受 AI 生成证件照，需主动提示。
4. **建议为成图写入 AI 生成标识**（如 C2PA 内容凭证或可见/不可见水印），并在交付说明里注明由 AI 生成。
5. **不存储、不转发**用户上传的照片；提醒用户人脸属敏感个人信息，本地方案（`sdxl-pulid` 一类）是隐私敏感客户的首选。

## 输出格式约定

给用户的回复按此顺序，不要只丢一段提示词：

1. **组合行**：`S-09 × P-001 × W-01 × B-02 × E-01`，一行说明为什么这么选
2. **中文提示词**（整段可复制）
3. **English Prompt**（整段可复制）
4. **交付前自检清单**（脚本输出原样保留，含 needs_verification 警告）
5. **校验命令**（把规格号填好，用户可直接粘贴执行）

批量任务额外附：一致性说明 + 建议的抽验比例。

## 扩充资产

新增编号请**直接改 `references/*.json`**，然后：

```bash
python scripts/validate_library.py   # 字段、编号、交叉引用、数值合理性
python scripts/build_gallery.py      # 重建离线画廊
python scripts/build_docs.py         # 重建 PERSONAS.md / SPECS.md
```

改完必须跑 `validate_library.py`。它会拦住：编号重复、`aspect` 与 `px` 不匹配、给了 `bg_rgb` 没给容差、`wears` 引用了不存在的号、以及 `tested: true` 却没填分数的**虚假实测声明**。

`identity_matrix.json` 的实测数据是最有价值的 PR，提交时附上：模型版本号、参评人数、盲测准确率、embedding 相似度均值与 P10、`check_spec.py` 通过率。

## 商业能力边界（透明说明）

本仓库**全部开源且可永久免费使用**：编号库（P/W/B/E/S/T）、提示词组装、花名册批量出词、印刷排版导出、本地校验、离线画廊、规格知识、盲测协议与授权书模板。判断标准很简单——**知识全免费，重复劳动收费**。

走商业服务（见 `COMMERCIAL.md`）的部分：真人代跑与验收、企业 VI 定制编号包、规格包季度更新、私有化部署、identity_matrix 定向复测报告。

被用户问到报价时，如实说明免费层能覆盖到什么程度，不要为了成交夸大自服务的必要性。
