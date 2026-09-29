# 岗位气质 · 着装 · 背景光型 · 神态 编号图鉴

> 本文件由 `scripts/build_docs.py` 从 `references/*.json` 生成，**不要手工编辑**。

- 岗位 `P`：决定「像个干这行的人」
- 着装 `W`：决定「穿什么」
- 背景光型 `B`：决定「在什么环境、什么光」
- 神态 `E`：决定「什么表情」
- 合规规格 `S`：见 [SPECS.md](SPECS.md)

组装一条提示词：

```bash
python scripts/prompt_spec.py --spec S-09 --persona P-001 --subject "30岁男性，圆脸，短寸发，自然肤色"
```

## 一、岗位气质（P）

| 编号 | 岗位 | 行业 | 气质 | 眼神 | 姿态 |
| :-- | :-- | :-- | :-- | :-- | :-- |
| **P-001** | 后端工程师 / Backend Engineer | 技术 | 沉稳、可靠、不张扬 | 平视镜头，目光聚焦不游移，带一点想事情的延迟感 | 肩线正对镜头，下巴微收 3 度，双肩放松下沉 |
| **P-002** | 产品经理 / Product Manager | 技术 | 清晰、有主见、好沟通 | 直视镜头，眼神明亮，眉尾略微上扬表示兴趣 | 上身略前倾 5 度，肩线打开 |
| **P-003** | 金融分析师 / Financial Analyst | 金融 | 严谨、克制、有分寸 | 平视，目光稳定不眨，嘴角完全闭合 | 肩线水平端正，颈部拉长，头不偏 |
| **P-004** | 律师 / Attorney | 法务 | 镇定、有权威、可托付 | 略低于眼位的机位，目光平直不逼迫 | 端正坐姿感，双肩下沉，头部保持水平 |
| **P-005** | 临床医生 / Physician | 医疗 | 干净、镇定、有掌控力 | 正视镜头，目光温和但不停留游移 | 肩线正对，颈部露出，白大褂领口平整 |
| **P-006** | 护士 / Nurse | 医疗 | 亲和、耐心、让人安心 | 眼神柔和，眼角自然放松 | 肩线略向镜头方向打开，头可微侧 5 度 |
| **P-007** | 教师 / Teacher | 教育 | 温和、有条理、能压住场 | 正视镜头，目光平稳带一点审视的善意 | 肩线水平端正，下颌略收 |
| **P-008** | 销售顾问 / Sales Consultant | 销售 | 有精神、可信、主动 | 直视镜头，眉毛自然舒展，眼神先一步打招呼 | 上身略前倾，肩打开，头保持水平 |
| **P-009** | 门店店长 / Store Manager | 零售 | 实干、亲切、能解决问题 | 平视镜头，目光直接不绕 | 肩线正对，姿态放松但不塌 |
| **P-010** | 物流调度 / Logistics Coordinator | 供应链 | 利落、抗压、靠得住 | 正视镜头，目光快而准 | 肩线水平，头部端正不侧 |
| **P-011** | 物业客服 / Property Service | 物业服务 | 耐心、好说话、有边界 | 眼神柔和正视，不刻意讨好 | 肩线打开，头微侧不超过 5 度 |
| **P-012** | 房产经纪 / Real Estate Agent | 销售 | 干练、热络、消息灵通 | 直视镜头，眼神带一点分享好消息的劲 | 上身端直，肩打开，微前倾 |
| **P-013** | 设计师 / Designer | 创意 | 有审美主见、松弛、不装 | 目光略微偏离镜头 10 度，或直视但放松 | 肩线可略斜，姿态自然不做作 |
| **P-014** | 内容运营 / Content Operations | 创意 | 灵活、有网感、好合作 | 眼神灵动，眉尾轻微上挑 | 肩线自然，头可微侧 8 度 |
| **P-015** | 人力资源 / HR Business Partner | 职能 | 稳、可倾诉、有原则 | 正视镜头，目光稳定且不带评判 | 肩线水平端正，头保持水平 |
| **P-016** | 财务 / Finance Manager | 职能 | 细、稳、不多话 | 平视，目光安静聚焦 | 肩线端平，身体不做倾斜 |
| **P-017** | 技术支持 / Technical Support | 技术 | 有耐心、反应快、不推诿 | 直视镜头，眼神先一步回应 | 肩线放松打开，微前倾 |
| **P-018** | 连锁门店员工 / Frontline Retail Staff | 零售 | 整齐划一、有品牌感、亲和 | 标准正视镜头，目光干净统一 | 统一规范：肩线水平正对镜头，头不侧 |
| **P-019** | 仓库与产线 / Warehouse & Line Operator | 制造 | 踏实、能吃苦、守规矩 | 正视镜头，目光朴实稳定 | 肩线正对，姿态自然不挺胸 |
| **P-020** | 自由职业与咨询顾问 / Independent Consultant | 专业服务 | 专业但不冷，有个人风格 | 直视镜头，眼神有内容和故事感 | 端正但放松，允许肩线有 5 度自然差 |

