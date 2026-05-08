# inkflow ✦ Article to Image Cards

> Turn any article or copywriting into a beautiful, scroll-ready image card set — in one command.

![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)
![Platform: Perplexity Computer](https://img.shields.io/badge/platform-Perplexity%20Computer-6366f1)
![Lang: Python 3](https://img.shields.io/badge/python-3.8%2B-blue)

---

## What it does

You have great writing. You just can't make it look this good.

**inkflow** takes your article text + a cover image, and outputs:

| File | What it is |
|------|-----------|
| `cover_<topic>.png` | AI-generated 16:9 cover illustration |
| `images_<topic>.zip` | `01.png` cover card + paginated body cards, ready to upload |

Card specs: **1080 × 1920 px · Alibaba PuHuiTi · 6 color themes**

Works with WeChat Official Account (微信公众号), Xiaohongshu (小红书), and any mobile-first platform.

---

## Preview

```
Article text  ──►  [inkflow]  ──►  01.png (cover card)
Cover image   ──►             ──►  02.png
                              ──►  03.png
                              ──►  ...NN.png
                              ──►  images.zip  (all cards bundled)
```

**Cover card layout:**
- Top half: cover illustration (AI-generated, photo, or your own artwork)
- Gradient fade into background
- Centered bold title
- Accent divider line
- Keyword bullet list

**Body card layout:**
- Clean top rule in accent color
- Body text: 52px Alibaba PuHuiTi Regular, 1.65× line height
- Paragraph spacing preserved
- Page number (N / Total) at bottom center

---

## Color Themes

| Theme | Preview | Best For |
|-------|---------|---------|
| `warm` | Warm off-white + teal | General / lifestyle / social |
| `cool_blue` | Cool blue + navy | Tech / rational / AI |
| `sage_green` | Soft sage + leaf | Growth / wellness / nature |
| `dusty_rose` | Muted blush + rose | Relationships / emotions |
| `amber` | Amber-white + gold | Economy / career / money |
| `slate` | Blue-grey + slate | Workplace / formal / serious |

---

## Quick Start

### As a Perplexity Computer Skill

1. Download [`SKILL.md`](./SKILL.md) or the full repo ZIP
2. Go to [perplexity.ai/computer/skills](https://www.perplexity.ai/computer/skills) → Upload skill
3. In any conversation, paste your article and say:

```
帮我把这篇文章做成图文包，用 warm 配色
```

The agent will handle font setup, cover generation, and card rendering automatically.

### Direct Script Usage

```bash
# 1. Install dependency
pip install Pillow

# 2. Download fonts (one-time)
mkdir -p ~/workspace/fonts
curl -L "https://github.com/alibabadesign/puhuiti/raw/master/fonts/Alibaba%20PuHuiTi%202.0/Alibaba-PuHuiTi-2-55-Regular/Alibaba-PuHuiTi-2-55-Regular.ttf" \
  -o ~/workspace/fonts/Alibaba-PuHuiTi-Regular.ttf
curl -L "https://github.com/alibabadesign/puhuiti/raw/master/fonts/Alibaba%20PuHuiTi%202.0/Alibaba-PuHuiTi-2-75-SemiBold/Alibaba-PuHuiTi-2-75-SemiBold.ttf" \
  -o ~/workspace/fonts/Alibaba-PuHuiTi-Bold.ttf

# 3. Run
python scripts/generate_images.py \
  article.txt \
  cover.png \
  "你的标题" \
  "关键词1,关键词2,关键词3" \
  output.zip \
  warm
```

---

## Article File Format

Plain `.txt` file. First non-empty line = title (skipped in body render). Content after `---` is stripped (use it for metadata/notes).

```
你的文章标题

正文第一段……

第二段……

---
这里是备注，不会出现在图片里
```

---

## Repository Structure

```
inkflow/
├── SKILL.md                  # Perplexity Computer skill instructions
├── README.md                 # This file
├── scripts/
│   └── generate_images.py    # Core rendering script
└── references/
    └── color-schemes.md      # Full RGB values for all themes
```

---

## Requirements

- Python 3.8+
- [Pillow](https://pillow.readthedocs.io/) (`pip install Pillow`)
- Alibaba PuHuiTi font files (see Quick Start)

---

## License

MIT © [gljx898989](https://github.com/gljx898989)

Font: [Alibaba PuHuiTi](https://github.com/alibabadesign/puhuiti) — free for commercial use under its own license.
