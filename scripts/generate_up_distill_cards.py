#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Batch render study-note Markdown drafts into public PNG + WeChat copy bundles.

This helper is intentionally conservative about public wording: source metadata can
exist in the drafts, but generated PNGs, filenames, manifests, and copy files are
written as original personal study notes.
"""
from __future__ import annotations

import argparse
import csv
import re
import zipfile
from pathlib import Path
from typing import Dict, List, Tuple

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

W, H = 1080, 1920
MARGIN_X = 82

FORBIDDEN_PUBLIC_TERMS = [
    'UP主深度蒸馏', 'UP主蒸馏', 'UP主', '来源 UP', '来源UP', '原文档', '内部来源', '内部主题',
    '长视频观点', '蒸馏', '宏哥说管理', 'CLS同学', '家卫老师', '峰video', '赏味不足', '万物周期研究所',
]

THEMES = {
    '组织管理与职场成长': {'bg': (242, 244, 248), 'ink': (31, 38, 54), 'muted': (93, 101, 120), 'accent': (63, 96, 168), 'soft': (222, 230, 247)},
    '商业思维与现实决策': {'bg': (250, 245, 232), 'ink': (52, 39, 24), 'muted': (112, 86, 50), 'accent': (190, 125, 36), 'soft': (243, 229, 197)},
    '教育与亲子沟通': {'bg': (247, 240, 240), 'ink': (58, 35, 42), 'muted': (116, 75, 84), 'accent': (174, 83, 104), 'soft': (240, 218, 222)},
    '个人成长与情绪认知': {'bg': (240, 245, 238), 'ink': (36, 48, 38), 'muted': (78, 97, 76), 'accent': (76, 132, 88), 'soft': (219, 235, 216)},
    'default': {'bg': (248, 244, 236), 'ink': (42, 36, 31), 'muted': (92, 78, 66), 'accent': (66, 122, 118), 'soft': (224, 238, 235)},
}


def pick_font(paths: List[str]) -> str:
    for p in paths:
        if Path(p).exists():
            return p
    raise FileNotFoundError('No usable CJK font found. Pass --font-regular/--font-bold.')


def make_fonts(font_regular: str | None, font_bold: str | None):
    regular = font_regular or pick_font([
        '/mnt/c/Windows/Fonts/msyh.ttc',
        '/mnt/c/Windows/Fonts/simhei.ttf',
        str(Path.home() / 'workspace/fonts/Alibaba-PuHuiTi-Regular.ttf'),
    ])
    bold = font_bold or pick_font([
        '/mnt/c/Windows/Fonts/msyhbd.ttc',
        '/mnt/c/Windows/Fonts/simhei.ttf',
        str(Path.home() / 'workspace/fonts/Alibaba-PuHuiTi-Bold.ttf'),
    ])
    return {
        'title': ImageFont.truetype(bold, 88),
        'subtitle': ImageFont.truetype(regular, 48),
        'h1': ImageFont.truetype(bold, 58),
        'body': ImageFont.truetype(regular, 45),
        'body_b': ImageFont.truetype(bold, 45),
        'small': ImageFont.truetype(regular, 32),
        'small_b': ImageFont.truetype(bold, 34),
        'page': ImageFont.truetype(regular, 28),
    }


def text_w(draw, text, fnt):
    b = draw.textbbox((0, 0), text, font=fnt)
    return b[2] - b[0]


def wrap_cjk(draw, text: str, fnt, max_width: int) -> List[str]:
    text = re.sub(r'`([^`]+)`', r'\1', text.strip())
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    if not text:
        return ['']
    out, cur = [], ''
    for ch in text:
        test = cur + ch
        if text_w(draw, test, fnt) <= max_width or not cur:
            cur = test
        else:
            out.append(cur)
            cur = ch
    if cur:
        out.append(cur)
    return out


def smart_wrap_title(draw, text: str, fnt, max_width: int, max_lines: int = 4) -> List[str]:
    """Wrap large cover titles with better Chinese reading rhythm.

    The generic CJK wrapper is greedy and can split words awkwardly at line ends
    (e.g. 系/统, 常/常). For cover titles, choose line breaks globally so all
    lines fit while preferring punctuation/phrase boundaries and avoiding lone
    repeated characters or common two-character words being split.
    """
    text = re.sub(r'`([^`]+)`', r'\1', text.strip())
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    if not text:
        return ['']
    n = len(text)
    # Candidate break positions are character offsets 1..n-1. Prefer breaks
    # after punctuation and before common conjunction/adverb starts.
    phrase_starts = set('越常是而因但不先别要把才往真看做从为')
    bad_pairs = {'系统', '常常', '问题', '组织', '企业', '公司', '孩子', '财富', '自由', '投资', '经济', '普通', '能力', '制度', '决定', '焦虑', '机会'}

    from functools import lru_cache

    @lru_cache(None)
    def width(s):
        return text_w(draw, s, fnt)

    @lru_cache(None)
    def best(start: int, lines_left: int):
        if start >= n:
            return (0, [])
        tail = text[start:]
        if width(tail) <= max_width:
            return (0, [tail])
        if lines_left <= 1:
            return (10**9, [tail])

        best_score, best_lines = 10**9, None
        for end in range(start + 1, n):
            seg = text[start:end]
            if width(seg) > max_width:
                break
            # Need at least one char for the remainder.
            if end >= n:
                continue
            score = 0
            line_len = end - start
            remaining = n - end
            # Prefer reasonably full lines but avoid pushing a single word/char.
            fullness = width(seg) / max_width
            score += int((1 - fullness) * 80)
            if text[end - 1] in '，、；：。？！!?':
                score -= 60
            if text[end] in phrase_starts:
                score -= 18
            if line_len <= 3:
                score += 80
            if remaining <= 2:
                score += 100
            # Avoid splitting common two-char words and duplicated words.
            pair = text[end-1:end+1]
            if pair in bad_pairs:
                score += 180
            if end - 1 >= 0 and end < n and text[end - 1] == text[end]:
                score += 180
            # Avoid orphan punctuation at the beginning of the next line.
            if text[end] in '，、；：。？！!?':
                score += 200
            child_score, child_lines = best(end, lines_left - 1)
            total = score + child_score
            if total < best_score:
                best_score, best_lines = total, [seg] + child_lines
        if best_lines is None:
            return (10**9, wrap_cjk(draw, text[start:], fnt, max_width)[:lines_left])
        return (best_score, best_lines)

    return best(0, max_lines)[1][:max_lines]


def md_section(text: str, name: str) -> str:
    m = re.search(rf'^##\s+{re.escape(name)}\s*$([\s\S]*?)(?=^##\s+|\Z)', text, flags=re.M)
    return m.group(1).strip() if m else ''


def meta_value(text: str, key: str) -> str:
    m = re.search(rf'^-\s*{re.escape(key)}：\s*(.+?)\s*$', text, flags=re.M)
    return m.group(1).strip() if m else ''


def public_category(theme_name: str) -> str:
    return {
        '组织管理与职场成长': '职场思考',
        '教育与亲子沟通': '教育观察',
        '教育亲子': '教育观察',
        '个人成长与情绪认知': '自我管理',
        '职场沟通与自我管理': '自我管理',
        '宏观经济与趋势判断': '趋势观察',
        '投资周期与财富认知': '财富认知',
        '商业思维与现实决策': '现实决策',
    }.get(theme_name, '思考笔记')


def sanitize_public_text(text: str) -> str:
    replacements = {
        'UP主深度蒸馏': '学习笔记', 'UP主蒸馏': '学习笔记', 'UP主': '作者',
        '来源 UP': '参考信息', '来源UP': '参考信息', '原文档': '参考资料',
        '长视频观点': '思考观点', '蒸馏': '整理',
        '宏哥说管理': '', 'CLS同学': '', '家卫老师': '', '峰video': '', '赏味不足': '', '万物周期研究所': '',
    }
    out = text
    for old, new in replacements.items():
        out = out.replace(old, new)
    return out.strip()


def assert_public_safe(text: str, where: str):
    hits = [term for term in FORBIDDEN_PUBLIC_TERMS if term in text]
    if hits:
        raise RuntimeError(f'Public output contains forbidden terms at {where}: {hits}')


def parse_draft(path: Path) -> Dict:
    raw = path.read_text(encoding='utf-8')
    first = re.search(r'^#\s+(.+?)\s*$', raw, flags=re.M)
    h1 = first.group(1).strip() if first else path.stem
    titles = []
    for line in md_section(raw, '备选标题').splitlines():
        m = re.match(r'\s*\d+[.、]\s*(.+)', line)
        if m:
            titles.append(sanitize_public_text(m.group(1).strip()))
    title = titles[0] if titles else sanitize_public_text(re.sub(r'^小红书草稿[:：]\s*', '', h1))
    cover_copy = sanitize_public_text(next((x.strip() for x in md_section(raw, '封面文案').splitlines() if x.strip()), ''))
    body = sanitize_public_text(md_section(raw, '正文'))
    tags = sanitize_public_text(' '.join(x.strip() for x in md_section(raw, '标签').splitlines() if x.strip()))
    theme = meta_value(raw, '主题分类') or 'default'
    return {'path': path, 'title': title, 'titles': titles, 'cover_copy': cover_copy, 'body': body, 'tags': tags, 'theme': theme, 'public_category': public_category(theme)}


def split_body_blocks(body: str) -> List[Tuple[str, str]]:
    blocks = []
    paras = [p.strip() for p in re.split(r'\n\s*\n', body.strip()) if p.strip()]
    for p in paras:
        lines = [ln.strip() for ln in p.splitlines() if ln.strip()]
        if all(re.match(r'^(\d+[.、]|[-•])\s+', ln) for ln in lines) and len(lines) > 1:
            for ln in lines:
                blocks.append(('bullet', re.sub(r'^[-•]\s+', '• ', ln)))
        elif len(lines) == 1 and re.match(r'^(\d+[.、]|[-•])\s+', lines[0]):
            blocks.append(('bullet', re.sub(r'^[-•]\s+', '• ', lines[0])))
        else:
            blocks.append(('para', ' '.join(lines)))
    return blocks


def make_avatar(path: Path, size: int) -> Image.Image:
    av = Image.open(path).convert('RGBA')
    av = ImageOps.fit(av, (size, size), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
    mask = Image.new('L', (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size-1, size-1), fill=255)
    out = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    out.paste(av, (0, 0), mask)
    return out


def make_bg(theme):
    img = Image.new('RGB', (W, H), theme['bg'])
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.ellipse((-210, -150, 490, 480), fill=theme['soft'] + (165,))
    d.ellipse((700, 80, 1260, 650), fill=theme['soft'] + (120,))
    d.ellipse((720, 1380, 1320, 2020), fill=theme['soft'] + (105,))
    return Image.alpha_composite(img.convert('RGBA'), layer.filter(ImageFilter.GaussianBlur(30))).convert('RGB')


def draw_round_rect(draw, xy, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def draw_header(draw, img, item, theme, fonts, avatar, page_label='思考笔记'):
    av = make_avatar(avatar, 74)
    img.paste(av, (MARGIN_X, 52), av)
    draw.text((MARGIN_X + 94, 57), '个人思考笔记', fill=theme['ink'], font=fonts['small_b'])
    draw.text((MARGIN_X + 94, 99), item.get('public_category') or '思考笔记', fill=theme['muted'], font=fonts['page'])
    tw = text_w(draw, page_label, fonts['page'])
    draw_round_rect(draw, (W - MARGIN_X - tw - 44, 66, W - MARGIN_X, 110), 22, theme['soft'])
    draw.text((W - MARGIN_X - tw - 22, 74), page_label, fill=theme['accent'], font=fonts['page'])


def draw_footer(draw, page, total, theme, fonts):
    draw.line((MARGIN_X, H-118, W-MARGIN_X, H-118), fill=theme['soft'], width=3)
    txt = f'{page:02d} / {total:02d}'
    draw.text(((W-text_w(draw, txt, fonts['page']))//2, H-82), txt, fill=theme['muted'], font=fonts['page'])


def paginate(draw, blocks, fonts, max_h=1420):
    pages, cur, y = [], [], 0
    for typ, txt in blocks:
        fnt = fonts['body_b'] if typ == 'bullet' else fonts['body']
        lines = wrap_cjk(draw, txt, fnt, W - 2*MARGIN_X)
        block_h = len(lines) * 68 + 34
        if y + block_h > max_h and cur:
            pages.append(cur)
            cur, y = [], 0
        cur.append((typ, txt, lines))
        y += block_h
    if cur:
        pages.append(cur)
    return pages


def create_cover(item, theme, fonts, avatar, out_path: Path, total: int):
    img = make_bg(theme)
    draw = ImageDraw.Draw(img)
    draw_header(draw, img, item, theme, fonts, avatar, '原创笔记')
    y = 238
    cat = item.get('public_category') or '思考笔记'
    cw = text_w(draw, cat, fonts['small_b'])
    draw_round_rect(draw, (MARGIN_X, y, MARGIN_X+cw+56, y+58), 29, theme['accent'])
    draw.text((MARGIN_X+28, y+12), cat, fill=(255,255,255), font=fonts['small_b'])
    y += 105
    for line in smart_wrap_title(draw, item['title'], fonts['title'], W - 2*MARGIN_X, max_lines=4):
        draw.text((MARGIN_X, y), line, fill=theme['ink'], font=fonts['title'])
        y += 114
    y += 18
    if item['cover_copy']:
        for line in wrap_cjk(draw, item['cover_copy'], fonts['subtitle'], W - 2*MARGIN_X):
            draw.text((MARGIN_X, y), line, fill=theme['accent'], font=fonts['subtitle'])
            y += 72
    y += 38
    card_top = y
    draw_round_rect(draw, (MARGIN_X, card_top, W-MARGIN_X, card_top+520), 48, (255,255,255), outline=theme['soft'], width=4)
    av = make_avatar(avatar, 260)
    img.paste(av, ((W-260)//2, card_top+64), av)
    lead = '把复杂问题，整理成可行动的思考卡片'
    hint = '内页包含：核心判断 / 使用步骤 / 适用边界'
    draw.text(((W-text_w(draw, lead, fonts['small_b']))//2, card_top+362), lead, fill=theme['ink'], font=fonts['small_b'])
    draw.text(((W-text_w(draw, hint, fonts['small']))//2, card_top+414), hint, fill=theme['muted'], font=fonts['small'])
    if item['tags']:
        ty = H - 235
        for line in wrap_cjk(draw, item['tags'], fonts['small'], W-2*MARGIN_X)[:2]:
            draw.text((MARGIN_X, ty), line, fill=theme['muted'], font=fonts['small'])
            ty += 46
    draw_footer(draw, 1, total, theme, fonts)
    img.save(out_path, quality=96)


def create_body_page(item, theme, fonts, avatar, page_blocks, out_path: Path, page_num: int, total: int):
    img = make_bg(theme)
    draw = ImageDraw.Draw(img)
    draw_header(draw, img, item, theme, fonts, avatar, item.get('public_category') or '学习笔记')
    y = 184
    for line in wrap_cjk(draw, item['title'], fonts['h1'], W - 2*MARGIN_X)[:2]:
        draw.text((MARGIN_X, y), line, fill=theme['ink'], font=fonts['h1'])
        y += 74
    y += 28
    draw.line((MARGIN_X, y, W-MARGIN_X, y), fill=theme['accent'], width=5)
    y += 54
    for typ, txt, lines in page_blocks:
        if typ == 'bullet':
            block_h = len(lines) * 68 + 34
            draw_round_rect(draw, (MARGIN_X-20, y-18, W-MARGIN_X+20, y+block_h-8), 26, (255,255,255), outline=theme['soft'], width=2)
            fnt = fonts['body_b']
        else:
            fnt = fonts['body']
        for line in lines:
            draw.text((MARGIN_X, y), line, fill=theme['ink'], font=fnt)
            y += 68
        y += 34
    if page_num == total and item['tags']:
        draw.text((MARGIN_X, min(y + 15, H - 260)), item['tags'], fill=theme['muted'], font=fonts['small'])
    draw_footer(draw, page_num, total, theme, fonts)
    img.save(out_path, quality=96)


def safe_name(path: Path, title: str) -> str:
    prefix = re.match(r'^(\d+)', path.stem)
    name = re.sub(r'[\\/:*?"<>|\s]+', '-', sanitize_public_text(title)).strip('-')
    return f'{prefix.group(1) if prefix else "00"}-{name[:38]}'


def build_publish_copy(item: Dict, folder: Path, png_count: int) -> str:
    title_lines = '\n'.join(f'{i}. {t}' for i, t in enumerate(item['titles'] or [item['title']], 1))
    png_lines = '\n'.join(f'- {p.name}' for p in sorted(folder.glob('*.png')))
    content = f"""# {item['title']}