### 风格描述原文

#### P-001 · 后端工程师（Backend Engineer）

- 关键词：深色圆领或立领、无 logo、哑光质感、不刻意微笑 / dark crew or mandarin collar, no logo, matte texture, no forced smile
- 中文：低调的技术气质：深色简约上衣，无任何标识，面部不加滤镜修饰，表情平静而专注，传递可信赖的工程感
- English: Understated engineering presence: dark minimal top without any logo, unretouched skin, calm focused expression, conveying dependable technical credibility
- 推荐组合：着装 W-01/W-02/W-06 · 背景 B-01/B-03 · 神态 E-01/E-05
- ⚠ 易翻车：过度磨皮和美白会直接削弱可信度；西装领带会让人误读为销售岗

#### P-002 · 产品经理（Product Manager）

- 关键词：浅色衬衫或针织、简洁、轻微笑意露齿、明亮 / light shirt or knit, clean, slight open smile, bright
- 中文：清爽的协作者气质：浅色简洁上衣，明亮面部光，自然露齿轻笑，眼神有交流感，像一个随时能把你问题接住的人
- English: Crisp collaborator presence: light clean top, bright facial lighting, natural closed-lip-to-slight smile, engaging eye contact that reads as someone ready to own your problem
- 推荐组合：着装 W-02/W-03 · 背景 B-02/B-03 · 神态 E-02/E-03
- ⚠ 易翻车：笑过头会变成客服；背景过暗会显得疲惫

#### P-003 · 金融分析师（Financial Analyst）

- 关键词：深色西装、素色领带或高领、冷调、零装饰 / dark suit, plain tie or turtleneck, cool tone, zero accessories
- 中文：克制的专业感：深色合体西装与素色内搭，冷白调光，面部线条干净利落，无首饰无装饰，表情中性偏严谨
- English: Restrained professionalism: well-fitted dark suit with plain inner layer, cool white lighting, clean facial lines, no jewelry or accessories, neutral-to-serious expression
- 推荐组合：着装 W-04/W-07 · 背景 B-01/B-04 · 神态 E-01/E-04
- ⚠ 易翻车：背景出现城市天际线或书架会显得刻意；暖光会削弱严谨感

#### P-004 · 律师（Attorney）

- 关键词：深色正装、挺括领口、适度对比度、不笑 / dark formal wear, crisp collar, moderate contrast, no smile
- 中文：权威而不压迫：挺括深色正装与清晰领口，中等对比度的稳重型打光，表情沉稳、嘴角闭合，传递可托付的判断力
- English: Authority without intimidation: crisp dark formal wear with a clean collar line, moderate-contrast steady lighting, composed closed-mouth expression signaling sound judgment
- 推荐组合：着装 W-04/W-07 · 背景 B-04/B-01 · 神态 E-04/E-01
- ⚠ 易翻车：机位过高会显得弱势；背景纹理过重抢注意力

#### P-005 · 临床医生（Physician）

- 关键词：白大褂、内搭浅色、头发整齐、无配饰 / white coat, light inner layer, neat hair, no accessories
- 中文：洁净的临床可信度：平整白大褂配浅色内搭，高调明亮布光，头发与领口整洁，表情温和镇定，无首饰无杂物
- English: Clinical trust through cleanliness: crisp white coat over a light inner layer, high-key bright lighting, neat hair and collar, calm warm expression, no jewelry or clutter
- 推荐组合：着装 W-08/W-03 · 背景 B-01/B-05 · 神态 E-01/E-03
- ⚠ 易翻车：背景出现听诊器特写或药品会像广告图；阴影过重显得病态

