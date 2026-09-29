# 身份保真盲测协议（identity_matrix 怎么填）

`references/identity_matrix.json` 是全项目最值钱、也最空的一块。
它值钱是因为没人愿意手工测；它空是因为**任何没经过真人盲测的分数都是假的**。
所以这份协议先规定怎么测，再规定什么才允许写进矩阵。

一句话原则：**分数可以难看，但不能来路不明。**

---

## 一、为什么要测这个

工牌头像和普通 AI 写真的差别只有一条：

> 这张照片挂在公司门口，同事认不认得出是他。

好看是次要指标，"像不像本人"是唯一通过条件。而目前市面上所有"AI 证件照"教程都在回答另一个问题——
怎么让图更好看。这就是本项目要做矩阵的原因：把"哪个模型垫图后最不像换人"这件事测清楚。

## 二、最低门槛（低于此不得写入矩阵）

| 项 | 要求 | 为什么 |
|---|---|---|
| 志愿者 | ≥ 8 人，覆盖不同性别、年龄段、肤色、脸型 | 3 个年轻男性测不出磨皮对深肤色偏色的问题 |
| 每人原生照 | 3 张：正面证件角度、45 度、自然光生活照 | 只用正面照会高估模型在真实素材上的表现 |
| 每人每模型出图 | ≥ 5 次 | 批次一致性要看离散度，跑 1 次没有方差 |
| 盲测评审 | ≥ 3 人，未参与生成过程 | 生成者自己当评审等于没测 |
| 提示词 | 固定用 `prompt_spec.py --locked` 输出，全程不许改词 | 改词就等于换了被测对象 |
| 模型版本 | 必须记 `model_version` | 模型一更新，旧分数立刻变成误导 |

## 三、一轮测试怎么跑

1. **收授权**。用 `research/consent-form.md`，一人一份，签完再拍。没签就不测。
2. **建素材目录**（全部本地，不要上传网盘公开链接）：
   ```
   research/data/V01/src_front.jpg
   research/data/V01/src_45.jpg
   research/data/V01/src_life.jpg
   ```
   `data/` 已在 `.gitignore` 里，永远不要提交真实人脸。
3. **锁定提示词**：
   ```
   python scripts/prompt_spec.py --spec S-09 --persona P-018 --subject "32岁男性，方圆脸，短发" --locked
   ```
   把输出的中文段与英文段分别存成 `locked_zh.txt` / `locked_en.txt`，所有模型用同一份。
4. **逐模型出图**：每人每模型 5 次，命名 `out_<model>_V01_r1.jpg`。**中途不许换措辞、不许挑图**。
   挑图会把均值刷上去，这是矩阵最常见的污染方式。
5. **规格通过率**：
   ```
   python scripts/check_spec.py out_<model>_V01_r*.jpg --spec S-09 --json
   ```
   把每张图的 pass/fail 填进 `spec_check_pass`（1/0）。
6. **盲测同认率**：把成图与该志愿者的 3 张原生照混排（含干扰项：别人的照片），
   请 3 名评审独立判断"哪些是同一个真人"，结果填 `judge_1/2/3`（1=认对，0=认错）。
   评审不能看到模型名，也不能看到成图顺序。
7. **主观分**：由测试人按 `identity_matrix.json` 的 `scoring_dimensions` 量表填
   `identity_fidelity`（1-5）、`beauty_drift`（0-3）、`batch_consistency`（1-5）。
8. **可选客观指标**：统一人脸检测器算 embedding 余弦相似度，填 `embedding_cosine`。
   必须全项目用同一个检测器，否则跨模型不可比。
9. **聚合入库**：
   ```
   python scripts/score_matrix.py 我的实测.csv --dry-run
   python scripts/score_matrix.py 我的实测.csv --evidence "issue#12" --write
   python scripts/validate_library.py
   ```

## 四、打分表列定义

模板：`research/score-sheet-template.csv`（示例行请删掉）。

| 列 | 含义 | 取值 |
|---|---|---|
| `model_key` | 模型标识 | 必须是 `identity_matrix.json` 里已有的 key，否则脚本会拒绝并提示先增行 |
| `model_version` | 模型版本号 / build 号 | 必填，写"最新"视为未填 |
| `tested_at` | 测试日期 | ISO `YYYY-MM-DD` |
| `tester` | 测试人代号 | 不要写真名，别把同事写进公开仓库 |
| `subject_id` | 志愿者编号 | `V01` 这种匿名编号，**不要写姓名** |
| `source_photo` / `output_file` | 素材文件名 | 只记文件名，不记路径不记内容 |
| `spec_id` | 目标规格 | `S-09` 等 |
| `identity_fidelity` | 身份保真度 | 1-5，见量表 |
| `beauty_drift` | 美颜漂移 | 0-3，越高越不可用 |
| `batch_consistency` | 批次一致性 | 1-5 |
| `judge_1..3` | 盲测同认 | 1=认对 0=认错 |
| `embedding_cosine` | 人脸向量余弦相似度 | 0-1，可选 |
| `spec_check_pass` | 规格自检是否通过 | 1/0 |
| `failure_mode` | 失败模式 | 耳部畸变 / 牙齿异常 / 肤色偏红 … |

聚合口径：主观分取**中位数**（不是均值，一次翻车不该把模型打死）；
embedding 同时报 **mean 与 P10**（工牌场景看的是最差那 10% 像不像）。

## 五、什么算作弊（会让 PR 直接不合）

- 只挑每个模型最好的一张去打分（选择偏差）
- 生成者本人兼任盲测评审（利益相关）
- 用 3 个志愿者得出"全模型第一"（样本不足，`score_matrix.py` 会拦）
- 不写 `model_version`（三个月后无人能复核）
- 拿别家的分数抄进矩阵（来源不可复核 = 没有证据）

## 六、为什么这份数据也是商业入口

免费层公开**协议、模板、脚本、以及最终结论表**；
付费层提供的是：企业 VI 色下的定向实测（你的工牌底色、你的岗位着装、你的门禁设备），
以及每季度模型更新后的复测报告。协议谁都能抄，一轮 8 人 × 8 模型 × 5 次的真人盲测抄不走。
