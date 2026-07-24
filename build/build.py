#!/usr/bin/env python3
"""
moddable-web SSG — Custom static site generator.
Zero dependencies (Python standard library only).
"""

import json
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BUILD_DIR, 'templates')
DATA_DIR = os.path.join(ROOT, 'data')

def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def load_json(path):
    return json.loads(read_file(path))

def get_version():
    vpath = os.path.join(ROOT, 'version.txt')
    if os.path.exists(vpath):
        return read_file(vpath).strip()
    return '0.1.0'


# ─── Template Engine ────────────────────────────────────────────────────────

def load_partial(name):
    path = os.path.join(TEMPLATES_DIR, name + '.html')
    if os.path.exists(path):
        return read_file(path)
    path = os.path.join(TEMPLATES_DIR, '_' + name + '.html')
    if os.path.exists(path):
        return read_file(path)
    return ''

def resolve_value(key, context):
    parts = key.strip().split('.')
    val = context
    for part in parts:
        if isinstance(val, dict):
            val = val.get(part)
        else:
            return None
        if val is None:
            return None
    return val

def expand_partials(template):
    """Inline partials (text substitution only, no rendering)."""
    result = template
    for _ in range(10):
        def replace_partial(m):
            name = m.group(1).strip()
            return load_partial(name)
        new_result = re.sub(r'\{\{>\s*([^}]+?)\s*\}\}', replace_partial, result)
        if new_result == result:
            break
        result = new_result
    return result

def render_template(template, context):
    # First, expand all partials (text only, no variable resolution)
    result = expand_partials(template)

    # Each loops: {{#each items}}...{{/each}} (supports nesting)
    def find_matching_block(text, open_tag, close_tag, start):
        """Find the matching close tag, handling nested blocks."""
        depth = 1
        pos = start
        while pos < len(text) and depth > 0:
            next_open = text.find(open_tag, pos)
            next_close = text.find(close_tag, pos)
            if next_close == -1:
                return -1
            if next_open != -1 and next_open < next_close:
                depth += 1
                pos = next_open + len(open_tag)
            else:
                depth -= 1
                if depth == 0:
                    return next_close
                pos = next_close + len(close_tag)
        return -1

    def process_each_blocks(text):
        each_open_re = re.compile(r'\{\{#each\s+([^}]+?)\s*\}\}')
        while True:
            m = each_open_re.search(text)
            if not m:
                break
            key = m.group(1).strip()
            body_start = m.end()
            body_end = find_matching_block(text, '{{#each', '{{/each}}', body_start)
            if body_end == -1:
                break
            body = text[body_start:body_end]
            items = resolve_value(key, context)
            if not items or not isinstance(items, list):
                replacement = ''
            else:
                parts = []
                for i, item in enumerate(items):
                    if isinstance(item, dict):
                        child_ctx = {**context, **item, '@index': i, '@first': i == 0, '@last': i == len(items) - 1}
                    else:
                        child_ctx = {**context, 'this': item, '@index': i, '@first': i == 0, '@last': i == len(items) - 1}
                    parts.append(render_template(body, child_ctx))
                replacement = ''.join(parts)
            text = text[:m.start()] + replacement + text[body_end + len('{{/each}}'):]
        return text

    result = process_each_blocks(result)

    # Conditionals (supports nesting): {{#if key}}...{{else}}...{{/if}}
    def process_if_blocks(text):
        if_open_re = re.compile(r'\{\{#if\s+([^}]+?)\s*\}\}')
        while True:
            m = if_open_re.search(text)
            if not m:
                break
            expr = m.group(1).strip()
            body_start = m.end()
            body_end = find_matching_block(text, '{{#if', '{{/if}}', body_start)
            if body_end == -1:
                break
            body = text[body_start:body_end]

            # Check for equality test: key "value"
            eq_match = re.match(r'(\S+)\s+"([^"]+)"', expr)
            if eq_match:
                key = eq_match.group(1)
                expected = eq_match.group(2)
                val = resolve_value(key, context)
                if str(val) == expected:
                    replacement = render_template(body, context)
                else:
                    replacement = ''
            else:
                key = expr
                val = resolve_value(key, context)
                # Split on {{else}} at depth 0
                else_pos = find_else_at_depth(body)
                if else_pos != -1:
                    true_body = body[:else_pos]
                    false_body = body[else_pos + len('{{else}}'):]
                else:
                    true_body = body
                    false_body = ''
                if val:
                    replacement = render_template(true_body, context)
                else:
                    replacement = render_template(false_body, context) if false_body else ''

            text = text[:m.start()] + replacement + text[body_end + len('{{/if}}'):]
        return text

    def find_else_at_depth(text):
        """Find {{else}} at depth 0 (not inside nested #if blocks)."""
        depth = 0
        pos = 0
        while pos < len(text):
            if text[pos:pos+5] == '{{#if':
                depth += 1
                pos += 5
            elif text[pos:pos+7] == '{{/if}}':
                depth -= 1
                pos += 7
            elif text[pos:pos+8] == '{{else}}' and depth == 0:
                return pos
            else:
                pos += 1
        return -1

    result = process_if_blocks(result)

    # Unless (supports nesting): {{#unless key}}...{{/unless}}
    def process_unless_blocks(text):
        unless_open_re = re.compile(r'\{\{#unless\s+([^}]+?)\s*\}\}')
        while True:
            m = unless_open_re.search(text)
            if not m:
                break
            key = m.group(1).strip()
            body_start = m.end()
            body_end = find_matching_block(text, '{{#unless', '{{/unless}}', body_start)
            if body_end == -1:
                break
            body = text[body_start:body_end]
            val = resolve_value(key, context)
            if not val:
                replacement = render_template(body, context)
            else:
                replacement = ''
            text = text[:m.start()] + replacement + text[body_end + len('{{/unless}}'):]
        return text

    result = process_unless_blocks(result)

    # Raw (unescaped): {{{key}}}
    def replace_raw(m):
        key = m.group(1).strip()
        val = resolve_value(key, context)
        if val is None:
            return ''
        return str(val)

    result = re.sub(r'\{\{\{([^}]+?)\}\}\}', replace_raw, result)

    # Escaped substitution: {{key}}
    def replace_var(m):
        key = m.group(1).strip()
        val = resolve_value(key, context)
        if val is None:
            return ''
        return html_escape(str(val))

    result = re.sub(r'\{\{([^#/!>][^}]*?)\}\}', replace_var, result)

    return result

