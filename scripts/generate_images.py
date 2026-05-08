#!/usr/bin/env python3
"""
inkflow — Article to Image Cards
https://github.com/Ficere/inkflow

Converts a plain-text article + cover image into a ZIP of numbered PNGs:
  01.png  — cover card (title + keywords)
  02.png+ — paginated body cards

Usage:
  python generate_images.py <article_path> <cover_img_path> <title> \
      <highlights_comma_sep> <output_zip> [color_scheme]

Color schemes: warm (default), cool_blue, sage_green, dusty_rose, amber, slate

Font requirement:
  /home/user/workspace/fonts/Alibaba-PuHuiTi-Regular.ttf
  /home/user/workspace/fonts/Alibaba-PuHuiTi-Bold.ttf
  (see SKILL.md Step 2 for download instructions)
"""

import os
import sys
import zipfile
import re
from PIL import Image, ImageDraw, ImageFont

# ─── Canvas ──────────────────────────────────────────────────────────────────
IMG_WIDTH = 1080
IMG_HEIGHT = 1920

MARGIN_X = 80
MARGIN_TOP = 110
MARGIN_BOTTOM = 130
BODY_FONT_SIZE = 52
LINE_SPACING = 1.65
PARA_SPACING = 44

# ─── Fonts ───────────────────────────────────────────────────────────────────
FONTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "..", "..", "fonts")
# Fallback to workspace/fonts if running from workspace root
if not os.path.isdir(FONTS_DIR):
    FONTS_DIR = "/home/user/workspace/fonts"

SANS_FONT      = os.path.join(FONTS_DIR, "Alibaba-PuHuiTi-Regular.ttf")
SANS_BOLD_FONT = os.path.join(FONTS_DIR, "Alibaba-PuHuiTi-Bold.ttf")

# ─── Color Schemes ───────────────────────────────────────────────────────────
COLOR_SCHEMES = {
    "warm": {
        "bg":       (248, 244, 236),
        "text":     (42,  36,  31),
        "title":    (20,  42,  48),
        "subtitle": (70,  60,  52),
        "accent":   (66,  122, 118),
        "page_num": (130, 120, 110),
    },
    "cool_blue": {
        "bg":       (235, 242, 250),
        "text":     (30,  36,  48),
        "title":    (18,  32,  60),
        "subtitle": (50,  60,  80),
        "accent":   (52,  100, 168),
        "page_num": (120, 130, 150),
    },
    "sage_green": {
        "bg":       (240, 245, 238),
        "text":     (36,  42,  34),
        "title":    (24,  48,  32),
        "subtitle": (55,  68,  52),
        "accent":   (76,  132, 88),
        "page_num": (115, 128, 112),
    },
    "dusty_rose": {
        "bg":       (248, 240, 240),
        "text":     (48,  32,  36),
        "title":    (60,  20,  30),
        "subtitle": (80,  50,  58),
        "accent":   (168, 82,  100),
        "page_num": (150, 120, 128),
    },
    "amber": {
        "bg":       (250, 245, 232),
        "text":     (48,  38,  24),
        "title":    (60,  36,  10),
        "subtitle": (80,  62,  38),
        "accent":   (188, 132, 48),
        "page_num": (150, 135, 108),
    },
    "slate": {
        "bg":       (238, 240, 244),
        "text":     (36,  38,  44),
        "title":    (24,  28,  42),
        "subtitle": (58,  62,  72),
        "accent":   (88,  98,  128),
        "page_num": (120, 125, 138),
    },
}

DEFAULT_SCHEME = COLOR_SCHEMES["warm"]


# ─── Font Loader ─────────────────────────────────────────────────────────────
def load_fonts():
    for path in [SANS_FONT, SANS_BOLD_FONT]:
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"Font not found: {path}\n"
                "Download Alibaba PuHuiTi — see SKILL.md Step 2."
            )
    return {
        "body":           ImageFont.truetype(SANS_FONT,      BODY_FONT_SIZE),
        "cover_title":    ImageFont.truetype(SANS_BOLD_FONT, 100),
        "cover_subtitle": ImageFont.truetype(SANS_FONT,      42),
        "cover_label":    ImageFont.truetype(SANS_FONT,      36),
        "page_num":       ImageFont.truetype(SANS_FONT,      28),
    }


# ─── Text Utilities ───────────────────────────────────────────────────────────
def split_lines(draw, text, font, max_width):
    """Split a single string into lines that fit within max_width."""
    lines, cur = [], ""
    for ch in text:
        test = cur + ch
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] > max_width and cur:
            lines.append(cur)
            cur = ch
        else:
            cur = test
    if cur:
        lines.append(cur)
    return lines


