#!/usr/bin/env python3
"""Generate OG images for mod detail pages from mods.json.
Only regenerates images under 30KB (templates). Run with --force to regenerate all."""

import json, sys, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

mods_raw = json.load(open('data/mods.json'))
mods = mods_raw.get('items', mods_raw) if isinstance(mods_raw, dict) else mods_raw
force = '--force' in sys.argv

WIDTH, HEIGHT = 1200, 630
BG = (10, 13, 42)

COLORS = {
    'Conversion': (209, 26, 26),
    'Total conversion': (209, 26, 26),
    'Rebalance': (58, 153, 40),
    'Reskin': (12, 79, 141),
}



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


# Load shared assets
logo_src = Image.open('img/moddable-logo-white.png').convert('RGBA')
logo_h = 28
logo_w = int(logo_src.width * logo_h / logo_src.height)
logo = logo_src.resize((logo_w, logo_h), Image.LANCZOS)

hex_svg_path = 'img/hex-grid-white.svg'

for mod in mods:
    slug = mod['path'].strip('/').split('/')[-1]
    out_path = f'img/og/mods-{slug}.png'

    if not force and os.path.exists(out_path) and os.path.getsize(out_path) > 30000:
        continue

    color = COLORS.get(mod['category'], (12, 79, 141))
    r, g, b = color

    img = Image.new('RGBA', (WIDTH, HEIGHT), (*BG, 255))

    # Background glow in category colour
    glow_layer = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_layer)
    glow_draw.ellipse([700, 80, 1300, 680], fill=(r, g, b, 50))
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=100))
    img = Image.alpha_composite(img, glow_layer)

    # Right-side visual: logo only (no hex card) if unique logo exists, else hex card
    logo_path = mod.get('logo')
    has_unique_logo = logo_path and os.path.exists(logo_path) and 'moddable-cube' not in logo_path

    if has_unique_logo:
        # Render logo large and centred in right zone
        mod_logo = Image.open(logo_path).convert('RGBA')
        max_logo_size = 280
        ratio = min(max_logo_size / mod_logo.width, max_logo_size / mod_logo.height)
        lw = int(mod_logo.width * ratio)
        lh = int(mod_logo.height * ratio)
        mod_logo = mod_logo.resize((lw, lh), Image.LANCZOS)
        logo_layer = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
        zone_cx = (680 + WIDTH - 80) // 2
        zone_cy = HEIGHT // 2
        logo_layer.paste(mod_logo, (zone_cx - lw // 2, zone_cy - lh // 2), mod_logo)
        img = Image.alpha_composite(img, logo_layer)
    elif os.path.exists('img/moddable-cube-logo.png'):
        # Render cube logo centred in right zone
        cube = Image.open('img/moddable-cube-logo.png').convert('RGBA')
        cube_size = 200
        ratio = min(cube_size / cube.width, cube_size / cube.height)
        cw = int(cube.width * ratio)
        ch = int(cube.height * ratio)
        cube = cube.resize((cw, ch), Image.LANCZOS)
        cube_layer = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
        zone_cx = (680 + WIDTH - 80) // 2
        zone_cy = HEIGHT // 2
        cube_layer.paste(cube, (zone_cx - cw // 2, zone_cy - ch // 2), cube)
        img = Image.alpha_composite(img, cube_layer)
    else:
        # Hex-grid card on right side
        card_w, card_h = 380, 380
        card_x, card_y = 740, 125
        card = Image.new('RGBA', (card_w, card_h), (0, 0, 0, 0))
        cd = ImageDraw.Draw(card)
        for y in range(card_h):
            t = (y / card_h) ** 0.7
            cr = int(BG[0] * (1-t) + r * t)
            cg = int(BG[1] * (1-t) + g * t)
            cb = int(BG[2] * (1-t) + b * t)
            cd.line([(0, y), (card_w, y)], fill=(cr, cg, cb, 255))
        hd = ImageDraw.Draw(card)
        hex_size = 32
        for row in range(card_h // hex_size + 2):
            for col in range(card_w // hex_size + 2):
                hx = col * hex_size + (hex_size//2 if row % 2 else 0)
                hy = row * hex_size
                hd.regular_polygon((hx, hy, hex_size//3), 6,
                                   fill=None, outline=(255, 255, 255, 20))
        mask = Image.new('L', (card_w, card_h), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, card_w-1, card_h-1], radius=24, fill=255)
        card.putalpha(mask)
        card_layer = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
        card_layer.paste(card, (card_x, card_y), card)
        img = Image.alpha_composite(img, card_layer)

    # Text content — left side
    draw = ImageDraw.Draw(img)

    # Logo
    img.paste(logo, (80, 40), logo)

    # Category pill
    font_cat = load_font(14, bold=True)
    cat_text = mod['category'].upper()
    draw.text((80, 220), cat_text, fill=(r, g, b, 255), font=font_cat)

    # Title
    font_title = load_font(52, bold=True)
    draw.text((80, 248), mod['title'], fill=(255, 255, 255, 255), font=font_title)

    # Base game
    font_base = load_font(22)
    draw.text((80, 318), mod['baseGame'], fill=(180, 185, 200, 255), font=font_base)

    # Stats line
    font_stats = load_font(15)
    draw.text((80, 360), mod.get('stats', ''), fill=(130, 140, 160, 255), font=font_stats)

    # Bottom accent line
    draw.line([(80, 560), (240, 560)], fill=(r, g, b, 200), width=4)

    out = img.convert('RGB')
    out.save(out_path, 'PNG', optimize=True)
    print(f'  → {out_path}')

print('Done.')