def html_escape(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


# ─── Page Building ──────────────────────────────────────────────────────────

def load_all_data():
    data = {}
    for f in os.listdir(DATA_DIR):
        if f.endswith('.json'):
            key = f[:-5]
            data[key] = load_json(os.path.join(DATA_DIR, f))
    return data

def bundle_css(page_id, css_files):
    """Concatenate CSS files into a single per-page bundle."""
    shared = ['_mg', 'navbar', 'footer', 'hero', 'hero-features']
    all_files = shared + css_files
    parts = []
    for name in all_files:
        path = os.path.join(ROOT, 'css', name + '.css')
        if os.path.exists(path):
            parts.append(f'/* {name}.css */\n' + read_file(path))
    bundle_content = '\n'.join(parts)
    bundle_path = os.path.join(ROOT, 'css', f'page-{page_id}.css')
    write_file(bundle_path, bundle_content)
    return f'page-{page_id}'

def apply_base_path(html, base):
    """Rewrite absolute paths to include the base prefix for local dev."""
    if not base:
        return html
    # Rewrite href="/..." and src="/..." and url('/...' and url("/...
    html = re.sub(r'(href|src|action)="/', rf'\1="{base}/', html)
    html = re.sub(r"url\('/", f"url('{base}/", html)
    html = re.sub(r'url\("/', f'url("{base}/', html)
    return html

def build_page(template_name, context, output_path, base=''):
    template = read_file(os.path.join(TEMPLATES_DIR, template_name + '.html'))
    html = render_template(template, context)
    if base:
        html = apply_base_path(html, base)
    full_path = os.path.join(ROOT, output_path)
    write_file(full_path, html)
    print(f'  Built: {output_path}')

def mark_nav_active(nav_data, active_id):
    """Return nav data with 'active' flag set on the matching item."""
    if not nav_data or 'items' not in nav_data:
        return nav_data
    items = []
    for item in nav_data['items']:
        item_copy = {**item, 'active': item['id'] == active_id}
        items.append(item_copy)
    return {**nav_data, 'items': items}

def mark_footer_external(nav_data):
    """Mark external links in footer columns."""
    if not nav_data or 'footer_cols' not in nav_data:
        return nav_data
    cols = []
    for col in nav_data['footer_cols']:
        links = []
        for link in col.get('links', []):
            link_copy = {**link, 'external': link['href'].startswith('http')}
            links.append(link_copy)
        cols.append({**col, 'links': links})
    return {**nav_data, 'footer_cols': cols}

def get_base_path():
    """Parse --base flag from command line args."""
    import sys
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg == '--base' and i < len(sys.argv) - 1:
            return sys.argv[i + 1].rstrip('/')
        if arg.startswith('--base='):
            return arg.split('=', 1)[1].rstrip('/')
    return ''

def build_site():
    print('moddable-web SSG build starting...')
    print(f'  Root: {ROOT}')

    version = get_version()
    base = get_base_path()
    if base:
        print(f'  Base path: {base}')

    def build(template_name, context, output_path):
        build_page(template_name, context, output_path, base)

    data = load_all_data()
    nav_raw = data.get('nav', {})
    nav_raw = mark_footer_external(nav_raw)
    heroes = data.get('heroes', {})
    meta = data.get('meta', {})

    def make_context(page_id, nav_active, extra_css=None):
        hero = heroes.get(page_id, {})
        hero['tier1'] = hero.get('tier') == 1
        page_meta = meta.get(page_id, {})
        nav = mark_nav_active(nav_raw, nav_active)
        css_bundle = bundle_css(page_id, extra_css or [])
        ctx = {
            'version': version,
            'nav': nav,
            'year': '2026',
            'site_name': 'Moddable.Games',
            'site_url': 'https://moddable.games',
            'page_id': page_id,
            'meta': page_meta,
            'hero': hero,
            'css_bundle': css_bundle,
        }
        return ctx

    # ─── Tier 1: Pure content pages ────────────────────────────────────
    pages = data.get('pages', {})
    for page_id, page_data in pages.items():
        ctx = make_context(page_id, page_data.get('nav_active', ''), page_data.get('css_files', []))
        # Merge page-specific data directly into context
        page_json = data.get(page_id)
        if page_json and isinstance(page_json, dict):
            ctx.update(page_json)
        template = page_data.get('template', 'page')
        output = page_data.get('output', page_id + '/index.html')
        build(template, ctx, output)

    # ─── Tier 2: Index pages ───────────────────────────────────────────
    CATEGORY_COLORS = {
        'Conversion': '#d11a1a',
        'Rebalance': '#3a9928',
        'Reskin': '#0c4f8d',
    }
    ACCENT_COLORS = {
        'red': '#d11a1a',
        'green': '#3a9928',
        'blue': '#0c4f8d',
        'amber': '#e8a91a',
        'cyan': '#06b6d4',
    }

    # Mods index
    mods = data.get('mods', [])
    for mod in mods:
        mod['category_color'] = CATEGORY_COLORS.get(mod.get('category'), '#0c4f8d')
    ctx = make_context('mods', 'Mods', ['mods', 'cards'])
    ctx['mods'] = mods
    ctx['mod_count'] = str(len(mods))
    build('mods-index', ctx, 'mods/index.html')

    # Games index
    games = data.get('games', [])
    for game in games:
        game['accent_color'] = ACCENT_COLORS.get(game.get('accent'), '#0c4f8d')
    ctx = make_context('games', 'Games', ['games', 'cards'])
    ctx['games'] = games
    build('games-index', ctx, 'games/index.html')

    # Engines index
    engines = data.get('engines', [])
    for eng in engines:
        eng['accent_color'] = ACCENT_COLORS.get(eng.get('accent'), '#0c4f8d')
    ctx = make_context('engines', 'Engines', ['engines', 'cards'])
    ctx['engines'] = engines
    build('engines-index', ctx, 'engines/index.html')

    # News index
    ctx = make_context('news', 'News', ['news-index', 'cards'])
    ctx['news'] = data.get('news', [])
    build('news-index', ctx, 'news/index.html')

    # Tools hub
    ctx = make_context('tools', 'Tools', ['tools'])
    ctx['tools_sections'] = data.get('tools-sections', {})
    build('tools-index', ctx, 'tools/index.html')

    # ─── Team index ────────────────────────────────────────────────────
    ctx = make_context('team', 'About', ['team'])
    ctx['team'] = data.get('team', [])
    build('team-index', ctx, 'team/index.html')

    # ─── Home page ──────────────────────────────────────────────────────
    home_data = data.get('home', {})
    home_meta = meta.get('home', {
        'title': 'Moddable.Games — Creating games you already own',
        'description': 'The first board game company built entirely in the open. CC-licensed rulebooks, forkable engines, and original games designed to be taken apart.',
        'url': 'https://moddable.games/',
        'image': 'https://moddable.games/img/og/default.png',
    })
    nav = mark_nav_active(nav_raw, '')
    home_css_bundle = bundle_css('home', ['home', 'cards'])
    home_ctx = {
        'version': version,
        'nav': nav,
        'year': '2026',
        'site_name': 'Moddable.Games',
        'site_url': 'https://moddable.games',
        'page_id': 'home',
        'meta': home_meta,
        'hero': {},
        'css_bundle': home_css_bundle,
        'home': home_data,
        'featured_mods': mods[:6],
        'latest_news': data.get('news', [])[:3],
    }
    build('home', home_ctx, 'index.html')

    print(f'\nBuild complete. Version: {version}')


if __name__ == '__main__':
    build_site()
