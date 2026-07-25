#!/usr/bin/env python3
"""Generate OG images for tools pages. Data-driven from config below."""

import json, sys, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

force = '--force' in sys.argv

WIDTH, HEIGHT = 1200, 630
BG = (10, 13, 42)

TOOLS = [
    {
        'slug': 'tools',
        'title': 'Game Night Tools',
        'subtitle': 'Dice · Timer · Seating · Score',
        'color': (111, 181, 255),
        'icon': 'dice',
    },
    {
        'slug': 'tools-dice',
        'title': 'Dice Lab',
        'subtitle': 'Roll any dice · Simulate combat for 7 systems',
        'color': (209, 26, 26),
        'icon': 'dice',
    },
    {
        'slug': 'tools-chess',
        'title': 'Chess Tools',
        'subtitle': '70 playable variants',
        'color': (12, 79, 141),
        'icon': 'chess',
    },
    {
        'slug': 'tools-decks',
        'title': 'Deck Builder',
        'subtitle': 'Custom card decks for any game',
        'color': (111, 181, 255),
        'icon': 'cards',
    },
    {
        'slug': 'tools-nukes',
        'title': 'Nukes Tools',
        'subtitle': 'Strike planner · Combat · Resources',
        'color': (209, 26, 26),
        'icon': 'nuke',
        'logo': 'img/nukes-logo.png',
    },
    {
        'slug': 'tools-talisman',
        'title': 'Talisman Tools',
        'subtitle': 'Character lottery · Hex board · Encounters',
        'color': (12, 79, 141),
        'icon': 'spiral',
    },
    {
        'slug': 'tools-ti',
        'title': 'TI4 Tools',
        'subtitle': 'Factions · Objectives · Agenda voter',
        'color': (12, 79, 141),
        'icon': 'galaxy',
    },
    {
        'slug': 'tools-ti-dashboard',
        'title': 'TI4 Game Dashboard',
        'subtitle': 'Shared-screen session tracker · VP · Objectives · Agenda',
        'color': (111, 181, 255),
        'icon': 'galaxy',
    },
    {
        'slug': 'tools-oracles',
        'title': 'Oracles',
        'subtitle': 'Scene Forge · Ask the Oracle · Thread Weaver',
        'color': (111, 181, 255),
        'icon': 'spiral',
    },
]


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


