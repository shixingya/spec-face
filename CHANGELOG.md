# 更新日志 Changelog

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 与[语义化版本](https://semver.org/lang/zh-CN/)。

判断标准一句话：**知识全免费，重复劳动收费。** 每一版新增的能力都在免费层，收费的从来只是"替你把两百人做完"。

---

## [0.4.0] - 2026-09-30 · 在线试用站：不装 Python 也能选编号、出提示词、验成图

前几版所有的门槛里，最劝退的不是"不懂规格"，是"要先装 Python"。这一版把**出词**和**校验**这两步搬到浏览器：<https://shixingya.github.io/spec-face/>。纯静态、无后端、无账号、无统计脚本。

### 新增 Added

- **`docs/index.html` + `docs/assets/`——试用台四步**
  1. 定规格 `S`：选中后直接摊开尺寸 / DPI / 头部占比 / 瞳孔线 / 底色 RGB / 体积上限，`needs_verification` 的规格在页面上同样标黄提醒
  2. 选岗位 `P` + 着装 `W` + 背景 `B` + 神态 `E`，说一句"这个人长什么样" → 组合编号、中文提示词、English Prompt、交付前自检清单，一键复制
  3. 拖图片进浏览器做本地校验，逐项 ✓ / ✗ / −
  4. 选生成后端 `G`，页面**生成给你本机跑的 `gen_portrait.py` 命令**（含 `--photo`、`--confirm-authorized` 与三道闸门说明），并列出该后端的显存门槛与权重许可
- **`scripts/build_site.py`** —— 把 `references/*.json` 打包成 `docs/data/library.js`，顺带同步离线画廊。网页**不另存一份数字**：改 JSON 不重跑构建脚本，这一条在 `MANIFEST.md` 的改动流程里排第 4 步
- 站点内页 `/spec-face/gallery.html`：全量编号图鉴（72 张卡片）随构建一起发布

### 一致性 Consistency（这一版最重要的一条）

网页版提示词拼装是 `prompt_spec.py --json` 的逐句 JS 移植，包括缺省维度按岗位推荐并说明理由那段。两边对同一组输入做了 **SHA-256 比对，逐字符与哈希都一致**（2026-09-30 在 0.4.0 构建产物上复测）：

```
输入：--spec S-09 --persona P-001
      --subject "30岁男性，方脸，短寸发，自然肤色"
      --subject-en "30-year-old man, square face, buzz cut, natural skin tone"

中文 500 字符  e128f73cc225714429296d0fe468e702aea1332750cc7d9163363241ad902688
英文 1354 字符 b0fad1290e3878d1ca6acdc7031fb8f82880644dbf8799325b2b8117d214f0a1
             ↑ 命令行 `prompt_spec.py --json` 与网页 textarea 两侧实测相同
```

不会出现"网页给的和命令行给的不是一句话"。底色取样同样沿用 `check_spec.py` 的口径：顶边 + 侧边上部、逐通道中位数，**不是整圈均值**（整圈取样会把肩膀和头发算进背景，一张合格的白底照反而被判不合格）。同一张 `images/sample-headshot.jpg` 在 `S-01` 下，网页给的结论与 `check_spec.py` 逐行相同：3 项 ✗、3 项 −、背景取样中位色 rgb(239, 239, 240)、最大偏差 16。

### 已知缺口 Known gaps

- **浏览器里没有 DPI 元数据，也不做人脸检测**：这两项在网页上一律标 `−`，不假装通过。真正的 DPI 与头部占比判定仍归本机 `check_spec.py`
- **页面不出图**。渲染必须由本机 Python + GPU 完成，网站不代跑、不排队、不托管——它只是一台没有安装门槛的计算器
- 拖进去的图片在浏览器本地解码，页面不发任何上传请求；但它是**静态站**，别把它当成私有化部署的替代品
- **发布仍是手工同步**：`docs/` 是源，`gh-pages` 分支是 Pages 的发布副本，改了 `docs/` 必须重跑 `build_site.py` 并全量覆盖一次，否则线上还是旧数字库。接 CI 已在路线图，本版刻意**没有**上一个没跑过的 workflow 文件

### 变更 Changed

- 双语 README 顶部加在线试用入口，痛点表补一行"装环境之前先想看看长什么样"，快速开始新增第 3 步「上面这两步，浏览器里也有一份」
- `MANIFEST.md` 新增「试用站发布」小节，写清 `docs/` → `gh-pages` 的手工同步步骤，以及一个真实坑：Pages 的 "Site not found" 页**也返回 HTTP 200**，验证必须 grep `<title>` 而不是看状态码

### 规模 Stats

试用站 5 个文件：`index.html` 7.4KB · `assets/app.js` 19.0KB · `assets/style.css` 6.0KB · `data/library.js` 52.9KB · `gallery.html` 130KB

---

## [0.3.0] - 2026-09-29 · 生成后端层：从照片直接出合规头像

用户要的不是一段提示词，是一张能印进工卡的图。这一版补上从**本人照片**到**成图**的那一段——出图由你自己机器上跑的开源服务完成，本仓库不训练、不托管、不代跑、不上传。

### 新增 Added

- **`references/providers.json`——生成后端 G-01~G-06**（第 7 个编号层）
  - `G-01` ComfyUI + PuLID · `G-02` ComfyUI + InstantID · `G-03` SD WebUI/Forge + IP-Adapter-FaceID
  - `G-04` Diffusers PhotoMaker（配方交接，本仓库不代跑 torch）
  - `G-05` OpenAI 兼容 `/v1/images` 端点 · `G-06` 只导出提示词与请求体（无 GPU 时的默认落点）
  - 每条都写明协议、默认端点、显存门槛、**权重许可**与易翻车点（例如 InstantID 会把脸"拍得更立体"、PhotoMaker 权重 CC-BY-NC **不可商用**）
- **`scripts/gen_portrait.py`** —— 照片 → 按规格居中裁切并 EXIF 转正 → 组装双语提示词 → 身份注入请求 → 本机服务出图 → 自动回跑 `check_spec.py` → 写 `render_manifest.json`（谁授权、走哪个后端、哪些项没过）
- **`scripts/studio.py`** —— 本机头像工作台，**只监听 127.0.0.1**：左边选照片，中间挑 `S/P/W/B/E` 并实时画构图辅助线，右边选后端、勾授权、点生成，结果卡片下面直接挂规格校验结论
- **三道闸门，写在代码里而不是文档里**
  1. 没有 `--photo` 拒跑——凭文字生成一个不存在的人，是写真需求，请回 `prompt_spec.py`
  2. 没有 `--confirm-authorized` 拒跑，且拒绝一切"用生成的照片去过门禁 / 活体检测 / 实名认证"的用法
  3. 请求体里找不到身份注入节点（PuLID / InstantID / IP-Adapter / ReActor）拒跑——**没有身份注入的文生图必然画出"更好看但不是本人"的人，而"像不像本人"是工牌头像唯一的通过条件**
- **默认只连回环地址**：端点非 127.0.0.1 / localhost 一律拒绝，跨出去必须你自己写 `--allow-remote`——把人脸上传到别人的服务器，这个决定该由操作的人明确承担，而不是由工具的默认值替他做
- `validate_library.py` 开始校验 `providers.json`：`status: verified` 却没有 `evidence` 字段直接判失败

### 变更 Changed

- `SKILL.md` 工作流扩到 7 步、使用模式扩到 5 种，合规红线补 3 条（身份注入、回环、不许谎称出图）
- 双语 README 新增「从照片到成图」章节，命令与输出全部为真实捕获
- `SPECS.md` 与离线画廊新增「生成后端」表格与标签页（画廊共 72 张卡片）
- `COMMERCIAL.md` 把"私有化部署"写成具体交付物：**在你的内网把 G 层搭通，调到 `check_spec.py` 连续 20 张全过为止**，12000 元起

### 已知缺口 Known gaps

- **G-01~G-05 全部标 `unverified`：本仓库从未在任何真实 GPU 上跑通过这条出图链路。** 已验证的只有协议形状（端点、字段、上传→排队→轮询→下载的完整流程，用本机假服务端端到端跑过）和闸门逻辑。唯一标 `verified` 的 G-06 只写本地文件，不发任何网络请求
- 不预置 ComfyUI 工作流模板——节点名随插件版本变，硬编码必翻车，只认你自己「Save (API Format)」导出的文件与 `{{prompt}}` 一类占位符
- `studio.py` 还是单人单次，没和 `batch_roster.py` 打通

### 规模 Stats

15 files changed, +1438 / −48 · 编号层 6 → 7（P/W/B/E/S/T/G）· 脚本 9 → 11 · 资产 66 → 72 条

---

## [0.2.0] - 2026-09-29 · 批量与印刷交付层

免费层解决"怎么做"，这一版解决"两百个人、下周三之前、还要能过打印店"。

### 新增 Added

- **`references/papers.json`——打印载体 T-01~T-06**：3R/4R/5R/6R 相纸、A4、CR80 PVC 卡面，含出血、间距、留白默认值
- **`scripts/print_export.py`** —— 按 `mm × dpi` 反算目标像素，多联排版、边缘像素补出血、CMYK 转换、裁切线；同时给 RGB 冲印稿与 CMYK 印刷稿并说明各交给谁；证件照默认**绝不旋转**凑版
- **`scripts/batch_roster.py`** —— 读 HR 的 Excel/CSV：认编号也认 HR 嘴里的「仓储主管」「置业顾问」（125 个岗位别名），补默认值、查冲突，输出每人双语提示词 + `prompts.jsonl` + `review.html` 复核表 + `batch_manifest.json`
- **批次一致性体检** —— 主动报告同一 `S-09` 里出现两种 `mood`、微笑幅度跨度大、着装不统一；这些正是甲方验收时挑刺的点
- **`scripts/guide_overlay.py`** —— 把瞳孔线带、头部高度框、背景取色区、70% 圆形安全区画到图上，让"差在哪"可见而不只是"过没过"
- **`scripts/score_matrix.py` + `research/`** —— 身份保真盲测协议、肖像授权书模板（含撤回权与删除期限）、打分表模板；聚合入库时**拒绝没有证据的结论**
- `images/sample-headshot.jpg` —— 本项目提示词生成的 AI 示例人像（带生成标识，非真人），README 里所有命令可直接复制执行

### 变更 Changed

- **单一真源**：`lib.print_fit()` 被 `print_export.py`、`validate_library.py`、画廊、`SPECS.md` 共用，不会出现"文档写 12 张、脚本算出 8 张"
- `check_spec.py` 重写背景取色：改为顶边 + 侧边上部采样后取逐通道中位数，修掉"白底被肩膀读成 rgb(181,182,183)"的误判
- `validate_library.py` 拦截虚假声明：`tested: true` 却缺分数、缺样本量、缺证据的条目一律失败

### 规模 Stats

27 files changed, +2936 / −180 · 新增 T 层 6 条 · 脚本 5 → 9

---

## [0.1.0] - 2026-09-29 · 首发

把"给谁看、什么气质、什么规格"拆成可组合、可校验的编号。

### 新增 Added

- **五层编号库**：岗位气质 `P` 20 条（含眼神、姿态、易翻车点）、着装仪容 `W` 12 条、背景光型 `B` 8 条、神态表情 `E` 8 条（含微笑幅度数值）、**合规规格 `S` 12 条**（一寸/二寸/小一寸/小二寸/护照/美签/申根/日本/CR80 工卡/门禁底库/企业 IM 圆裁/LinkedIn）
- `scripts/prompt_spec.py` —— 五元编号 + 一句"这个人长什么样" → 中英双语提示词 + 交付前自检清单；缺省维度按岗位推荐并说明理由
- `scripts/check_spec.py` —— 本地校验尺寸、底色、头部占比、瞳孔线、DPI、体积上限；判不了的项目标 `SKIP`，**绝不谎报通过**；图片全程不出本机
- `references/identity_matrix.json` —— 8 个生图模型的身份保真评测骨架。所有分数为 `null`，因为还没做真人实测——**我们没有编一组看起来很像真的数字填进去**
- `skills/portrait-prompter/SKILL.md` —— Agent Skill 定义：工作流、三种使用模式、身份保真红线、安全与合规红线
- 离线单页画廊：全文检索、一键复制双语提示词，双击即开

### 规模 Stats

25 files changed, +3567 · 资产 60 条 · 脚本 4 个

---

## 版本节奏 Versioning policy

- **补丁号**：数值修正、官方规格更新、别名扩充
- **次号**：新编号层或新交付环节
- **主号**：编号体系不兼容变更（会附迁移脚本）

规格数据里带 `needs_verification` 的条目，意味着我们还没逐条比对受理方最新公告——**使领馆、出入境、交管、平台的官方口径永远优先于本仓库**。