def wrap_text(draw, text, font, max_width):
    """Wrap multi-paragraph text, preserving blank lines as paragraph breaks."""
    lines = []
    for paragraph in text.split("\n"):
        if not paragraph.strip():
            lines.append("")
            continue
        current_line = ""
        for char in paragraph:
            test_line = current_line + char
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] > max_width:
                if current_line:
                    lines.append(current_line)
                current_line = char
            else:
                current_line = test_line
        if current_line:
            lines.append(current_line)
    return lines


# ─── Cover Card ──────────────────────────────────────────────────────────────
def create_cover_page(cover_img_path, title, highlights, fonts, output_path,
                      scheme=None):
    """Generate 01.png: cover illustration + title + keyword bullets."""
    if scheme is None:
        scheme = DEFAULT_SCHEME

    BG_COLOR      = scheme["bg"]
    TITLE_COLOR   = scheme["title"]
    SUBTITLE_COLOR = scheme["subtitle"]
    ACCENT_COLOR  = scheme["accent"]

    img  = Image.new("RGB", (IMG_WIDTH, IMG_HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    title_font    = fonts["cover_title"]
    label_font    = fonts["cover_label"]
    subtitle_font = fonts["cover_subtitle"]
    max_w         = IMG_WIDTH - 2 * MARGIN_X

    # Measure title block
    title_lines  = split_lines(draw, title, title_font, max_w)
    title_line_h = draw.textbbox((0, 0), "测", font=title_font)
    title_h      = len(title_lines) * int((title_line_h[3] - title_line_h[1]) * 1.2)

    # Measure highlight block
    hl_lines = [split_lines(draw, f"• {h}", subtitle_font, max_w - 20)
                for h in highlights]
    alt_h = sum(len(ls) * 62 + 12 for ls in hl_lines)

    text_zone_h = 60 + title_h + 40 + 4 + 55 + 65 + alt_h + 80
    cover_h     = IMG_HEIGHT - text_zone_h

    # Paste and crop cover image
    cover   = Image.open(cover_img_path)
    ratio   = max(IMG_WIDTH / cover.width, cover_h / cover.height)
    new_w   = int(cover.width  * ratio)
    new_h   = int(cover.height * ratio)
    cover   = cover.resize((new_w, new_h), Image.LANCZOS)
    left    = (new_w - IMG_WIDTH) // 2
    top     = (new_h - cover_h)   // 2
    cover   = cover.crop((left, top, left + IMG_WIDTH, top + cover_h))
    img.paste(cover, (0, 0))

    # Gradient fade into background
    fade_h = 180
    for y in range(max(0, cover_h - fade_h), cover_h):
        alpha = int(255 * (y - (cover_h - fade_h)) / fade_h)
        t = alpha / 255
        for x in range(IMG_WIDTH):
            r, g, b = img.getpixel((x, y))
            img.putpixel((x, y), (
                int(r * (1 - t) + BG_COLOR[0] * t),
                int(g * (1 - t) + BG_COLOR[1] * t),
                int(b * (1 - t) + BG_COLOR[2] * t),
            ))

    # Title
    y_pos = cover_h + 55
    for tl in title_lines:
        bbox = draw.textbbox((0, 0), tl, font=title_font)
        x    = (IMG_WIDTH - (bbox[2] - bbox[0])) // 2
        draw.text((x, y_pos), tl, fill=TITLE_COLOR, font=title_font)
        y_pos += int((bbox[3] - bbox[1]) * 1.18)
    y_pos += 42

    # Divider
    draw.line([(MARGIN_X + 40, y_pos),
               (IMG_WIDTH - MARGIN_X - 40, y_pos)], fill=ACCENT_COLOR, width=4)
    y_pos += 55

    # Keyword label
    draw.text((MARGIN_X, y_pos), "关键词", fill=TITLE_COLOR, font=label_font)
    y_pos += 65

    # Keywords
    for lines in hl_lines:
        for line in lines:
            draw.text((MARGIN_X + 10, y_pos), line,
                      fill=SUBTITLE_COLOR, font=subtitle_font)
            y_pos += 62
        y_pos += 12

    img.save(output_path, quality=95)


# ─── Body Pages ──────────────────────────────────────────────────────────────
def create_text_pages(article_text, fonts, output_dir, start_num=2, scheme=None):
    """Generate paginated body card images (02.png, 03.png, …)."""
    if scheme is None:
        scheme = DEFAULT_SCHEME

    BG_COLOR      = scheme["bg"]
    TEXT_COLOR    = scheme["text"]
    ACCENT_COLOR  = scheme["accent"]
    PAGE_NUM_COLOR = scheme["page_num"]

    body_font    = fonts["body"]
    page_num_font = fonts["page_num"]

    tmp_img  = Image.new("RGB", (IMG_WIDTH, IMG_HEIGHT), BG_COLOR)
    tmp_draw = ImageDraw.Draw(tmp_img)
    max_w    = IMG_WIDTH - 2 * MARGIN_X
    lh       = int(BODY_FONT_SIZE * LINE_SPACING)
    all_lines = wrap_text(tmp_draw, article_text, body_font, max_w)

    usable_h   = IMG_HEIGHT - MARGIN_TOP - MARGIN_BOTTOM
    lines_per_page = usable_h // lh

    pages, current_page, current_lines = [], [], 0
    for line in all_lines:
        if line == "":
            extra = PARA_SPACING / lh
            if current_lines + extra + 1 > lines_per_page and current_page:
                pages.append(current_page)
                current_page, current_lines = [], 0
            else:
                current_page.append(("gap", ""))
                current_lines += extra
        else:
            if current_lines + 1 > lines_per_page and current_page:
                pages.append(current_page)
                current_page, current_lines = [], 0
            current_page.append(("text", line))
            current_lines += 1
    if current_page:
        pages.append(current_page)

    total = len(pages)
    for idx, page_lines in enumerate(pages):
        img  = Image.new("RGB", (IMG_WIDTH, IMG_HEIGHT), BG_COLOR)
        draw = ImageDraw.Draw(img)

        draw.line([(MARGIN_X, 56), (IMG_WIDTH - MARGIN_X, 56)],
                  fill=ACCENT_COLOR, width=4)

        y = MARGIN_TOP
        for line_type, line_text in page_lines:
            if line_type == "gap":
                y += PARA_SPACING
            else:
                draw.text((MARGIN_X, y), line_text, fill=TEXT_COLOR, font=body_font)
                y += lh

        page_text = f"{idx + 1} / {total}"
        bbox = draw.textbbox((0, 0), page_text, font=page_num_font)
        px   = (IMG_WIDTH - (bbox[2] - bbox[0])) // 2
        draw.text((px, IMG_HEIGHT - 72), page_text,
                  fill=PAGE_NUM_COLOR, font=page_num_font)

        img.save(os.path.join(output_dir, f"{start_num + idx:02d}.png"), quality=95)

    return total


# ─── Main Entry ──────────────────────────────────────────────────────────────
def create_article_zip(article_path, cover_img_path, title, highlights,
                       output_zip, color_scheme="warm"):
    """
    Full pipeline: read article → render cover card + body pages → ZIP.

    Returns total page count (including cover).
    """
    with open(article_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Skip first non-empty line (title) and use remainder as body
    body_start = 0
    for i, line in enumerate(lines):
        if i == 0:
            continue
        if line.strip():
            body_start = i
            break
    article_text = "".join(lines[body_start:]).strip()

    # Strip trailing metadata after '---' separator
    article_text = re.split(r"\n---\s*\n", article_text)[0].strip()

    scheme  = COLOR_SCHEMES.get(color_scheme, DEFAULT_SCHEME)
    tmp_dir = "/home/user/workspace/tmp_inkflow_images"
    os.makedirs(tmp_dir, exist_ok=True)
    for fname in os.listdir(tmp_dir):
        os.remove(os.path.join(tmp_dir, fname))

    fonts = load_fonts()
    create_cover_page(cover_img_path, title, highlights, fonts,
                      os.path.join(tmp_dir, "01.png"), scheme)
    num_body = create_text_pages(article_text, fonts, tmp_dir,
                                 start_num=2, scheme=scheme)

    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for fname in sorted(os.listdir(tmp_dir)):
            zf.write(os.path.join(tmp_dir, fname), fname)

    return num_body + 1  # body pages + cover


if __name__ == "__main__":
    if len(sys.argv) < 6:
        print(
            "Usage: python generate_images.py "
            "<article_path> <cover_img_path> <title> "
            "<highlights_comma_sep> <output_zip> [color_scheme]"
        )
        sys.exit(1)

    article_path   = sys.argv[1]
    cover_img_path = sys.argv[2]
    title          = sys.argv[3]
    highlights     = [h.strip() for h in sys.argv[4].split(",")]
    output_zip     = sys.argv[5]
    color_scheme   = sys.argv[6] if len(sys.argv) > 6 else "warm"

    total = create_article_zip(
        article_path, cover_img_path, title,
        highlights, output_zip, color_scheme
    )
    print(f"完成！共{total}张图片")