#### P-006 · 护士（Nurse）

- 关键词：护士服或浅色制服、头发束起、柔光、自然微笑 / nurse uniform or light scrubs, hair tied back, soft light, natural smile
- 中文：安心的照护感：整洁浅色制服，头发放顺束起，柔和散射光，自然真诚的微笑，眼周放松，传递耐心与可靠
- English: Reassuring care: neat light uniform, hair softly tied back, diffused gentle lighting, genuine natural smile with relaxed eye area, conveying patience and reliability
- 推荐组合：着装 W-08/W-03 · 背景 B-05/B-02 · 神态 E-02/E-03
- ⚠ 易翻车：笑容僵硬会立刻掉信任；浓妆与制服气质冲突

#### P-007 · 教师（Teacher）

- 关键词：衬衫或针织开衫、素雅、中等明度、轻笑或不笑 / shirt or cardigan, muted, medium brightness, light smile or neutral
- 中文：有秩序感的亲和力：素雅衬衫或开衫，中等明度均匀布光，表情温和中带一点严肃，像能同时管好四十个人的神态
- English: Orderly warmth: muted shirt or cardigan, even medium-brightness lighting, an expression gently warm yet slightly serious, the look that holds a room of forty
- 推荐组合：着装 W-03/W-05 · 背景 B-02/B-03 · 神态 E-03/E-01
- ⚠ 易翻车：背景书架虚化过度像咖啡厅；过于时髦的穿搭削弱权威

#### P-008 · 销售顾问（Sales Consultant）

- 关键词：合体衬衫、整洁、明亮、露齿轻笑 / fitted shirt, groomed, bright, open smile
- 中文：主动的可信感：合体衬衫与整洁仪容，明亮通透布光，露齿轻笑、眉宇舒展，神态像已经准备好回应你的需求
- English: Proactive credibility: fitted shirt with neat grooming, bright transparent lighting, open slight smile with relaxed brows, radiating readiness to respond
- 推荐组合：着装 W-03/W-04 · 背景 B-02/B-03 · 神态 E-02/E-06
- ⚠ 易翻车：笑过度和露齿过多会显轻浮；深色背景削弱主动性印象

#### P-009 · 门店店长（Store Manager）

- 关键词：工装或 Polo、干净、自然光感、轻微笑 / work shirt or polo, clean, natural light feel, light smile
- 中文：落地能干的气质：简洁工装或 Polo 衫，自然光感不修饰，表情亲切直接、带一丝笑意，像在高峰期照样稳住场子的人
- English: Grounded operator vibe: simple work shirt or polo, unpolished natural light, friendly direct expression with a trace of a smile — someone who holds the floor through peak hours
- 推荐组合：着装 W-06/W-09 · 背景 B-01/B-02 · 神态 E-02/E-06
- ⚠ 易翻车：正装感过重反而不贴岗；背景出现货架易杂乱

#### P-010 · 物流调度（Logistics Coordinator）

- 关键词：深色工装、简洁、对比度略高、不笑 / dark workwear, spare, slightly higher contrast, no smile
- 中文：高压环境的利落感：深色简洁工装，稍高对比度的直白布光，表情中性而警觉，传递随时能拍板调度的稳定
- English: High-pressure crispness: dark spare workwear, direct lighting with slightly raised contrast, neutral alert expression that reads as ready to make the call
- 推荐组合：着装 W-09/W-01 · 背景 B-01/B-04 · 神态 E-01/E-05
- ⚠ 易翻车：柔光会让人怀疑执行力；背景虚化过强像棚拍广告

#### P-011 · 物业客服（Property Service）

- 关键词：制服或衬衫、整洁、中明度、礼貌性轻笑 / uniform or shirt, neat, medium brightness, polite light smile
- 中文：得体不过界的亲和：整洁制服或衬衫，均匀中明度布光，礼貌而有分寸的浅笑，眼神愿意听但不谄媚
- English: Measured approachability: neat uniform or shirt, even medium-brightness lighting, a polite restrained smile, willing-to-listen eyes without flattery
- 推荐组合：着装 W-09/W-03 · 背景 B-02/B-01 · 神态 E-03/E-02
- ⚠ 易翻车：笑得太大显得不专业；过暗背景让人误判为管理层

