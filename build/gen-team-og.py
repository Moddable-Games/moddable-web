#!/usr/bin/env python3
"""Generate per-team-member OG images (1200x630) mimicking the team detail hero."""

import json
from PIL import Image, ImageDraw, ImageFont, ImageFilter

team = json.load(open('data/team.json'))

WIDTH, HEIGHT = 1200, 630
BG = (10, 13, 42)  # cosmicDeep #0a0d2a


def hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def load_font(size, bold=False):
    paths = [
        '/System/Library/Fonts/Supplemental/Helvetica Neue.ttc',
        '/System/Library/Fonts/Helvetica.ttc',
    ]
    for p in paths:
        try:
            # Index 0 = regular, higher indices = bold/italic variants
            idx = 4 if bold else 0  # Helvetica Neue Bold is usually index 4
            return ImageFont.truetype(p, size, index=idx)
        except (OSError, IndexError):
            try:
                return ImageFont.truetype(p, size, index=0)
            except OSError:
                continue
    return ImageFont.load_default()


# Load logo once
logo_src = Image.open('img/moddable-logo-white.png').convert('RGBA')
logo_h = 28
logo_w = int(logo_src.width * logo_h / logo_src.height)
logo = logo_src.resize((logo_w, logo_h), Image.LANCZOS)

for member in team:
    # Start with dark background
    img = Image.new('RGBA', (WIDTH, HEIGHT), (*BG, 255))

    color = hex_to_rgb(member['color'])

    # Create large soft glow — render at full canvas size with gaussian blur
    glow_layer = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_layer)
    # Draw filled ellipse at the glow position
    gx, gy = 780, 180
    gr = 320
    glow_draw.ellipse(
        [gx - gr, gy - gr, gx + gr, gy + gr],
        fill=(*color, 70)
    )
    # Heavy gaussian blur for smooth feathering
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=120))
    img = Image.alpha_composite(img, glow_layer)

    # Load and place team photo — using the proven breakout recipe:
    # Clip bottom 35%, position so clipped edge sits ABOVE canvas bottom,
    # leaving space for the shadow line they emerge from.
    photo = Image.open(f'img/team/{member["img"]}').convert('RGBA')
    ph_w = 500
    ph_h = int(photo.height * ph_w / photo.width)
    photo = photo.resize((ph_w, ph_h), Image.LANCZOS)
    # Crop bottom 35% (equivalent of clip-path: inset(0 0 35% 0))
    visible_h = int(ph_h * 0.65)
    photo = photo.crop((0, 0, ph_w, visible_h))
    # Position: clipped bottom edge sits 50px above canvas bottom (shadow line zone)
    shadow_offset = 50
    x_pos = WIDTH - ph_w - 60
    y_pos = HEIGHT - visible_h - shadow_offset
    photo_layer = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
    photo_layer.paste(photo, (x_pos, y_pos), photo)
    img = Image.alpha_composite(img, photo_layer)

    # Shadow slit beneath person — stronger for dark bg
    shadow_y = HEIGHT - shadow_offset
    shadow_layer = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow_layer)
    sx_center = x_pos + ph_w // 2
    sw = int(ph_w * 0.75)
    # Core slit line
    sdraw.line(
        [(sx_center - sw//2, shadow_y), (sx_center + sw//2, shadow_y)],
        fill=(0, 0, 0, 255), width=4
    )
    # Downward shadow spread
    for i in range(1, 28):
        alpha = int(200 * (1 - i/28) ** 1.5)
        sdraw.line(
            [(sx_center - sw//2 + i*2, shadow_y + i), (sx_center + sw//2 - i*2, shadow_y + i)],
            fill=(0, 0, 0, alpha), width=2
        )
    # Upward glow above slit
    for i in range(1, 14):
        alpha = int(120 * (1 - i/14) ** 2)
        sdraw.line(
            [(sx_center - sw//2 + i*2, shadow_y - i), (sx_center + sw//2 - i*2, shadow_y - i)],
            fill=(0, 0, 0, alpha), width=1
        )
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=4))
    img = Image.alpha_composite(img, shadow_layer)

    # Draw text
    draw = ImageDraw.Draw(img)

    # Logo in top-left
    img.paste(logo, (80, 40), logo)

    # Site name eyebrow
    font_sm = load_font(16)
    draw.text((80, 220), 'MODDABLE.GAMES', fill=(111, 181, 255, 255), font=font_sm)

    # Name (large bold)
    font_lg = load_font(62, bold=True)
    draw.text((80, 248), member['name'], fill=(255, 255, 255, 255), font=font_lg)

    # Role
    font_md = load_font(20)
    draw.text((80, 330), member['role'], fill=(200, 200, 210, 255), font=font_md)

    # Save as RGB (no alpha for PNG OG images)
    out = img.convert('RGB')
    out_path = f'img/og/team-{member["slug"]}.png'
    out.save(out_path, 'PNG', optimize=True)
    print(f'  → {out_path} ({out.size[0]}x{out.size[1]})')

print('Done.')
