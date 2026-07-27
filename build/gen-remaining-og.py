#!/usr/bin/env python3
"""Generate OG images for remaining template pages (hubs, utility, chess).
Reads titles and descriptions from data/heroes.json and data/meta.json."""

import json, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

heroes = json.load(open('data/heroes.json'))
meta = json.load(open('data/meta.json'))

WIDTH, HEIGHT = 1200, 630
BG = (10, 13, 42)

# Section colours — from navbar accents
MODS = (230, 50, 50)         # #e63232
ENGINES = (6, 182, 212)      # #06b6d4
GAMES = (232, 169, 26)       # #e8a91a
TOOLS = (58, 153, 40)        # #3a9928
DEVELOPERS = (139, 92, 246)  # #8b5cf6
NEWS = (225, 29, 137)        # #e11d89
ABOUT = (111, 181, 255)      # #6fb5ff

# Legacy aliases
GLOW_BLUE = ABOUT
GREEN = TOOLS
BLUE = (12, 79, 141)


def load_font(size, bold=False):
    paths = [
        '/System/Library/Fonts/Supplemental/Helvetica Neue.ttc',
        '/System/Library/Fonts/Helvetica.ttc',
    ]
    for p in paths:
        try:
            idx = 4 if bold else 0
            return ImageFont.truetype(p, size, index=idx)
        except (OSError, IndexError):
            try:
                return ImageFont.truetype(p, size, index=0)
            except OSError:
                continue
    return ImageFont.load_default()


def base_image(accent_color=GLOW_BLUE, glow_x=850, glow_y=300):
    img = Image.new('RGBA', (WIDTH, HEIGHT), (*BG, 255))
    # Glow
    glow = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse(
        [glow_x - 300, glow_y - 300, glow_x + 300, glow_y + 300],
        fill=(*accent_color, 45)
    )
    glow = glow.filter(ImageFilter.GaussianBlur(radius=100))
    img = Image.alpha_composite(img, glow)
    # Logo
    logo_src = Image.open('img/moddable-logo-white.png').convert('RGBA')
    lh = 28
    lw = int(logo_src.width * lh / logo_src.height)
    logo = logo_src.resize((lw, lh), Image.LANCZOS)
    img.paste(logo, (80, 40), logo)
    return img


def add_text(img, eyebrow, title, subtitle='', accent=GLOW_BLUE):
    draw = ImageDraw.Draw(img)
    if eyebrow:
        draw.text((80, 220), eyebrow, fill=(*accent, 255), font=load_font(14, True))
    draw.text((80, 248), title, fill=(255, 255, 255, 255), font=load_font(52, True))
    if subtitle:
        draw.text((80, 320), subtitle, fill=(180, 185, 200, 255), font=load_font(20))
    # Bottom accent line
    draw.line([(80, 560), (240, 560)], fill=(*accent, 200), width=4)
    return img


def save(img, path):
    img.convert('RGB').save(path, 'PNG', optimize=True)
    print(f'  → {path} ({os.path.getsize(path)//1024}KB)')


def strip_html(text):
    """Remove HTML tags from hero titles."""
    import re
    return re.sub(r'<[^>]+>', '', text)


def hero_text(page_id):
    """Get eyebrow, title, subtitle from heroes/meta data."""
    h = heroes.get(page_id, {})
    m = meta.get(page_id, {})
    eyebrow = h.get('eyebrow', page_id.upper())
    title = strip_html(h.get('title', m.get('title', page_id.title())))
    subtitle = m.get('description', h.get('lede', ''))[:80]
    return eyebrow, title, subtitle


def gen_about():
    img = base_image()
    logo_src = Image.open('img/moddable-logo-white.png').convert('RGBA')
    lh = 70
    lw = int(logo_src.width * lh / logo_src.height)
    logo = logo_src.resize((lw, lh), Image.LANCZOS)
    layer = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
    zone_left = 560
    zone_right = WIDTH - 80
    lx = (zone_left + zone_right) // 2 - lw // 2
    ly = (HEIGHT - lh) // 2
    layer.paste(logo, (lx, ly), logo)
    img = Image.alpha_composite(img, layer)
    eyebrow, title, subtitle = hero_text('about')
    add_text(img, eyebrow, title, subtitle, accent=ABOUT)
    save(img, 'img/og/about.png')