## 标题备选

{title_lines}

## 推荐标题

{item['title']}

## 封面文案

{item['cover_copy']}

## 正文

{item['body']}

## 标签

{item['tags']}

## 配图文件

共 {png_count} 张 PNG，建议按文件名顺序上传到公众号图文正文中。

{png_lines}
"""
    content = sanitize_public_text(content)
    assert_public_safe(content, f'{folder}/公众号发布文案.md')
    return content


def render_one(item: Dict, out_dir: Path, fonts, avatar: Path) -> Dict:
    theme = THEMES.get(item['theme'], THEMES['default'])
    dummy = ImageDraw.Draw(Image.new('RGB', (W, H)))
    pages = paginate(dummy, split_body_blocks(item['body']), fonts)
    total = 1 + len(pages)
    folder = out_dir / safe_name(item['path'], item['title'])
    folder.mkdir(parents=True, exist_ok=True)
    for old in folder.glob('*.png'):
        old.unlink()
    create_cover(item, theme, fonts, avatar, folder / '01-封面.png', total)
    for i, page in enumerate(pages, start=2):
        create_body_page(item, theme, fonts, avatar, page, folder / f'{i:02d}-正文.png', i, total)
    png_count = len(list(folder.glob('*.png')))
    copy_path = folder / '公众号发布文案.md'
    copy_path.write_text(build_publish_copy(item, folder, png_count), encoding='utf-8')
    return {'folder': folder, 'title': item['title'], 'title_options': ' / '.join(item['titles'] or [item['title']]), 'public_category': item['public_category'], 'pngs': png_count, 'copy_path': copy_path}


def build_master_copy(rows: List[Dict], out_dir: Path) -> str:
    parts = ['# 公众号发布文案合集', '', '说明：每篇均配有对应 PNG 图文卡片，正文可直接复制到公众号后台；图片按文件名顺序插入。', '']
    for i, r in enumerate(rows, 1):
        rel_copy = r['copy_path'].relative_to(out_dir)
        parts.extend([f'## {i:02d}. {r["title"]}', '', f'- 公开分类：{r["public_category"]}', f'- PNG 张数：{r["pngs"]}', f'- 发布文案：{rel_copy}', f'- 标题备选：{r["title_options"]}', ''])
        copy_text = r['copy_path'].read_text(encoding='utf-8')
        body = re.search(r'^## 正文\s*\n([\s\S]*?)(?=^##\s+标签|\Z)', copy_text, flags=re.M)
        tags = re.search(r'^## 标签\s*\n([\s\S]*?)(?=^##\s+配图文件|\Z)', copy_text, flags=re.M)
        parts.extend(['### 正文', '', body.group(1).strip() if body else '', '', '### 标签', '', tags.group(1).strip() if tags else '', ''])
    content = sanitize_public_text('\n'.join(parts).strip() + '\n')
    assert_public_safe(content, '公众号发布文案合集.md')
    return content


def main():
    ap = argparse.ArgumentParser(description='Render public study-note PNG cards plus WeChat copy from Markdown drafts.')
    ap.add_argument('src_dir', type=Path, help='Folder containing Markdown drafts')
    ap.add_argument('avatar', type=Path, help='Avatar image used in the card header/cover')
    ap.add_argument('out_dir', type=Path, help='Output folder')
    ap.add_argument('--zip', dest='zip_path', type=Path, default=None, help='Optional ZIP path for the whole output')
    ap.add_argument('--font-regular', default=None)
    ap.add_argument('--font-bold', default=None)
    args = ap.parse_args()

    fonts = make_fonts(args.font_regular, args.font_bold)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for p in sorted(args.src_dir.glob('*.md'), key=lambda x: x.name):
        item = parse_draft(p)
        if not item['body']:
            raise RuntimeError(f'No 正文 section: {p}')
        rows.append(render_one(item, args.out_dir, fonts, args.avatar))

    master = args.out_dir / '公众号发布文案合集.md'
    master.write_text(build_master_copy(rows, args.out_dir), encoding='utf-8')
    index = args.out_dir / '生成清单.csv'
    with index.open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=['序号','标题','标题备选','公开分类','PNG张数','发布文案','输出文件夹'])
        w.writeheader()
        for i, r in enumerate(rows, 1):
            w.writerow({'序号': i, '标题': r['title'], '标题备选': r['title_options'], '公开分类': r['public_category'], 'PNG张数': r['pngs'], '发布文案': str(r['copy_path'].relative_to(args.out_dir)), '输出文件夹': r['folder'].name})
    assert_public_safe(index.read_text(encoding='utf-8-sig'), str(index))

    if args.zip_path:
        if args.zip_path.exists():
            args.zip_path.unlink()
        with zipfile.ZipFile(args.zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
            for p in sorted(args.out_dir.rglob('*')):
                if p.is_file():
                    z.write(p, p.relative_to(args.out_dir.parent))

    print(f'完成：{len(rows)}篇')
    print(f'总PNG：{sum(r["pngs"] for r in rows)}张')
    print(f'发布文案：{len(rows)}份 + 合集1份')
    print(f'输出目录：{args.out_dir}')
    if args.zip_path:
        print(f'合集ZIP：{args.zip_path}')


if __name__ == '__main__':
    main()