#### P-012 · 房产经纪（Real Estate Agent）

- 关键词：西装或衬衫、整洁、明亮通透、露齿笑 / suit or shirt, groomed, bright clear, open smile
- 中文：热络的干练感：合体西装或挺括衬衫，明亮通透布光，露齿微笑，眼神像带着客户没开口就知道他要什么的消息
- English: Personable competence: fitted suit or crisp shirt with bright clear lighting, open smile, eyes carrying good news before you ask
- 推荐组合：着装 W-04/W-03 · 背景 B-02/B-03 · 神态 E-02/E-06
- ⚠ 易翻车：背景放楼盘或钥匙易像素材模板；笑过头损专业

#### P-013 · 设计师（Designer）

- 关键词：纯色基础款、无 logo、低饱和、表情淡 / solid basic, no logo, low saturation, plain expression
- 中文：松弛的审美感：纯色基础款、无任何标识，低饱和色调，表情淡然，姿态自然不摆拍，靠克制体现品位
- English: Relaxed taste: solid basics with no logo, desaturated tones, plain expression, unstudied posture — restraint as the signal of judgment
- 推荐组合：着装 W-01/W-05 · 背景 B-03/B-06 · 神态 E-05/E-01
- ⚠ 易翻车：背景出现设计作品或色卡像在炫；摆拍感会破坏松弛

#### P-014 · 内容运营（Content Operations）

- 关键词：轻时尚基础款、明快配色、自然光、笑容真实 / casual fashion basic, fresh color, natural light, real smile
- 中文：明快的协作感：轻时尚基础款与明快配色，自然光，真实笑容与灵动眼神，神态传递反应快、跟得住热点
- English: Bright collaborator energy: casual fashion basics with fresh color, natural light, genuine smile and lively eyes that signal quick, current instincts
- 推荐组合：着装 W-05/W-02 · 背景 B-03/B-02 · 神态 E-06/E-02
- ⚠ 易翻车：过度正装显得不搭岗；色调灰暗会毁掉网感

#### P-015 · 人力资源（HR Business Partner）

- 关键词：衬衫或西装外套、中性色、柔亮、礼貌浅笑 / shirt or blazer, neutral tone, soft bright, polite light smile
- 中文：有原则的亲和力：中性色衬衫或外套，柔亮均匀布光，礼貌浅笑与不带评判的注视，像能说真话的人也听得进话
- English: Principled warmth: neutral shirt or blazer, soft even lighting, a polite smile and non-judgmental gaze — someone who speaks straight and listens back
- 推荐组合：着装 W-03/W-07 · 背景 B-02/B-01 · 神态 E-03/E-04
- ⚠ 易翻车：笑得过甜削弱原则感；冷光会显得像审计岗

#### P-016 · 财务（Finance Manager）

- 关键词：素色衬衫、深色外套、低对比杂讯、不笑 / plain shirt, dark layer, clean low-contrast, no smile
- 中文：安静的严谨感：素色衬衫配深色外套，干净无杂讯的布光，表情中性、嘴唇闭合，传递不差毫厘的耐心
- English: Quiet rigor: plain shirt under a dark layer, clean noise-free lighting, neutral closed-mouth expression that reads as exacting patience
- 推荐组合：着装 W-03/W-04 · 背景 B-01/B-04 · 神态 E-01/E-05
- ⚠ 易翻车：配饰与花哨领口破坏克制感；暖黄光显得随意

#### P-017 · 技术支持（Technical Support）

- 关键词：工服或纯色 T、整洁、明亮、轻笑 / uniform or plain tee, neat, bright, light smile
- 中文：回应感极强的气质：简洁工服或纯色上衣，明亮通透布光，轻笑且目光主动，传递不会把你的问题推回去
- English: Strongly responsive presence: neat uniform or plain top, bright clear lighting, a light smile with initiating eyes that promise no runaround
- 推荐组合：着装 W-09/W-01 · 背景 B-02/B-01 · 神态 E-02/E-06
- ⚠ 易翻车：表情过冷会让客户以为要排队；背景杂乱损可信度

