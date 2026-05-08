---
name: inkflow
description: "Turn any article or copywriting into beautiful WeChat / Xiaohongshu image-card sets (图文包). Given article text and a cover image, inkflow generates: (1) a 16:9 AI cover illustration, (2) a 1080×1920 cover card with title + keyword highlights, (3) paginated body cards with clean typography, and (4) ready-to-publish copy with title alternatives. Outputs a ZIP of numbered PNGs plus optional Markdown copy. Supports 6 color themes: warm, cool_blue, sage_green, dusty_rose, amber, slate. Use when the user wants to turn copywriting, essays, or articles into scroll-friendly image cards for WeChat Official Account, Xiaohongshu, or any mobile-first platform."
license: MIT
metadata:
  author: gljx898989
  version: '1.0'
---

# inkflow — Article to Image Cards

Convert any article or copywriting into a beautiful, scroll-ready image card set — cover + paginated body cards — plus ready-to-publish WeChat/Xiaohongshu copy with title alternatives.

## When to Use This Skill

Load this skill when the user:
- Provides article text / copywriting and wants it turned into image cards
- Says things like "做成图文""生成图片流""做成小绿书/小红书样式""帮我排版成图片"
- Wants a WeChat cover image + image set (图文包) for their content
- Also needs the public post body, recommended title, title alternatives, cover copy, and tags
- Has finished writing but can't produce visual image cards themselves

## What You Will Produce

| Output | Description |
|--------|-------------|
| `cover_<topic>.png` | 16:9 AI-generated cover illustration (no text) |
| `images_<topic>.zip` | Numbered PNGs: `01.png` (cover card) + `02–NN.png` (body pages) |
| `publish_copy_<topic>.md` | Ready-to-publish copy: title alternatives, recommended title, cover copy, body text, tags, upload notes |

Card specs: 1080 × 1920 px · Alibaba PuHuiTi font · 6 color themes

## Step-by-Step Instructions

### Step 1 — Gather inputs

Ask the user for (or infer from context):
- **Article text** — the full body copy. May be pasted inline or in a file.
- **Title** — the display title for the cover card (can differ from the article's first line).
- **Title alternatives** — 2–5 candidate public titles when the user asks for posting copy.
- **Keywords / highlights** — 3–5 short phrases shown on the cover card as bullet points.
- **Color theme** — default `warm`. Options: `warm`, `cool_blue`, `sage_green`, `dusty_rose`, `amber`, `slate`. See `references/color-schemes.md` for guidance.
- **Cover image style** — a brief description of what the cover illustration should look like. If not provided, infer from the article topic.
- **Cover copy / tags** (optional) — one short cover lead and platform tags for the Markdown publish copy.
- **IP character** (optional) — if the user has a mascot or character to include in the cover image.

If any of the above are missing and cannot be inferred, ask before proceeding.

### Step 2 — Set up fonts

The script requires Alibaba PuHuiTi. Check if fonts exist:

```bash
ls $HOME/workspace/fonts/Alibaba-PuHuiTi-Regular.ttf 2>/dev/null && echo "found" || echo "missing"
```

If missing, download them:

```bash
mkdir -p $HOME/workspace/fonts
curl -L "https://github.com/alibabadesign/puhuiti/raw/master/fonts/Alibaba%20PuHuiTi%202.0/Alibaba-PuHuiTi-2-55-Regular/Alibaba-PuHuiTi-2-55-Regular.ttf" \
  -o $HOME/workspace/fonts/Alibaba-PuHuiTi-Regular.ttf
curl -L "https://github.com/alibabadesign/puhuiti/raw/master/fonts/Alibaba%20PuHuiTi%202.0/Alibaba-PuHuiTi-2-75-SemiBold/Alibaba-PuHuiTi-2-75-SemiBold.ttf" \
  -o $HOME/workspace/fonts/Alibaba-PuHuiTi-Bold.ttf
```

### Step 3 — Copy the generation script

Copy the bundled script to the workspace:

```bash
cp /path/to/inkflow/scripts/generate_images.py "$HOME/workspace/generate_images.py"
```

### Step 4 — Save the article text

Save the article text to a `.txt` file. The first non-empty line is treated as the title and skipped; body starts from the second non-empty line. Content after a `---` separator line is stripped (metadata zone).

```bash
# Example
cat > $HOME/workspace/article_<topic>.txt << 'EOF'
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
python $HOME/workspace/generate_images.py \
  "<article_path>" \
  "<cover_img_path>" \
  "<display_title>" \
  "<kw1>,<kw2>,<kw3>" \
  "<output_zip_path>" \
  [color_scheme] \
  --copy-md "<publish_copy.md>" \
  --title-options "<title1>|<title2>|<title3>" \
  --cover-copy "<cover lead>" \
  --tags "<tags>" \
  --include-copy-in-zip
```

Example:
```bash
python $HOME/workspace/generate_images.py \
  $HOME/workspace/article_topic.txt \
  $HOME/workspace/cover_topic.png \
  "假装上班的人，到底在假装什么？" \
  "失业羞耻感,三十块的体面,身份绑架" \
  $HOME/workspace/images_topic.zip \
  warm \
  --copy-md $HOME/workspace/publish_copy_topic.md \
  --title-options "假装上班的人，到底在假装什么？|三十块的体面，困住了多少成年人|失业后最难的，不是没收入" \
  --cover-copy "失业后的体面，常常比收入更难处理" \
  --tags "#职场 #成长 #社会观察" \
  --include-copy-in-zip
```

The script prints: `完成！共N张图片` and, when `--copy-md` is set, writes a Markdown publishing copy file. If `--include-copy-in-zip` is set, the Markdown file is also included in the ZIP.


### Optional — Batch Markdown drafts into public publishing bundles

Use the bundled batch script when the user has a folder of Markdown drafts with sections such as `## 备选标题`, `## 封面文案`, `## 正文`, and `## 标签`:

```bash
python scripts/generate_up_distill_cards.py \
  "<draft_folder>" \
  "<avatar.png>" \
  "<output_folder>" \
  --zip "<output_bundle.zip>"
```

This produces:
- one folder per draft
- numbered PNGs (`01-封面.png`, `02-正文.png`, …)
- per-article `公众号发布文案.md`
- root-level `公众号发布文案合集.md`
- root-level `生成清单.csv` with title alternatives and copy paths

For public-facing outputs, keep source metadata out of filenames, manifests, images, and copy. Present the work as original/personal study notes unless the user explicitly asks otherwise.

### Step 7 — Inspect quality

Preview the cover card (`01.png`) and last body page using the `read` tool (renders images inline). Check:
- Title text fits without breaking awkwardly
- Keywords display cleanly
- Last page ends with article content, not metadata

If issues are found, adjust title length or keywords and re-run.

### Step 8 — Deliver

Share the generated files with the user:
```
share_file(cover_<topic>.png)
share_file(images_<topic>.zip)
share_file(publish_copy_<topic>.md)  # when generated
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
- When the user asks for WeChat Official Account publishing, deliver both the PNG card set and Markdown copy (recommended title, alternatives, body, tags).
- The `---` separator in `.txt` files cleanly divides body from metadata — use it to keep notes after the article without leaking them into cards.
- Font files are shared across runs; only need to download once per workspace.