def gen_roadmap():
    img = base_image()
    draw = ImageDraw.Draw(img)
    # Bold vertical timeline on right side
    tx = 900
    y_start = 140
    y_end = 520
    # Main vertical line
    draw.line([(tx, y_start), (tx, y_end)], fill=(*GLOW_BLUE, 80), width=3)
    # Milestones
    roadmap_data = json.load(open('data/roadmap.json'))
    timeline_items = []
    for s in roadmap_data.get('sections', []):
        if s.get('type') == 'timeline':
            timeline_items = s.get('items', [])
            break
    milestones = [(it.get('quarter', ''), it.get('text', '')[:20], it.get('color', '') != '') for it in timeline_items[:4]]
    spacing = (y_end - y_start) // (len(milestones) - 1)
    for i, (date, label, done) in enumerate(milestones):
        my = y_start + i * spacing
        # Dot
        r = 10
        if done:
            draw.ellipse([tx - r, my - r, tx + r, my + r], fill=(*GLOW_BLUE, 220))
        else:
            draw.ellipse([tx - r, my - r, tx + r, my + r],
                         outline=(*GLOW_BLUE, 150), width=2)
        # Date left of line
        draw.text((tx - 120, my - 8), date,
                  fill=(*GLOW_BLUE, 180), font=load_font(12, True))
        # Label right of line
        draw.text((tx + 24, my - 8), label,
                  fill=(220, 225, 235, 220 if done else 120), font=load_font(15, done))
    eyebrow, title, subtitle = hero_text('roadmap')
    add_text(img, eyebrow, title, subtitle, accent=ABOUT)
    save(img, 'img/og/about-roadmap.png')


