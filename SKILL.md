---
name: inkflow
description: "Turn any article or copywriting into beautiful WeChat / Xiaohongshu image-card sets (图文包). Given article text and a cover image, inkflow generates: (1) a 16:9 AI cover illustration, (2) a 1080×1920 cover card with title + keyword highlights, (3) paginated body cards with clean typography. Outputs a ZIP of numbered PNGs ready to upload. Supports 6 color themes: warm, cool_blue, sage_green, dusty_rose, amber, slate. Use when the user wants to turn copywriting, essays, or articles into scroll-friendly image cards for WeChat Official Account, Xiaohongshu, or any mobile-first platform."
license: MIT
metadata:
  author: gljx898989
  version: '1.0'
---

# inkflow — Article to Image Cards

Convert any article or copywriting into a beautiful, scroll-ready image card set — cover + paginated body cards — ready for WeChat Official Account, Xiaohongshu, or any mobile-first platform.

## When to Use This Skill

Load this skill when the user:
- Provides article text / copywriting and wants it turned into image cards
- Says things like "做成图文""生成图片流""做成小绿书/小红书样式""帮我排版成图片"
- Wants a WeChat cover image + image set (图文包) for their content
- Has finished writing but can't produce visual image cards themselves

## What You Will Produce

| Output | Description |
|--------|-------------|
| `cover_<topic>.png` | 16:9 AI-generated cover illustration (no text) |
| `images_<topic>.zip` | Numbered PNGs: `01.png` (cover card) + `02–NN.png` (body pages) |

Card specs: 1080 × 1920 px · Alibaba PuHuiTi font · 6 color themes

## Step-by-Step Instructions

### Step 1 — Gather inputs

Ask the user for (or infer from context):
- **Article text** — the full body copy. May be pasted inline or in a file.
- **Title** — the display title for the cover card (can differ from the article's first line).
- **Keywords / highlights** — 3–5 short phrases shown on the cover card as bullet points.
- **Color theme** — default `warm`. Options: `warm`, `cool_blue`, `sage_green`, `dusty_rose`, `amber`, `slate`. See `references/color-schemes.md` for guidance.
- **Cover image style** — a brief description of what the cover illustration should look like. If not provided, infer from the article topic.
- **IP character** (optional) — if the user has a mascot or character to include in the cover image.

If any of the above are missing and cannot be inferred, ask before proceeding.

### Step 2 — Set up fonts

The script requires Alibaba PuHuiTi. Check if fonts exist:

```bash
ls /home/user/workspace/fonts/Alibaba-PuHuiTi-Regular.ttf 2>/dev/null && echo "found" || echo "missing"
```

If missing, download them:

```bash
mkdir -p /home/user/workspace/fonts
curl -L "https://github.com/alibabadesign/puhuiti/raw/master/fonts/Alibaba%20PuHuiTi%202.0/Alibaba-PuHuiTi-2-55-Regular/Alibaba-PuHuiTi-2-55-Regular.ttf" \
  -o /home/user/workspace/fonts/Alibaba-PuHuiTi-Regular.ttf
curl -L "https://github.com/alibabadesign/puhuiti/raw/master/fonts/Alibaba%20PuHuiTi%202.0/Alibaba-PuHuiTi-2-75-SemiBold/Alibaba-PuHuiTi-2-75-SemiBold.ttf" \
  -o /home/user/workspace/fonts/Alibaba-PuHuiTi-Bold.ttf
```

### Step 3 — Copy the generation script

Copy the bundled script to the workspace:

```bash
cp /home/user/workspace/skills/inkflow/scripts/generate_images.py /home/user/workspace/generate_images.py
```

### Step 4 — Save the article text

Save the article text to a `.txt` file. The first non-empty line is treated as the title and skipped; body starts from the second non-empty line. Content after a `---` separator line is stripped (metadata zone).

```bash
# Example
cat > /home/user/workspace/article_<topic>.txt << 'EOF'
<title line>

<body paragraphs>
EOF
```

### Step 5 — Generate the cover illustration

Use `asi-generate-image` to generate a 16:9 cover PNG. No text in the image — it's a pure illustration.

```bash
asi-generate-image '{"prompt": "<scene description>", "filename": "cover_<topic>", "aspect_ratio": "16:9"}'
```

With `api_credentials=["llm-api:image"]`.

**Cover prompt guidelines:**
- Describe the scene, mood, and visual style concisely
- Match the article's emotional tone (warm/melancholic/energetic/contemplative)
- Request illustration style, not photorealism, for editorial feel
- If user has an IP character, include its description and pass `"images": ["<path>"]`
- No text in the image

### Step 6 — Generate image cards

```bash
python /home/user/workspace/generate_images.py \
  "<article_path>" \
  "<cover_img_path>" \
  "<display_title>" \
  "<kw1>,<kw2>,<kw3>" \
  "<output_zip_path>" \
  [color_scheme]
```

Example:
```bash
python /home/user/workspace/generate_images.py \
  /home/user/workspace/article_topic.txt \
  /home/user/workspace/cover_topic.png \
  "假装上班的人，到底在假装什么？" \
  "失业羞耻感,三十块的体面,身份绑架" \
  /home/user/workspace/images_topic.zip \
  warm
```

The script prints: `完成！共N张图片`

### Step 7 — Inspect quality

Preview the cover card (`01.png`) and last body page using the `read` tool (renders images inline). Check:
- Title text fits without breaking awkwardly
- Keywords display cleanly
- Last page ends with article content, not metadata

If issues are found, adjust title length or keywords and re-run.

### Step 8 — Deliver

Share both files with the user:
```
share_file(cover_<topic>.png)
share_file(images_<topic>.zip)
```

Then briefly summarize: number of cards generated, color theme used, and any tips for platform upload.

## Color Theme Quick Reference

| Theme | Background | Best For |
|-------|-----------|---------|
| `warm` | Warm off-white | General / lifestyle / social commentary |
| `cool_blue` | Cool light blue | Tech / rational / analytical |
| `sage_green` | Soft green | Growth / wellness / nature |
| `dusty_rose` | Muted pink | Relationships / emotion / personal |
| `amber` | Warm amber | Economy / consumption / career |
| `slate` | Blue-grey | Workplace / serious / formal |

See `references/color-schemes.md` for full RGB values.

## Notes

- Article text can be in any language; layout engine handles CJK and Latin equally.
- Optimal article length for card sets: 800–3000 characters. Longer texts produce more pages.
- The `---` separator in `.txt` files cleanly divides body from metadata — use it to keep notes after the article without leaking them into cards.
- Font files are shared across runs; only need to download once per workspace.