#### P-018 · 连锁门店员工（Frontline Retail Staff）

- 关键词：品牌工服、仪容规范、统一底色、标准微笑 / brand uniform, grooming standard, unified backdrop color, standard smile
- 中文：品牌统一规范感：整洁品牌工服与规范仪容，标准正面姿态，统一底色与光型，微笑幅度控制在标准范围，适合批量出图
- English: Brand-uniform standard: tidy branded uniform with grooming standards, squared-on posture, unified backdrop and lighting, smile held within standard range, built for batch output
- 推荐组合：着装 W-09/W-06 · 背景 B-01/B-02 · 神态 E-02/E-03
- ⚠ 易翻车：个性化打光会破坏整批一致性；批量场景务必锁定同一背景与光型

#### P-019 · 仓库与产线（Warehouse & Line Operator）

- 关键词：工服、安全规范、自然光、轻微微笑或不笑 / work uniform, safety compliance, natural light, faint smile or neutral
- 中文：朴实的可靠感：整洁工服与安全规范着装，自然偏硬的光，表情朴实稳定，不摆拍不修饰，传递一线实干的信任
- English: Plain reliability: clean work uniform with safety compliance, natural slightly hard light, grounded steady expression, unposed and unretouched — frontline trust
- 推荐组合：着装 W-09/W-10 · 背景 B-01/B-05 · 神态 E-01/E-05
- ⚠ 易翻车：背景出现设备易失焦杂乱；过度美颜会失去岗位真实感

#### P-020 · 自由职业与咨询顾问（Independent Consultant）

- 关键词：质感基础款、细节配饰克制、层次光、浅笑 / textured basic, restrained accessory, layered light, soft smile
- 中文：有辨识度的专业：质感基础款与克制细节，带层次的主光与轮廓光，浅笑且眼神有内容，既专业又像有自己方法论的人
- English: Distinctive professionalism: textured basics with restrained detail, layered key and rim lighting, a soft smile with substance behind the eyes — expert with a point of view
- 推荐组合：着装 W-07/W-05 · 背景 B-06/B-03 · 神态 E-04/E-03
- ⚠ 易翻车：层次光过强变明星写真；配饰抢戏会削弱专业主线

## 二、着装仪容（W）

| 编号 | 名称 | 说明 | 适配行业 |
| :-- | :-- | :-- | :-- |
| **W-01** | 深色圆领基础款 / Dark Crew Basic | 纯黑或深灰圆领，无任何印花与 logo，面料哑光不反光 | 技术、创意、职能 |
| **W-02** | 深色立领或半高领 / Dark Stand Collar | 立领或半高领，弱化领带感，保留一点正式度 | 技术、专业服务 |
| **W-03** | 浅色挺括衬衫 / Light Crisp Shirt | 白或浅蓝衬衫，领口挺括第一颗扣可选系 | 销售、职能、教育、医疗 |
| **W-04** | 深色合体西装 / Fitted Dark Suit | 深蓝或深灰西装，肩线合体，素色内搭 | 金融、法务、销售 |
| **W-05** | 针织开衫 / Knit Cardigan | 中薄针织，降低压迫感，适合教育与职能岗 | 教育、职能、创意 |
| **W-06** | Polo 衫 / Polo Shirt | 纯色 Polo，领子立得住，休闲与规范之间 | 零售、技术、供应链 |
| **W-07** | 高领毛衣 / Turtleneck | 细针织高领，去领带感并保留权威 | 金融、法务、专业服务 |
| **W-08** | 白大褂 / White Coat | 平整白大褂，内搭浅色，胸前不挂杂物 | 医疗 |
| **W-09** | 品牌工服 / Brand Uniform | 企业统一工服，批量场景必须锁定同一款式与同一色号 | 零售、物业服务、制造、供应链 |
| **W-10** | 安全规范着装 / Safety-Compliant Wear | 含反光条工装或安全帽，适用于产线与仓储门禁照 | 制造、供应链 |
| **W-11** | 护士服或刷手服 / Nurse Uniform or Scrubs | 浅色系护理服，头发束起，仪容规范 | 医疗 |
| **W-12** | 质感基础款（顾问向） / Textured Basic | 有面料质感的纯色基础款，靠剪裁而非logo体现品位 | 专业服务、创意 |