def draw_icon(draw, icon, cx, cy, color, size=120):
    """Draw a simple geometric icon."""
    r, g, b = color
    if icon == 'dice':
        # Two overlapping squares with dots
        s = size // 2
        draw.rounded_rectangle([cx-s, cy-s, cx+s, cy+s], radius=12,
                               outline=(r, g, b, 200), width=3)
        for dot in [(-s//3, -s//3), (0, 0), (s//3, s//3)]:
            draw.ellipse([cx+dot[0]-6, cy+dot[1]-6, cx+dot[0]+6, cy+dot[1]+6],
                        fill=(r, g, b, 200))
    elif icon == 'chess':
        # Knight piece silhouette
        s = size // 2
        # Base
        draw.rounded_rectangle([cx-s//2, cy+s//2-8, cx+s//2, cy+s//2+8], radius=4, fill=(r, g, b, 180))
        # Stem
        draw.rounded_rectangle([cx-s//4, cy, cx+s//4, cy+s//2-8], radius=4, fill=(r, g, b, 150))
        # Head (knight shape - angled rectangle)
        head_pts = [(cx-s//3, cy), (cx+s//4, cy), (cx+s//3, cy-s//2), (cx-s//6, cy-s//2)]
        draw.polygon(head_pts, fill=(r, g, b, 160))
        # Ear/mane
        draw.polygon([(cx-s//6, cy-s//2), (cx, cy-s//2-s//4), (cx+s//6, cy-s//2)], fill=(r, g, b, 180))
        # Eye
        draw.ellipse([cx, cy-s//3-4, cx+8, cy-s//3+4], fill=(10, 13, 42, 255))
    elif icon == 'cards':
        # Single playing card with suit symbol
        cw, ch = 70, 100
        x1, y1 = cx - cw//2, cy - ch//2
        x2, y2 = cx + cw//2, cy + ch//2
        draw.rounded_rectangle([x1, y1, x2, y2], radius=8, outline=(r, g, b, 200), width=3)
        # Spade symbol in centre
        draw.polygon([(cx, cy-20), (cx-16, cy+4), (cx+16, cy+4)], fill=(r, g, b, 180))
        draw.ellipse([cx-16, cy-8, cx, cy+8], fill=(r, g, b, 180))
        draw.ellipse([cx, cy-8, cx+16, cy+8], fill=(r, g, b, 180))
        draw.line([(cx, cy+4), (cx, cy+20)], fill=(r, g, b, 180), width=3)
    elif icon == 'nuke':
        # Mushroom cloud — circle on top of a stem
        draw.ellipse([cx-50, cy-60, cx+50, cy+10], outline=(r, g, b, 200), width=3)
        draw.line([(cx, cy+10), (cx, cy+60)], fill=(r, g, b, 200), width=4)
        draw.arc([cx-30, cy+40, cx+30, cy+80], 0, 180, fill=(r, g, b, 150), width=3)
    elif icon == 'spiral':
        # Spiral path
        import math
        points = []
        for i in range(80):
            angle = i * 0.15
            radius = 10 + i * 0.8
            px = cx + int(radius * math.cos(angle))
            py = cy + int(radius * math.sin(angle))
            points.append((px, py))
        draw.line(points, fill=(r, g, b, 180), width=2)
    elif icon == 'galaxy':
        # Concentric rings with dots
        for rad in [30, 55, 80]:
            draw.ellipse([cx-rad, cy-rad, cx+rad, cy+rad],
                        outline=(r, g, b, 100 + rad), width=1)
        draw.ellipse([cx-8, cy-8, cx+8, cy+8], fill=(r, g, b, 220))
        # Orbital dots
        import math
        for i in range(5):
            angle = i * 1.25
            px = cx + int(55 * math.cos(angle))
            py = cy + int(55 * math.sin(angle))
            draw.ellipse([px-4, py-4, px+4, py+4], fill=(r, g, b, 180))


# Load logo
logo_src = Image.open('img/moddable-logo-white.png').convert('RGBA')
logo_h = 28
logo_w = int(logo_src.width * logo_h / logo_src.height)
logo = logo_src.resize((logo_w, logo_h), Image.LANCZOS)

for tool in TOOLS:
    out_path = f'img/og/{tool["slug"]}.png'

    if not force and os.path.exists(out_path) and os.path.getsize(out_path) > 30000:
        continue

    r, g, b = tool['color']
    img = Image.new('RGBA', (WIDTH, HEIGHT), (*BG, 255))

    # Background glow
    glow_layer = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow_layer)
    gd.ellipse([750, 100, 1350, 700], fill=(r, g, b, 40))
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=100))
    img = Image.alpha_composite(img, glow_layer)

    # Logo or icon on right
    if tool.get('logo') and os.path.exists(tool['logo']):
        tool_logo = Image.open(tool['logo']).convert('RGBA')
        max_size = 220
        ratio = min(max_size / tool_logo.width, max_size / tool_logo.height)
        lw = int(tool_logo.width * ratio)
        lh = int(tool_logo.height * ratio)
        tool_logo = tool_logo.resize((lw, lh), Image.LANCZOS)
        logo_layer = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
        logo_layer.paste(tool_logo, (920 - lw//2, 315 - lh//2), tool_logo)
        img = Image.alpha_composite(img, logo_layer)
    else:
        icon_layer = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
        id = ImageDraw.Draw(icon_layer)
        draw_icon(id, tool['icon'], 920, 315, tool['color'], 140)
        img = Image.alpha_composite(img, icon_layer)

    # Text
    draw = ImageDraw.Draw(img)
    img.paste(logo, (80, 40), logo)

    font_eyebrow = load_font(14, bold=True)
    draw.text((80, 220), 'INTERACTIVE TOOLS', fill=(r, g, b, 255), font=font_eyebrow)

    font_title = load_font(52, bold=True)
    draw.text((80, 248), tool['title'], fill=(255, 255, 255, 255), font=font_title)

    font_sub = load_font(20)
    draw.text((80, 320), tool['subtitle'], fill=(180, 185, 200, 255), font=font_sub)

    # Bottom accent line
    draw.line([(80, 560), (240, 560)], fill=(r, g, b, 200), width=4)

    out = img.convert('RGB')
    out.save(out_path, 'PNG', optimize=True)
    print(f'  → {out_path}')

print('Done.')
