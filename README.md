# 🖼️ inkflow / 墨流

把任意文章或文案，变成一套美观的公众号 / 小红书图文包，并配套输出可直接发布的正文与标题备选。

Turn any article or copywriting into a beautiful, scroll-ready WeChat / Xiaohongshu image card set, with ready-to-publish body copy and title alternatives.

遵循 [Agent Skills 开放标准](https://agentskills.io)，兼容 Claude Code、Cursor、GitHub Copilot、Codex、Windsurf、Gemini CLI、Perplexity Computer 等 30+ AI Agent 平台。

## 安装 / Install

```bash
npx skills add Ficere/inkflow
```

> 需要 Node.js。安装后 Agent 会自动发现并按需加载该技能。
>
> Requires Node.js. Once installed, your agent will auto-discover and load this skill when relevant.

<details>
<summary>其他安装方式 / Alternative methods</summary>

**手动安装 / Manual install：**

```bash
git clone https://github.com/Ficere/inkflow.git
# 将整个目录复制到你的 Agent 的 skills 目录下即可
# Copy the directory to your agent's skills folder:
#   Claude Code:  ~/.claude/skills/
#   Cursor:       .cursor/skills/
#   Copilot:      .github/skills/
#   Codex:        ~/.codex/skills/
#   Gemini CLI:   .gemini/skills/
```

**Perplexity Computer：**

下载本仓库 zip → 在 [Skills 管理页面](https://www.perplexity.ai/computer/skills) 上传。

</details>

## 使用 / Usage

安装后直接用自然语言触发，无需任何配置：

```
帮我把这篇文章做成图文包
```

```
把这篇文案做成小红书图文，用 dusty_rose 配色
```

```
生成小绿书图片流，主题是职场焦虑，用 slate 配色
```

```
这篇文章封面用一个人坐在空旷办公室里发呆的场景，配色用 warm
```

## 输出内容 / Output

| 文件 | 说明 |
|------|------|
| `cover_<主题>.png` | AI 生成的 16:9 封面插画（无文字，纯场景） |
| `images_<主题>.zip` | 编号图片包：`01.png` 封面卡 + `02–NN.png` 正文页 |
| `publish_copy_<主题>.md` | 公众号发布文案：标题备选、推荐标题、封面文案、正文、标签、配图说明 |

图片规格：**1080 × 1920 px · 阿里巴巴普惠体 · 6 种配色**

## 功能 / Features

| 模块 | 说明 |
|------|------|
| **AI 封面生成** | 根据文章主题自动生成 16:9 插画封面，支持传入 IP 形象参考图 |
| **封面卡排版** | 封面图 + 渐变过渡 + 居中标题 + 关键词导读，一页抓住读者 |
| **正文分页** | 自动断行、分段、分页，字号 52px，行距 1.65×，适合手机滑读 |
| **发布文案** | 除 PNG 外输出公众号可复制正文、推荐标题、标题备选、封面文案与标签 |
| **批量工作流** | `generate_up_distill_cards.py` 可把一批 Markdown 草稿渲染成逐篇文件夹 + 总合集 |
| **6 种配色** | warm / cool_blue / sage_green / dusty_rose / amber / slate |
| **元数据隔离** | 文章内 `---` 分隔线后的内容不会出现在图片里，可放写作备注 |

<details>
<summary>配色选色指南 / Color theme guide</summary>

| 配色 | 背景色 | 适合场景 |
|------|--------|---------|
| `warm` | 暖白 | 社会话题、生活感悟、通用文章 |
| `cool_blue` | 冷蓝 | 科技、AI、理性分析 |
| `sage_green` | 柔绿 | 成长、健康、自然 |
| `dusty_rose` | 暗粉 | 情感、关系、个人叙事 |
| `amber` | 琥珀 | 消费、经济、职场 |
| `slate` | 蓝灰 | 职场、制度、严肃话题 |

</details>

## 独立脚本 / Standalone Script

`scripts/generate_images.py` 可以脱离 Agent 平台独立运行（Python 3，依赖 Pillow）：

```bash
# 安装依赖
pip install Pillow

# 字体下载（首次运行前执行一次）
mkdir -p ~/workspace/fonts
curl -L "https://github.com/alibabadesign/puhuiti/raw/master/fonts/Alibaba%20PuHuiTi%202.0/Alibaba-PuHuiTi-2-55-Regular/Alibaba-PuHuiTi-2-55-Regular.ttf" \
  -o ~/workspace/fonts/Alibaba-PuHuiTi-Regular.ttf
curl -L "https://github.com/alibabadesign/puhuiti/raw/master/fonts/Alibaba%20PuHuiTi%202.0/Alibaba-PuHuiTi-2-75-SemiBold/Alibaba-PuHuiTi-2-75-SemiBold.ttf" \
  -o ~/workspace/fonts/Alibaba-PuHuiTi-Bold.ttf

# 运行
python scripts/generate_images.py \
  文章.txt \
  封面.png \
  "你的标题" \
  "关键词1,关键词2,关键词3" \
  输出.zip \
  warm \
  --copy-md publish_copy.md \
  --title-options "标题1|标题2|标题3" \
  --cover-copy "封面上的一句话" \
  --tags "#标签1 #标签2" \
  --include-copy-in-zip
```

## 使用案例 / Use Cases

> 以下案例均使用虚拟人物与虚拟信息，仅供演示参考。详细内容见 `references/use-cases.md`。

### 案例一：职场社交评论 → 公众号图文包

**输入**：一篇关于"假装上班"现象的社会评论文章，使用 `warm` 配色，关键词"失业惨耻感, 身份绑架, 商业区咖啡店, 自由职业, 面对真实"。

**输出**：`01.png` 封面卡 + `02–04.png` 正文页 + `publish_copy.md` 发布文案（含推荐标题、标题备选、封面文案、标签）。

### 案例二：科技评论 → 小红书图文模板

**输入**：一篇关于"大模型时代信息稠密”的科技分析文章，使用 `cool_blue` 配色，关键词"AI不能替代的, 信息稠密, 向内发展, 体验经验, 个人氛围"。

**输出**：冷蓝色调封面卡 + 4 正文页 + 小红书风格发布文案（短句 + emoji 建议）。

### 案例三：情感个人叙事 → 小绿书图文流

**输入**：一篇关于"离开上海"的个人叙事，使用 `dusty_rose` 配色，关键词"远离上海, 选择与放弃, 重新安排, 夜晚骑车, 答案不是逃跑"。

**输出**：暗粉色调文艺封面卡 + 5 正文页 + 小绿书配图说明。

### 案例四：批量生成 UP 主内容赋能包

**输入**：3 篇 Markdown 草稿（每篇含 `备选标题`、`封面文案`、`正文`、`标签`），使用 `generate_up_distill_cards.py` 批量转换。

**输出**：每篇一个文件夹（`01-封面.png` + `02-正文.png` + 公众号发布文案） + 合集 md + 生成清单 CSV。

## 批量生成 / Batch Workflow

如果你的草稿是 Markdown 文件夹，并包含 `## 备选标题`、`## 封面文案`、`## 正文`、`## 标签` 等小节，可使用批量脚本：

```bash
python scripts/generate_up_distill_cards.py \
  /path/to/drafts \
  /path/to/avatar.png \
  /path/to/output \
  --zip /path/to/output_bundle.zip
```

输出结构：

- 每篇文章一个文件夹
- `01-封面.png` + `02-正文.png` ...
- 每篇一份 `公众号发布文案.md`
- 根目录一份 `公众号发布文案合集.md`
- 根目录一份 `生成清单.csv`，包含标题备选、公开分类、PNG 张数与发布文案路径

批量脚本会把来源/内部备注类信息隔离在草稿里，公开文件以「个人思考笔记 / 原创笔记」口吐呈现。

<details>
<summary>文章 txt 格式说明</summary>

```
文章标题（第一行，会被跳过，不出现在正文页）

正文第一段……

第二段……

---
这里是备注，不会出现在图片里
```

第一个非空行视为标题行，从第二个非空行开始渲染为正文。`---` 之后的内容全部屏蔽。

</details>

## 目录结构 / Structure

```
inkflow/
├── SKILL.md                  # 技能入口（Agent 自动读取）
├── scripts/
│   ├── generate_images.py    # 单篇图片渲染脚本（Pillow，可独立运行）
│   └── generate_up_distill_cards.py # 批量生成 PNG + 公众号发布文案
├── references/
│   └── color-schemes.md      # 6 种配色的完整 RGB 值与选色指南
└── README.md
```

## License

MIT · 字体：[阿里巴巴普惠体](https://github.com/alibabadesign/puhuiti)（免费商用）