## 三、背景与光型（B）

| 编号 | 名称 | 目标底色 | 光型 | 适用 |
| :-- | :-- | :-- | :-- | :-- |
| **B-01** | 纯白无缝 / Seamless Pure White | rgb(255, 255, 255) | 正面柔光箱加下方补光，下巴无明显阴影，背景独立打亮 | 签证类、门禁人脸库、批量工卡 |
| **B-02** | 浅灰到白渐变 / Light Grey to White Gradient | rgb(214, 216, 219) | 45 度主光加反射板，背景留轻微中心亮、边缘暗 | 企业工卡、官网团队页、简历照 |
| **B-03** | 中性灰纯色 / Neutral Solid Grey | rgb(150, 152, 155) | 柔光主光加轻微轮廓光，人物与背景明度分离 | 创意与职能岗、对外沟通头像 |
| **B-04** | 深藏青纯色 / Deep Navy Solid | rgb(28, 38, 62) | 较高对比硬光，主光位偏高，塑造权威线条 | 金融、法务、管理层 |
| **B-05** | 医疗浅蓝绿 / Clinical Pale Blue-Green | rgb(208, 230, 231) | 高调柔光，几乎无阴影，色彩偏冷白 | 医护、口腔、诊所、药房 |
| **B-06** | 暖调微纹理纸面 / Warm Textured Paper | rgb(232, 222, 208) | 侧位柔光保留纸纹明暗，人物光略暖 | 咨询顾问、教育、文创岗 |
| **B-07** | 办公室轻度虚化 / Soft Office Blur | 不限 | 窗光为主加室内环境光，背景虚化控制在中等程度 | 对外销售、门店店长、顾问 |
| **B-08** | 品牌指定纯色 / Brand-Specified Solid | 不限 | 按品牌 VI 色值打背景，需先录入客户 RGB | 企业统一工卡、连锁门店 |

## 四、神态表情（E）

| 编号 | 名称 | 微笑幅度 | 说明 | 合规提示 |
| :-- | :-- | :-- | :-- | :-- |
| **E-01** | 平静专注 / Calm Focus | 0.00 | 嘴唇自然闭合，眼周放松，目光稳定不游移 | — |
| **E-02** | 亲和浅笑 / Approachable Light Smile | 0.40 | 嘴角上提 15 度以内，不露或微露齿，苹果肌自然发力 | — |
| **E-03** | 温和耐心 / Gentle Patience | 0.30 | 眉眼舒展，笑意很浅但持续，注视不带催促感 | — |
| **E-04** | 沉稳权威 / Grounded Authority | 0.05 | 面部肌肉整体放松但下颌明确，注视时长略增 | — |
| **E-05** | 内敛克制 / Reserved Restraint | 0.00 | 情绪幅度压到最低，适合技术与财务岗 | — |
| **E-06** | 明快主动 / Bright Initiative | 0.60 | 眉尾轻微上挑，笑意明确，眼神先一步打招呼 | — |
| **E-07** | 严谨中性 / Strictly Neutral | 0.00 | 证件与签证级中性表情，禁止微笑 | 多数国家签证照要求中性表情且双眼睁开，不得露齿笑 |
| **E-08** | 自信松弛 / Confident Ease | 0.35 | 肩线与面部同时松下来，笑或不笑都可以 | — |

## 五、批量出图的一致性约定

同一岗位、同一批人必须锁定同一组编号（尤其是背景与光型），否则整批一眼就能看出不齐：

- 后端工程师（批量）：`--spec S-09 --persona P-001 --wear W-01 --backdrop B-01 --mood E-01`
- 产品经理（批量）：`--spec S-09 --persona P-002 --wear W-02 --backdrop B-02 --mood E-02`
- 金融分析师（批量）：`--spec S-09 --persona P-003 --wear W-04 --backdrop B-01 --mood E-01`
- 律师（批量）：`--spec S-09 --persona P-004 --wear W-04 --backdrop B-04 --mood E-04`
- 临床医生（批量）：`--spec S-09 --persona P-005 --wear W-08 --backdrop B-01 --mood E-01`

> 批量场景避开 `B-07 办公室轻度虚化`（环境光无法统一）。需要品牌背景请用 `B-08` 并先录入客户 RGB。