def gen_community():
    img = base_image()
    # Prominent hex grid covering right 60% with stronger opacity
    hex_layer = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
    hd = ImageDraw.Draw(hex_layer)
    hex_size = 44
    for row in range(HEIGHT // hex_size + 2):
        for col in range(20):
            hx = 500 + col * hex_size + (hex_size // 2 if row % 2 else 0)
            hy = row * hex_size
            t = min(1.0, (hx - 500) / 500)
            alpha = int(20 + 50 * t)
            hd.regular_polygon((hx, hy, hex_size // 3), 6,
                               fill=None, outline=(111, 181, 255, alpha))
    img = Image.alpha_composite(img, hex_layer)
    # Centred stat in right zone
    draw = ImageDraw.Draw(img)
    zone_cx = (560 + WIDTH - 80) // 2
    font_big = load_font(120, True)
    draw.text((zone_cx - 80, 240), '15', fill=(111, 181, 255, 70), font=font_big)
    draw.text((zone_cx - 60, 370), 'MEMBERS', fill=(111, 181, 255, 45), font=load_font(18, True))
    eyebrow, title, subtitle = hero_text('community')
    add_text(img, eyebrow, title, subtitle, accent=ABOUT)
    save(img, 'img/og/community.png')


def gen_news():
    img = base_image()
    # 3 news covers as fanned cards, centred in right zone
    covers = ['img/news/beyond-the-box.jpg', 'img/news/the-ancients.jpg',
              'img/news/making-mods-matter.jpg']
    positions = [(640, 180, -6), (760, 220, 0), (880, 190, 5)]
    for i, (cx, cy, angle) in enumerate(positions):
        path = covers[i]
        if not os.path.exists(path):
            continue
        cover = Image.open(path).convert('RGBA')
        cw, ch = 200, 130
        cover = cover.resize((cw, ch), Image.LANCZOS)
        bordered = Image.new('RGBA', (cw + 12, ch + 12), (255, 255, 255, 50))
        bordered.paste(cover, (6, 6), cover)
        bordered = bordered.rotate(angle, expand=True, fillcolor=(0, 0, 0, 0))
        layer = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
        layer.paste(bordered, (cx, cy), bordered)
        img = Image.alpha_composite(img, layer)
    eyebrow, title, subtitle = hero_text('news')
    add_text(img, eyebrow, title, subtitle, accent=NEWS)
    save(img, 'img/og/news.png')


def gen_games():
    img = base_image()
    # 3 game logos — centred in right half with equal margins
    logos = ['img/nukes-logo.png', 'img/endless-skies-logo.png', 'img/mongo-logo.png']
    logo_size = 120
    gap = 16
    total_w = logo_size * len(logos) + gap * (len(logos) - 1)
    # Right zone: from 560 to 1120 (equal 80px margin on right as left text has)
    zone_left = 560
    zone_right = WIDTH - 80
    zone_center = (zone_left + zone_right) // 2
    x_start = zone_center - total_w // 2
    for i, path in enumerate(logos):
        if not os.path.exists(path):
            continue
        logo = Image.open(path).convert('RGBA')
        lh = logo_size
        lw = int(logo.width * lh / logo.height)
        logo = logo.resize((lw, lh), Image.LANCZOS)
        layer = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
        lx = x_start + i * (logo_size + gap) + (logo_size - lw) // 2
        ly = (HEIGHT - lh) // 2
        layer.paste(logo, (lx, ly), logo)
        img = Image.alpha_composite(img, layer)
    eyebrow, title, subtitle = hero_text('games')
    add_text(img, eyebrow, title, subtitle, accent=GAMES)
    save(img, 'img/og/games.png')


def gen_press():
    img = base_image()
    # Large logo centred in right zone with proper margins
    logo_src = Image.open('img/moddable-logo-white.png').convert('RGBA')
    lh = 70
    lw = int(logo_src.width * lh / logo_src.height)
    logo = logo_src.resize((lw, lh), Image.LANCZOS)
    layer = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
    zone_left = 560
    zone_right = WIDTH - 80
    lx = (zone_left + zone_right) // 2 - lw // 2
    ly = (HEIGHT - lh) // 2
    layer.paste(logo, (lx, ly), logo)
    img = Image.alpha_composite(img, layer)
    eyebrow, title, subtitle = hero_text('press')
    add_text(img, eyebrow, title, subtitle, accent=ABOUT)
    save(img, 'img/og/press.png')


def gen_submit():
    img = base_image(accent_color=MODS)
    draw = ImageDraw.Draw(img)
    tx = 900
    y_start = 180
    y_end = 480
    spacing = (y_end - y_start) // 2
    draw.line([(tx, y_start), (tx, y_end)], fill=(*MODS, 80), width=3)
    submit_data = json.load(open('data/submit.json'))
    submit_steps = submit_data.get('sections', [{}])[0].get('steps', [])
    steps = [(s.get('number', str(i+1)), s.get('label', '')) for i, s in enumerate(submit_steps)]
    for i, (num, label) in enumerate(steps):
        sy = y_start + i * spacing
        r = 18
        draw.ellipse([tx - r, sy - r, tx + r, sy + r], fill=(*MODS, 200))
        draw.text((tx - 6, sy - 10), num, fill=(255, 255, 255, 255), font=load_font(18, True))
        draw.text((tx + 32, sy - 9), label,
                  fill=(220, 225, 235, 220), font=load_font(16))
    eyebrow, title, subtitle = hero_text('submit')
    add_text(img, eyebrow, title, subtitle, accent=MODS)
    save(img, 'img/og/submit.png')


def gen_subscribe():
    img = base_image(accent_color=GLOW_BLUE)
    draw = ImageDraw.Draw(img)
    ex, ey = 920, 310
    draw.rounded_rectangle([ex - 60, ey - 35, ex + 60, ey + 35],
                           radius=6, outline=(*GLOW_BLUE, 180), width=2)
    draw.line([(ex - 60, ey - 35), (ex, ey + 5), (ex + 60, ey - 35)],
              fill=(*GLOW_BLUE, 150), width=2)
    eyebrow, title, subtitle = hero_text('subscribe')
    add_text(img, eyebrow, title, subtitle, accent=GLOW_BLUE)
    save(img, 'img/og/subscribe.png')


def gen_team():
    img = base_image()
    # 4 team photos in 2x2 grid — generous spacing
    photos = ['img/team/mark.png', 'img/team/kevin.png',
              'img/team/akmal.png', 'img/team/iqbal.png']
    pw = 140
    gap = 24
    zone_left = 580
    zone_right = WIDTH - 80
    zone_cx = (zone_left + zone_right) // 2
    zone_cy = HEIGHT // 2
    grid_w = pw * 2 + gap
    x_start = zone_cx - grid_w // 2

    positions = [(0, 0), (1, 0), (0, 1), (1, 1)]
    for i, p in enumerate(photos):
        if not os.path.exists(p):
            continue
        photo = Image.open(p).convert('RGBA')
        ph_full = int(photo.height * pw / photo.width)
        photo = photo.resize((pw, ph_full), Image.LANCZOS)
        visible = int(ph_full * 0.50)
        photo = photo.crop((0, 0, pw, visible))
        col, row = positions[i]
        lx = x_start + col * (pw + gap)
        ly = zone_cy - visible - gap // 2 + row * (visible + gap)
        layer = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
        layer.paste(photo, (lx, ly), photo)
        img = Image.alpha_composite(img, layer)
    eyebrow, title, subtitle = hero_text('team')
    add_text(img, eyebrow, title, subtitle, accent=ABOUT)
    save(img, 'img/og/team.png')


def gen_chess_engine():
    img = base_image(accent_color=ENGINES)
    draw = ImageDraw.Draw(img)
    board_x, board_y = 750, 160
    sq = 40
    light = (45, 55, 90, 200)
    dark = (20, 28, 55, 200)
    board_layer = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
    bd = ImageDraw.Draw(board_layer)
    for row in range(8):
        for col in range(8):
            x1 = board_x + col * sq
            y1 = board_y + row * sq
            color = light if (row + col) % 2 == 0 else dark
            bd.rectangle([x1, y1, x1 + sq, y1 + sq], fill=color)
    mask = Image.new('L', (WIDTH, HEIGHT), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [board_x, board_y, board_x + 8*sq, board_y + 8*sq],
        radius=12, fill=255
    )
    board_layer.putalpha(mask)
    img = Image.alpha_composite(img, board_layer)
    details = json.load(open('data/details.json'))
    chess = details.get('chess', {})
    add_text(img, 'ENGINE', chess.get('title', 'Moddable Chess'),
             f"{chess.get('stats', [['']])[0][1] if chess.get('stats') else ''} variants",
             accent=ENGINES)
    save(img, 'img/og/engines-chess.png')


def gen_hexmaps_engine():
    import math
    img = base_image(accent_color=ENGINES)
    # Draw flat-top hexagons matching the site's hex-grid pattern (56x64 tile)
    hex_layer = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
    hd = ImageDraw.Draw(hex_layer)
    size = 18  # radius
    col_w = size * 1.5
    row_h = size * math.sqrt(3)
    for row in range(int(HEIGHT / row_h) + 2):
        for col in range(int((WIDTH - 580) / col_w) + 2):
            cx = 620 + col * col_w
            cy = row * row_h + (row_h / 2 if col % 2 else 0)
            # Flat-top hex vertices
            pts = []
            for i in range(6):
                angle = math.radians(60 * i)
                px = cx + size * math.cos(angle)
                py = cy + size * math.sin(angle)
                pts.append((px, py))
            # Fade opacity based on x position
            t = min(1.0, (cx - 620) / 400)
            alpha = int(30 + 70 * t)
            hd.polygon(pts, fill=None, outline=(6, 182, 212, alpha))
    img = Image.alpha_composite(img, hex_layer)
    hexmaps = details.get('moddable-hexmaps', {})
    add_text(img, 'ENGINE', hexmaps.get('title', 'Moddable Hexmaps'),
             f"Shared hex map engine for {hexmaps.get('stats', [['']])[0][1] if hexmaps.get('stats') else '6'} games",
             accent=ENGINES)
    save(img, 'img/og/engines-moddable-hexmaps.png')


def gen_mods():
    img = base_image(accent_color=MODS)
    eyebrow, title, subtitle = hero_text('mods')
    add_text(img, eyebrow, title, subtitle, accent=MODS)
    save(img, 'img/og/mods.png')


def gen_engines():
    img = base_image(accent_color=ENGINES)
    eyebrow, title, subtitle = hero_text('engines')
    add_text(img, eyebrow, title, subtitle, accent=ENGINES)
    save(img, 'img/og/engines.png')


def gen_developers():
    img = base_image(accent_color=DEVELOPERS)
    eyebrow, title, subtitle = hero_text('developers')
    add_text(img, eyebrow, title, subtitle, accent=DEVELOPERS)
    save(img, 'img/og/developers.png')


def gen_developers_api():
    img = base_image(accent_color=DEVELOPERS)
    m = meta.get('developers-api', {})
    add_text(img, 'TOOLS API',
             m.get('title', 'Connect and call'),
             m.get('description', 'MCP protocol and REST API')[:80],
             accent=DEVELOPERS)
    save(img, 'img/og/developers-api.png')


def gen_developers_examples():
    img = base_image(accent_color=DEVELOPERS)
    m = meta.get('developers-examples', {})
    add_text(img, 'BUILD WITH IT',
             m.get('title', 'Examples'),
             m.get('description', 'Bots, apps, and integrations')[:80],
             accent=DEVELOPERS)
    save(img, 'img/og/developers-examples.png')


# Generate all
print('Generating remaining OG images...')
gen_mods()
gen_engines()
gen_about()
gen_roadmap()
gen_community()
gen_news()
gen_games()
gen_press()
gen_submit()
gen_subscribe()
gen_team()
gen_chess_engine()
gen_hexmaps_engine()
gen_developers()
gen_developers_api()
gen_developers_examples()
print('Done.')
