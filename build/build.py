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
    # Rewrite href="/..." and src="/..." and data="/..." and url('/...' and url("/...
    html = re.sub(r'(href|src|action|data)="/', rf'\1="{base}/', html)
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
    mods_data = data.get('mods', {})
    mods = mods_data.get('items', []) if isinstance(mods_data, dict) else mods_data
    mods_labels = mods_data.get('labels', {}) if isinstance(mods_data, dict) else {}
    mods_categories = mods_data.get('categories', []) if isinstance(mods_data, dict) else []
    for mod in mods:
        mod['category_color'] = CATEGORY_COLORS.get(mod.get('category'), '#0c4f8d')
    ctx = make_context('mods', 'Mods', ['mods', 'cards'])
    ctx['mods'] = mods
    ctx['mods_labels'] = mods_labels
    ctx['mods_categories'] = mods_categories
    ctx['mods_submit_cta'] = mods_data.get('submit_cta', {}) if isinstance(mods_data, dict) else {}
    ctx['mod_count'] = str(len(mods))
    build('mods-index', ctx, 'mods/index.html')

    # Games index
    games_data = data.get('games', {})
    games = games_data.get('items', []) if isinstance(games_data, dict) else games_data
    for game in games:
        game['accent_color'] = ACCENT_COLORS.get(game.get('accent'), '#0c4f8d')
    ctx = make_context('games', 'Games', ['games', 'cards'])
    ctx['games'] = games
    ctx['games_rules'] = games_data.get('rules_section', {}) if isinstance(games_data, dict) else {}
    ctx['games_cta'] = games_data.get('cta', {}) if isinstance(games_data, dict) else {}
    build('games-index', ctx, 'games/index.html')

    # Engines index
    engines_data = data.get('engines', {})
    engines = engines_data.get('items', []) if isinstance(engines_data, dict) else engines_data
    for eng in engines:
        eng['accent_color'] = ACCENT_COLORS.get(eng.get('accent'), '#0c4f8d')
    ctx = make_context('engines', 'Engines', ['engines', 'cards'])
    ctx['engines'] = engines
    ctx['engines_cta'] = engines_data.get('cta', {}) if isinstance(engines_data, dict) else {}
    build('engines-index', ctx, 'engines/index.html')

    # News index
    news_raw = data.get('news', [])
    news_items = news_raw.get('items', news_raw) if isinstance(news_raw, dict) else news_raw
    news_labels = news_raw.get('labels', {}) if isinstance(news_raw, dict) else {}
    ctx = make_context('news', 'News', ['news-index', 'cards'])
    for post in news_items:
        post['tags_str'] = ','.join(post.get('tags', []))
    ctx['news'] = news_items
    ctx['labels'] = news_labels
    ctx['featured'] = news_items[0] if news_items else {}
    ctx['grid_news'] = news_items[1:] if len(news_items) > 1 else []
    # Build topic counts from tags
    topic_counts = {}
    for post in news_items:
        for tag in post.get('tags', []):
            topic_counts[tag] = topic_counts.get(tag, 0) + 1
    ctx['topics'] = [{'name': t, 'count': str(c)} for t, c in sorted(topic_counts.items(), key=lambda x: -x[1])]
    # Build archive months
    archive_counts = {}
    for post in news_items:
        month = post.get('date', '')
        if month:
            archive_counts[month] = archive_counts.get(month, 0) + 1
    ctx['archive'] = [{'month': m, 'count': str(c)} for m, c in archive_counts.items()]
    build('news-index', ctx, 'news/index.html')

    # Tools hub
    ctx = make_context('tools', 'Tools', ['tools'])
    ctx['tools_sections'] = data.get('tools-sections', {})
    build('tools-index', ctx, 'tools/index.html')

    # ─── Team index ────────────────────────────────────────────────────
    SOCIAL_ICONS = {
        'linkedin': '<svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M20.5 2h-17A1.5 1.5 0 002 3.5v17A1.5 1.5 0 003.5 22h17a1.5 1.5 0 001.5-1.5v-17A1.5 1.5 0 0020.5 2zM8 19H5v-9h3zM6.5 8.25A1.75 1.75 0 118.3 6.5a1.78 1.78 0 01-1.8 1.75zM19 19h-3v-4.74c0-1.42-.6-1.93-1.38-1.93A1.74 1.74 0 0013 14.19V19h-3v-9h2.9v1.3a3.11 3.11 0 012.7-1.4c1.55 0 3.36.86 3.36 3.66z"/></svg>',
        'x': '<svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>',
        'instagram': '<svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z"/></svg>',
    }
    team_members = data.get('team', [])
    for member in team_members:
        socials_obj = member.get('socials', {})
        if socials_obj and isinstance(socials_obj, dict):
            socials_list = []
            for platform in ['linkedin', 'x', 'instagram']:
                if platform in socials_obj:
                    socials_list.append({'platform': platform, 'href': socials_obj[platform], 'icon': SOCIAL_ICONS.get(platform, '')})
            member['socials'] = socials_list
    ctx = make_context('team', 'About', ['team'])
    ctx['team'] = team_members
    build('team-index', ctx, 'team/index.html')

    # ─── Home page ──────────────────────────────────────────────────────
    home_data = data.get('home', {})
    # Prepare typewriter data for template
    hero = home_data.get('hero', {})
    tw_words = hero.get('typewriter_words', ['games'])
    hero['typewriter_default'] = tw_words[0]
    hero['typewriter_words_str'] = ','.join(tw_words)
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
        'latest_news': news_items[:3],
    }
    build('home', home_ctx, 'index.html')

    print(f'\nBuild complete. Version: {version}')


if __name__ == '__main__':
    build_site()
