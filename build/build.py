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

CONTENT_DIR = os.path.join(ROOT, 'content')


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


# ─── Counts Substitution ──────────────────────────────────────────────────

UNIVERSAL_STATS_URL = 'https://tools.moddable.games/api/stats'

STATS_TO_COUNTS = {
    'pieces': 'engine_pieces',
    'boards': 'engine_boards',
    'boardFamilies': 'engine_families',
    'tiles': 'engine_tiles',
    'puzzles': 'chess_puzzles',
    'variants': 'engine_variants',
    'games': 'games_count',
    'tools': 'tool_count',
    'families': 'tool_families',
    'pages': 'page_count',
    'newsArticles': 'news_count',
    'modsListed': 'mods_count',
}


def refresh_counts():
    """Fetch universal stats from tools API and update counts.json."""
    import urllib.request
    counts_path = os.path.join(DATA_DIR, 'counts.json')
    try:
        req = urllib.request.Request(UNIVERSAL_STATS_URL, headers={'Accept': 'application/json'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            universal = json.loads(resp.read().decode())
    except Exception as e:
        print(f'  Stats fetch skipped ({e}) — using existing counts.json')
        return

    combined = universal.get('combined', {})
    if not combined:
        print('  Stats fetch returned no combined data — using existing counts.json')
        return

    counts = load_json(counts_path) if os.path.exists(counts_path) else {}
    updated = 0
    for stat_key, count_key in STATS_TO_COUNTS.items():
        val = combined.get(stat_key)
        if val is not None:
            new_val = str(val)
            if counts.get(count_key) != new_val:
                counts[count_key] = new_val
                updated += 1

    if updated:
        write_file(counts_path, json.dumps(counts, indent=2) + '\n')
        print(f'  Refreshed counts.json from universal stats ({updated} values updated)')
    else:
        print('  Counts already up to date with universal stats')


def load_counts():
    """Load counts.json — single source of truth for all dynamic numbers."""
    path = os.path.join(DATA_DIR, 'counts.json')
    if os.path.exists(path):
        return load_json(path)
    return {}


def substitute_counts(obj, counts):
    """Recursively replace {{counts.X}} placeholders in string values."""
    if isinstance(obj, str):
        for key, val in counts.items():
            obj = obj.replace('{{counts.' + key + '}}', val)
        return obj
    elif isinstance(obj, list):
        return [substitute_counts(item, counts) for item in obj]
    elif isinstance(obj, dict):
        return {k: substitute_counts(v, counts) for k, v in obj.items()}
    return obj


# ─── Markdown Converter ────────────────────────────────────────────────────

def slugify(text):
    """Convert heading text to a URL-friendly ID."""
    s = text.lower().strip()
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'[\s]+', '-', s)
    return s.strip('-')


def markdown_to_html(text):
    """Convert markdown to HTML. Zero dependencies."""
    lines = text.split('\n')
    html_parts = []
    i = 0
    first_para = True

    while i < len(lines):
        line = lines[i]

        # Blank line
        if not line.strip():
            i += 1
            continue

        # HTML block passthrough (lines starting with < that aren't closing tags)
        if line.strip().startswith('<') and not line.strip().startswith('</'):
            html_block = []
            while i < len(lines) and lines[i].strip():
                html_block.append(lines[i])
                i += 1
            html_parts.append('\n'.join(html_block))
            # If the block is a <p class="lede">, count it as first para
            if html_block[0].strip().startswith('<p class="lede"'):
                first_para = False
            continue

        # Code block
        if line.strip().startswith('```'):
            lang = line.strip()[3:].strip()
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                code_lines.append(lines[i])
                i += 1
            i += 1  # skip closing ```
            code = '\n'.join(code_lines)
            code = code.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            lang_class = f' class="language-{lang}"' if lang else ''
            html_parts.append(f'<pre><code{lang_class}>{code}</code></pre>')
            continue

        # Heading
        if line.startswith('#'):
            match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if match:
                level = len(match.group(1))
                heading_text = match.group(2).strip()
                heading_id = slugify(heading_text)
                html_parts.append(f'<h{level} id="{heading_id}">{inline_format(heading_text)}</h{level}>')
                i += 1
                continue

        # Horizontal rule
        if re.match(r'^---+\s*$', line):
            html_parts.append('<hr>')
            i += 1
            continue

        # Blockquote
        if line.startswith('>'):
            bq_lines = []
            while i < len(lines) and lines[i].startswith('>'):
                bq_lines.append(lines[i][1:].strip() if len(lines[i]) > 1 else '')
                i += 1
            bq_text = ' '.join(l for l in bq_lines if l)
            html_parts.append(f'<blockquote><p>{inline_format(bq_text)}</p></blockquote>')
            continue

        # Unordered list
        if re.match(r'^[\-\*]\s', line):
            items = []
            while i < len(lines) and re.match(r'^[\-\*]\s', lines[i]):
                items.append(lines[i][2:].strip())
                i += 1
            html_parts.append('<ul>' + ''.join(f'<li>{inline_format(it)}</li>' for it in items) + '</ul>')
            continue

        # Ordered list
        if re.match(r'^\d+\.\s', line):
            items = []
            while i < len(lines) and re.match(r'^\d+\.\s', lines[i]):
                items.append(re.sub(r'^\d+\.\s', '', lines[i]).strip())
                i += 1
            html_parts.append('<ol>' + ''.join(f'<li>{inline_format(it)}</li>' for it in items) + '</ol>')
            continue

        # Image (standalone line)
        img_match = re.match(r'^!\[([^\]]*)\]\(([^)]+)\)\s*$', line)
        if img_match:
            alt, src = img_match.group(1), img_match.group(2)
            html_parts.append(f'<img src="{src}" alt="{alt}" loading="lazy">')
            i += 1
            continue

        # Paragraph (collect consecutive non-blank, non-special lines)
        para_lines = []
        while i < len(lines) and lines[i].strip() and not lines[i].startswith('#') \
                and not lines[i].startswith('>') and not lines[i].startswith('```') \
                and not re.match(r'^---+\s*$', lines[i]) \
                and not re.match(r'^[\-\*]\s', lines[i]) \
                and not re.match(r'^\d+\.\s', lines[i]) \
                and not re.match(r'^!\[', lines[i]) \
                and not (lines[i].strip().startswith('<') and not lines[i].strip().startswith('</')):
            para_lines.append(lines[i])
            i += 1
        if para_lines:
            text_content = ' '.join(para_lines)
            if first_para:
                html_parts.append(f'<p class="lede">{inline_format(text_content)}</p>')
                first_para = False
            else:
                html_parts.append(f'<p>{inline_format(text_content)}</p>')

    return '\n'.join(html_parts)


def inline_format(text):
    """Handle inline markdown: bold, italic, code, links, images."""
    # Inline images
    text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'<img src="\2" alt="\1" loading="lazy">', text)
    # Links
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
    # Bold
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # Italic
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    # Inline code
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    return text


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
    counts = load_counts()
    for f in os.listdir(DATA_DIR):
        if f.endswith('.json'):
            key = f[:-5]
            raw = load_json(os.path.join(DATA_DIR, f))
            data[key] = substitute_counts(raw, counts) if key != 'counts' else raw
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

    refresh_counts()

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

    # Tools sub-pages (per-game tool pages)
    tools_pages = data.get('tools-pages', {})
    for tool_key, tool_data in tools_pages.items():
        page_id = f'tools-{tool_key}'
        css_files = tool_data.get('css_files', ['tools'])
        ctx = make_context(page_id, 'Tools', css_files)
        ctx['tool_page'] = tool_data
        slug = tool_data.get('slug', tool_key)
        build('tools-page', ctx, f'tools/{slug}/index.html')

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

    # ─── Tier 3: Detail pages (games, engines, mods) ──────────────────
    details_raw = data.get('details', {})

    def resolve_href(href):
        """Convert rules: prefixes to full URLs."""
        if href.startswith('rules:'):
            return f'https://rules.moddable.games/{href[6:]}/'
        return href

    def prepare_detail_context(detail_key, detail_data, page_type, nav_active):
        """Prepare a detail page context from raw detail data."""
        slug = detail_data.get('slug', detail_key)
        accent = detail_data.get('accent', 'blue')
        accent_color = ACCENT_COLORS.get(accent, '#0c4f8d')
        colors = detail_data.get('colors', {})

        # Determine back link and category tag
        if page_type == 'game':
            back_href = '/games/'
            back_label = 'All games'
            tag_category = 'Original'
            tag_license = 'CC BY-NC-SA'
            og_prefix = 'games'
        elif page_type == 'engine':
            back_href = '/engines/'
            back_label = 'All engines'
            tag_category = 'Engine'
            tag_license = 'Open source'
            og_prefix = 'engines'
        else:
            back_href = '/mods/'
            back_label = 'All mods'
            # Use category from mods.json if available
            mod_item = next((m for m in mods if m.get('path', '').strip('/').split('/')[-1] == slug), None)
            tag_category = mod_item.get('category', 'Mod') if mod_item else 'Mod'
            tag_license = 'CC BY-NC-SA'
            og_prefix = 'mods'

        # Extract version from stats
        tag_version = ''
        for stat in detail_data.get('stats', []):
            if isinstance(stat, list) and len(stat) >= 2:
                if stat[0].lower() in ('version', 'engine', 'updated'):
                    if stat[0].lower() in ('version', 'engine'):
                        tag_version = stat[1]

        # Prepare stats as objects for template
        stats_list = []
        for stat in detail_data.get('stats', []):
            if isinstance(stat, list) and len(stat) >= 2:
                stats_list.append({'label': stat[0], 'value': stat[1]})

        # Prepare hero buttons
        hero_buttons = []
        for btn_data in detail_data.get('buttons', {}).get('hero', []):
            if isinstance(btn_data, list) and len(btn_data) >= 3:
                href = resolve_href(btn_data[1])
                external = href.startswith('http')
                hero_buttons.append({
                    'label': btn_data[0],
                    'href': href,
                    'style': btn_data[2],
                    'external': external,
                })

        # Prepare steps with accent color
        steps = []
        for step in detail_data.get('steps', []):
            steps.append({**step, 'eyebrow_color': accent})

        # Prepare variants
        variants = []
        for v in detail_data.get('variants', []):
            v_accent = v.get('accent', accent)
            featured = bool(v.get('accent') and v.get('accent') != accent)
            link_label = 'Learn more →' if v.get('href') else ''
            variants.append({**v, 'eyebrow_color': v_accent, 'featured': featured, 'link_label': link_label})

        # Prepare hooks with accent color
        hooks = []
        for h in detail_data.get('hooks', []):
            hooks.append({**h, 'accent_color': accent_color})

        # Prepare components
        components = []
        for comp in detail_data.get('components', []):
            components.append({
                'kind': comp['kind'],
                'kind_upper': comp['kind'].upper(),
                'eyebrow_color': accent,
                'list': comp['list'],
            })

        # Prepare community mods
        community = []
        for c in detail_data.get('community', []):
            cat_color = CATEGORY_COLORS.get(c.get('category'), '#0c4f8d')
            community.append({**c, 'category_color': cat_color, 'external': False})

        # Dark center section (for engines or games with special center)
        dark_center = None
        features = detail_data.get('features')
        if features:
            # Engine features section
            engine_cta_btns = []
            for btn_data in detail_data.get('buttons', {}).get('extra', {}).get('engine-cta', []):
                if isinstance(btn_data, list) and len(btn_data) >= 3:
                    href = resolve_href(btn_data[1])
                    engine_cta_btns.append({
                        'label': btn_data[0],
                        'href': href,
                        'style': btn_data[2],
                        'external': href.startswith('http'),
                    })
            dark_center = {
                'eyebrow': 'CAPABILITIES',
                'eyebrow_color': 'glow',
                'heading': 'Play any variant. Build your own',
                'body': '',
                'bloom': colors.get('bloom', ''),
                'pills': features,
                'buttons': engine_cta_btns if engine_cta_btns else None,
            }

        # Lede text from details.json (sourced from original HTML pages)
        lede = detail_data.get('lede', '')

        # Build sections array for template — each section carries its own items
        data_map = {
            'steps': steps,
            'variants': variants,
            'hooks': hooks,
            'factions': detail_data.get('factions'),
            'components': components,
            'community': community,
        }
        template_sections = []
        for sec in detail_data.get('sections', []):
            sec_copy = dict(sec)
            sec_type = sec_copy.get('type', '')
            # Inject items from data
            if sec_type in data_map and data_map[sec_type]:
                sec_copy['items'] = data_map[sec_type]
            # Inject eyebrow_color from accent
            if 'eyebrow_color' not in sec_copy:
                sec_copy['eyebrow_color'] = accent
            # Inject accent_color for hooks/steps items
            if sec_type in ('hooks', 'steps', 'variants', 'components'):
                if sec_copy.get('items'):
                    for item in sec_copy['items']:
                        if 'eyebrow_color' not in item:
                            item['eyebrow_color'] = accent
                        if 'accent_color' not in item:
                            item['accent_color'] = accent_color
            # Dark center: merge features/pills/buttons from old logic
            if sec_type == 'dark_center':
                if not sec_copy.get('pills') and features:
                    sec_copy['pills'] = features
                if not sec_copy.get('buttons') and dark_center and dark_center.get('buttons'):
                    sec_copy['buttons'] = dark_center['buttons']
                if not sec_copy.get('bloom'):
                    sec_copy['bloom'] = colors.get('bloom', '')
            template_sections.append(sec_copy)

        # Build the detail object for template
        detail = {
            'title': detail_data.get('title', ''),
            'slug': slug,
            'accent': accent,
            'accent_color': accent_color,
            'heroImage': detail_data.get('heroImage', ''),
            'colors_gradient': colors.get('gradient', ''),
            'colors_hexGrid': colors.get('hexGrid', ''),
            'colors_textColor': colors.get('textColor', ''),
            'colors_textShadow': colors.get('textShadow', ''),
            'colors_bloom': colors.get('bloom', ''),
            'back_href': back_href,
            'back_label': back_label,
            'tag_category': tag_category,
            'tag_license': tag_license,
            'tag_version': tag_version,
            'lede': lede,
            'hero_buttons': hero_buttons if hero_buttons else None,
            'stats': stats_list if stats_list else None,
            'sections': template_sections,
        }

        # Build output path
        output_path = f'{og_prefix}/{slug}/index.html'

        # CSS bundle
        page_css_id = f'{og_prefix}-{slug}'
        css_bundle = bundle_css(page_css_id, ['detail', 'cards'])

        # Meta
        page_meta = {
            'title': detail_data.get('title', ''),
            'description': lede[:160] if lede else detail_data.get('title', ''),
            'url': f'https://moddable.games/{og_prefix}/{slug}/',
            'image': f'https://moddable.games/img/og/{og_prefix}-{slug}.png',
        }

        nav = mark_nav_active(nav_raw, nav_active)
        ctx = {
            'version': version,
            'nav': nav,
            'year': '2026',
            'site_name': 'Moddable.Games',
            'site_url': 'https://moddable.games',
            'page_id': page_css_id,
            'meta': page_meta,
            'hero': {},
            'css_bundle': css_bundle,
            'detail': detail,
        }
        return ctx, output_path

    # Map detail keys to page types and slugs
    GAME_KEYS = {'nukes': 'nukes', 'mongo': 'planet-mongo', 'endless-skies': 'endless-skies'}
    ENGINE_KEYS = {'chess': 'chess', 'moddable-hexmaps': 'moddable-hexmaps'}
    MOD_SLUGS = set()
    for mod in mods:
        path = mod.get('path', '')
        if path:
            MOD_SLUGS.add(path.strip('/').split('/')[-1])

    for key, detail_data in details_raw.items():
        slug = detail_data.get('slug', key)
        if key in GAME_KEYS:
            ctx, output_path = prepare_detail_context(key, detail_data, 'game', 'Games')
            build('detail', ctx, output_path)
        elif key in ENGINE_KEYS:
            # Write redirect pages for deprecated engine detail pages
            redirect_html = '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta http-equiv="refresh" content="0;url=/developers/engine/">\n<link rel="canonical" href="https://moddable.games/developers/engine/">\n<title>Redirecting…</title>\n</head>\n<body>\n<p>This page has moved to <a href="/developers/engine/">/developers/engine/</a>.</p>\n</body>\n</html>'
            redir_path = os.path.join(ROOT, f'engines/{slug}/index.html')
            os.makedirs(os.path.dirname(redir_path), exist_ok=True)
            with open(redir_path, 'w') as f:
                f.write(redirect_html)
            print(f'  Redirect: engines/{slug}/index.html → /developers/engine/')
        elif slug in MOD_SLUGS:
            ctx, output_path = prepare_detail_context(key, detail_data, 'mod', 'Mods')
            build('detail', ctx, output_path)

    # ─── Team detail pages ─────────────────────────────────────────────
    team_detail_labels = {
        'back': 'Back to team',
        'posts_heading': '',  # Set per-member
        'connect': 'Connect',
        'team': 'Team',
    }
    for member in team_members:
        member_handle = member.get('handle', member.get('slug', ''))
        if not member_handle:
            continue

        # Filter posts by this member
        member_posts = [p for p in news_items if p.get('author') == member.get('name')]

        # Other team members
        teammates = [m for m in team_members if m.get('handle') != member_handle]

        # Labels
        first_name = member.get('name', '').split(' ')[0]
        labels = {**team_detail_labels, 'posts_heading': f'Posts by {first_name}'}

        # CSS bundle
        td_css_id = f'team-{member_handle}'
        css_bundle = bundle_css(td_css_id, ['team-detail'])

        # Meta
        page_meta = {
            'title': member.get('name', ''),
            'description': member.get('bio', ''),
            'url': f'https://moddable.games/team/{member_handle}/',
            'image': f'https://moddable.games/img/og/team-{member_handle}.png',
        }

        nav = mark_nav_active(nav_raw, 'About')
        td_ctx = {
            'version': version,
            'nav': nav,
            'year': '2026',
            'site_name': 'Moddable.Games',
            'site_url': 'https://moddable.games',
            'page_id': td_css_id,
            'meta': page_meta,
            'hero': {},
            'css_bundle': css_bundle,
            'member': member,
            'posts': member_posts if member_posts else None,
            'teammates': teammates,
            'labels': labels,
        }
        build('team-detail', td_ctx, f'team/{member_handle}/index.html')

    # ─── News article pages ──────────────────────────────────────────────
    from urllib.parse import quote as url_quote
    article_labels = news_labels
    content_news_dir = os.path.join(CONTENT_DIR, 'news')
    if os.path.isdir(content_news_dir):
        for post in news_items:
            slug = post.get('slug', '')
            if not slug:
                continue
            md_path = os.path.join(content_news_dir, f'{slug}.md')
            if not os.path.exists(md_path):
                continue

            md_text = read_file(md_path)
            article_html = markdown_to_html(md_text)

            # Author info from team
            author_member = next((m for m in team_members if m.get('slug') == post.get('teamSlug')), None)
            author_gradient = ''
            author_img = ''
            if author_member:
                author_gradient = f"linear-gradient(135deg, {author_member.get('color', '#0c4f8d')}, #0a0d2a)"
                author_img = author_member.get('img', '')

            # Share URLs
            canonical = f"https://moddable.games/news/{slug}/"
            encoded_url = url_quote(canonical, safe='')
            encoded_title = url_quote(f"{post.get('title', '')} — Moddable.Games", safe='')
            share_x = f"https://x.com/intent/tweet?url={encoded_url}&text={encoded_title}"
            share_fb = f"https://www.facebook.com/sharer/sharer.php?u={encoded_url}"
            share_li = f"https://www.linkedin.com/sharing/share-offsite/?url={encoded_url}"

            # Related posts (3 with most tag overlap)
            post_tags = set(post.get('tags', []))
            scored = []
            for p in news_items:
                if p.get('slug') == slug:
                    continue
                overlap = len(post_tags & set(p.get('tags', [])))
                scored.append((overlap, p))
            scored.sort(key=lambda x: -x[0])
            related = [p for _, p in scored[:3]]

            # CSS bundle
            art_css_id = f'news-{slug}'
            css_bundle = bundle_css(art_css_id, ['article', 'cards'])

            # Meta
            page_meta = {
                'title': post.get('title', ''),
                'description': post.get('excerpt', post.get('lede', ''))[:160],
                'url': canonical,
                'image': f"https://moddable.games/img/og/news-{slug}.png",
            }

            nav = mark_nav_active(nav_raw, 'News')
            art_ctx = {
                'version': version,
                'nav': nav,
                'year': '2026',
                'site_name': 'Moddable.Games',
                'site_url': 'https://moddable.games',
                'page_id': art_css_id,
                'meta': page_meta,
                'hero': {},
                'css_bundle': css_bundle,
                'article_html': article_html,
                'author_gradient': author_gradient,
                'author_img': author_img,
                'canonical_url': canonical,
                'share_x': share_x,
                'share_fb': share_fb,
                'share_li': share_li,
                'related': related if related else None,
                'labels': article_labels,
            }
            art_ctx.update(post)
            build('article', art_ctx, f'news/{slug}/index.html')

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

    # ─── Stats + Discovery files ────────────────────────────────────────
    generate_stats(news_items, mods, team_members, tools_pages, details_raw, pages)
    generate_discovery_files(data, news_items, mods, team_members, tools_pages, details_raw)

    print(f'\nBuild complete. Version: {version}')


def generate_stats(news_items, mods, team_members, tools_pages, details_raw, pages):
    """Generate api/stats.json — Web-authoritative stats for universal endpoint."""
    from datetime import datetime, timezone

    # Count all pages built
    content_news_dir = os.path.join(CONTENT_DIR, 'news')
    news_article_count = 0
    if os.path.isdir(content_news_dir):
        news_article_count = len([f for f in os.listdir(content_news_dir) if f.endswith('.md')])

    page_count = (
        len(pages) +                    # tier 1 content pages
        5 +                             # index pages (mods, games, engines, news, tools)
        len(tools_pages) +              # tool sub-pages
        len(team_members) +             # team detail pages
        news_article_count +            # news articles
        len([k for k in details_raw     # game + mod detail pages
             if k in ('nukes', 'mongo', 'endless-skies') or
             details_raw[k].get('slug', k) in
             {m.get('path', '').strip('/').split('/')[-1] for m in mods}]) +
        1                               # home
    )

    stats_data = {
        'project': 'web',
        'generated': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'stats': {
            'pages': page_count,
            'news_articles': news_article_count,
            'mods_listed': len(mods),
            'tools_showcased': len(tools_pages),
            'team_members': len(team_members),
            'games': len([k for k in details_raw if k in ('nukes', 'mongo', 'endless-skies')]),
        }
    }

    stats_path = os.path.join(ROOT, 'api', 'stats.json')
    write_file(stats_path, json.dumps(stats_data, indent=2) + '\n')
    print(f'  Built: api/stats.json ({page_count} pages)')


def generate_discovery_files(data, news_items, mods, team_members, tools_pages, details_raw):
    """Generate sitemap.xml, robots.txt, llms.txt, and .well-known/* files."""
    print('\n  Generating discovery files...')
    counts = data.get('counts', {})

    # Collect all URLs with priorities and change frequencies
    urls = []

    # Home
    urls.append(('https://moddable.games/', 'weekly', '1.0'))

    # Index pages
    urls.append(('https://moddable.games/mods/', 'weekly', '0.9'))
    urls.append(('https://moddable.games/games/', 'monthly', '0.9'))
    urls.append(('https://moddable.games/engines/', 'monthly', '0.8'))
    urls.append(('https://moddable.games/tools/', 'weekly', '0.8'))
    urls.append(('https://moddable.games/news/', 'weekly', '0.8'))
    urls.append(('https://moddable.games/developers/', 'monthly', '0.8'))
    urls.append(('https://moddable.games/developers/engine/', 'monthly', '0.7'))
    urls.append(('https://moddable.games/developers/api/', 'monthly', '0.7'))
    urls.append(('https://moddable.games/developers/examples/', 'monthly', '0.7'))

    # Static pages
    urls.append(('https://moddable.games/about/', 'monthly', '0.7'))
    urls.append(('https://moddable.games/about/roadmap/', 'monthly', '0.6'))
    urls.append(('https://moddable.games/community/', 'monthly', '0.7'))
    urls.append(('https://moddable.games/team/', 'monthly', '0.6'))
    urls.append(('https://moddable.games/press/', 'monthly', '0.6'))
    urls.append(('https://moddable.games/submit/', 'yearly', '0.5'))
    urls.append(('https://moddable.games/subscribe/', 'yearly', '0.5'))

    # Team detail pages
    for member in team_members:
        handle = member.get('handle', '')
        if handle:
            urls.append((f'https://moddable.games/team/{handle}/', 'yearly', '0.5'))

    # Game detail pages
    GAME_KEYS = {'nukes': 'nukes', 'mongo': 'planet-mongo', 'endless-skies': 'endless-skies'}
    for key, slug in GAME_KEYS.items():
        if key in details_raw:
            urls.append((f'https://moddable.games/games/{slug}/', 'monthly', '0.8'))

    # Mod detail pages
    for mod in mods:
        path = mod.get('path', '').strip('/')
        if path:
            urls.append((f'https://moddable.games/{path}/', 'monthly', '0.7'))

    # Tool sub-pages
    for tool_key, tool_data in tools_pages.items():
        slug = tool_data.get('slug', tool_key)
        urls.append((f'https://moddable.games/tools/{slug}/', 'monthly', '0.7'))

    # News articles
    for post in news_items:
        slug = post.get('slug', '')
        if slug:
            md_path = os.path.join(CONTENT_DIR, 'news', f'{slug}.md')
            if os.path.exists(md_path):
                urls.append((f'https://moddable.games/news/{slug}/', 'yearly', '0.6'))

    # Discovery file self-references
    urls.append(('https://moddable.games/api/stats.json', 'daily', '0.5'))
    urls.append(('https://moddable.games/llms.txt', 'monthly', '0.7'))
    urls.append(('https://moddable.games/.well-known/mcp.json', 'monthly', '0.7'))
    urls.append(('https://moddable.games/.well-known/agent-skills/index.json', 'monthly', '0.7'))

    # ─── sitemap.xml ──────────────────────────────────────────────────
    sitemap_lines = ['<?xml version="1.0" encoding="UTF-8"?>',
                     '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, freq, priority in urls:
        sitemap_lines.append(f'  <url><loc>{loc}</loc><changefreq>{freq}</changefreq><priority>{priority}</priority></url>')
    sitemap_lines.append('</urlset>')
    sitemap_lines.append('')
    write_file(os.path.join(ROOT, 'sitemap.xml'), '\n'.join(sitemap_lines))
    print(f'  Built: sitemap.xml ({len(urls)} URLs)')

    # ─── robots.txt ───────────────────────────────────────────────────
    robots = """User-agent: *
Allow: /
Disallow: /build/

Sitemap: https://moddable.games/sitemap.xml

User-agent: GPTBot
Allow: /

User-agent: CCBot
Allow: /

User-agent: anthropic-ai
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: Google-Extended
Allow: /

User-agent: Googlebot
Allow: /

User-agent: Bingbot
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: Bytespider
Allow: /

User-agent: *
Content-Signal: ai-train=yes, search=yes, ai-input=yes
"""
    write_file(os.path.join(ROOT, 'robots.txt'), robots)
    print('  Built: robots.txt')

    # ─── llms.txt ─────────────────────────────────────────────────────
    mod_count = counts.get('mods_count', str(len(mods)))
    tool_count = counts.get('tool_count', '83')
    news_count = str(len(news_items))
    team_count = counts.get('team_count', str(len(team_members)))
    games_count = counts.get('games_count', '3')

    llms_txt = f"""# Moddable.Games

> Open-source engines, community-built mods, and original games designed to be taken apart.

Moddable.Games is a workshop that publishes open-source rulebook mods for existing board games, plus original games designed to be modded from day one. We also build shared engines (Chess, Hexmaps) that power multiple games and tools.

## Data Feeds

These JSON files contain structured data about all our content:

- [Mods Library](https://moddable.games/data/mods.json): {mod_count} rulebook mods
- [Games](https://moddable.games/data/games.json): {games_count} original games (Endless Skies, Planet Mongo, Nukes)
- [Engines](https://moddable.games/data/engines.json): 2 shared engines (Moddable Chess, Moddable Hexmaps)
- [News](https://moddable.games/data/news.json): {news_count} articles about game design and modding
- [Team](https://moddable.games/data/team.json): {team_count} team members

## Key Pages

- [Homepage](https://moddable.games/): Overview and featured content
- [Mods Library](https://moddable.games/mods/): Filterable collection of all mods
- [Games](https://moddable.games/games/): Original games catalogue
- [Engines](https://moddable.games/engines/): Shared engine SDKs
- [Tools](https://moddable.games/tools/): Interactive game tools (dice, drafters, trackers)
- [News](https://moddable.games/news/): Articles on game design and modding philosophy
- [About](https://moddable.games/about/): Mission and approach
- [Community](https://moddable.games/community/): Discord and engagement

## AI Tool Access (MCP)

This site provides {tool_count} AI-callable tools via the Model Context Protocol (MCP) at:

- **MCP endpoint:** https://tools.moddable.games/mcp (SSE transport)
- **REST API:** https://tools.moddable.games/api/call (POST with {{"tool": "name", "args": {{...}}}})
- **OpenAPI spec:** https://tools.moddable.games/openapi.json
- **Agent skills:** https://tools.moddable.games/.well-known/agent-skills/index.json
- **Server card:** https://tools.moddable.games/.well-known/mcp/server-card.json

No authentication required. All tools are free and open.

### Tool Namespaces

- **Chess** (9 tools): variant listing, legal moves, analysis, puzzles, SVG render
- **Hex Maps** (6 tools): map generation, pathfinding, FOV, SVG export
- **Piece Gallery** (3 tools): search/browse 96 chess piece sets
- **Rules Library** (5 tools): game/variant lookup, search, random
- **Game Tools** (12 tools): TI4 drafting, Mancala, Morris, Ur, Pachisi, Nukes, Colony
- **Oracles & RPG** (14 tools): oracle tables, encounters, entity browser (10 RPG systems)
- **Utilities** (7 tools): dice, coins, teams, factions, mod jam

## Open Source

All engines and tools are MIT licensed. Game rules are CC-BY-SA 4.0. Source code available on GitHub.
"""
    write_file(os.path.join(ROOT, 'llms.txt'), llms_txt)
    print('  Built: llms.txt')

    # ─── .well-known/mcp.json (legacy location) ─────────────────────────
    mcp_json = {
        "schema_version": "1.0",
        "name": "Moddable.Games MCP Tools",
        "description": f"{tool_count} AI-callable tools for board game modding, chess variants, hex maps, RPG oracles, and game utilities. Free, open, no authentication required.",
        "url": "https://tools.moddable.games/mcp",
        "transport": "sse",
        "homepage": "https://moddable.games/developers/",
        "documentation": "https://tools.moddable.games/llms.txt",
        "openapi": "https://tools.moddable.games/openapi.json",
        "agent_skills": "https://tools.moddable.games/.well-known/agent-skills/index.json",
        "configSchema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
            "description": "No configuration required. All tools are free and open, no API keys needed."
        }
    }
    mcp_path = os.path.join(ROOT, '.well-known', 'mcp.json')
    write_file(mcp_path, json.dumps(mcp_json, indent=2) + '\n')
    print('  Built: .well-known/mcp.json')

    # ─── .well-known/mcp/server-card.json (SEP-1649) ─────────────────
    server_card = {
        "serverInfo": {
            "name": "Moddable.Games MCP Tools",
            "version": "1.0.0"
        },
        "transport": {
            "type": "sse",
            "url": "https://tools.moddable.games/mcp"
        },
        "capabilities": {
            "tools": True
        },
        "description": f"{tool_count} AI-callable tools for board game modding, chess variants, hex maps, RPG oracles, and game utilities.",
        "homepage": "https://moddable.games/developers/",
        "documentation": "https://tools.moddable.games/llms.txt",
        "openapi": "https://tools.moddable.games/openapi.json",
        "authentication": {
            "type": "none",
            "description": "No authentication required. All tools are free and open."
        }
    }
    card_path = os.path.join(ROOT, '.well-known', 'mcp', 'server-card.json')
    write_file(card_path, json.dumps(server_card, indent=2) + '\n')
    print('  Built: .well-known/mcp/server-card.json')

    # ─── .well-known/api-catalog (RFC 9727) ───────────────────────────
    api_catalog = {
        "linkset": [
            {
                "anchor": "https://moddable.games/.well-known/api-catalog",
                "item": [
                    {
                        "href": "https://tools.moddable.games/api/call",
                        "rel": "item",
                        "service-desc": [
                            {"href": "https://tools.moddable.games/openapi.json", "type": "application/json"}
                        ],
                        "service-doc": [
                            {"href": "https://moddable.games/developers/api/", "type": "text/html"}
                        ]
                    },
                    {
                        "href": "https://tools.moddable.games/mcp",
                        "rel": "item",
                        "service-desc": [
                            {"href": "https://moddable.games/.well-known/mcp/server-card.json", "type": "application/json"}
                        ],
                        "service-doc": [
                            {"href": "https://moddable.games/developers/", "type": "text/html"}
                        ]
                    }
                ]
            }
        ]
    }
    catalog_path = os.path.join(ROOT, '.well-known', 'api-catalog')
    write_file(catalog_path, json.dumps(api_catalog, indent=2) + '\n')
    print('  Built: .well-known/api-catalog')

    # ─── .well-known/agent-skills/index.json ──────────────────────────
    agent_skills = {
        "$schema": "https://schemas.agentskills.io/discovery/0.2.0/schema.json",
        "skills": [
            {
                "name": "moddable-games-tools",
                "type": "skill-md",
                "description": f"{tool_count} AI-callable board game tools: chess variants, hex maps, piece gallery, rules library, RPG oracles, and game utilities via MCP",
                "url": "https://tools.moddable.games/llms.txt",
                "digest": "sha256:placeholder"
            }
        ]
    }
    skills_path = os.path.join(ROOT, '.well-known', 'agent-skills', 'index.json')
    write_file(skills_path, json.dumps(agent_skills, indent=2) + '\n')
    print('  Built: .well-known/agent-skills/index.json')

    # ─── auth.md ──────────────────────────────────────────────────────
    auth_md = f"""# Authentication — Moddable.Games

## API Access

All {tool_count} tools are **free and open**. No authentication required.

### REST API
- **Endpoint:** `POST https://tools.moddable.games/api/call`
- **Auth:** None
- **Body:** `{{"tool": "tool_name", "args": {{...}}}}`

### MCP (Model Context Protocol)
- **Endpoint:** `https://tools.moddable.games/mcp`
- **Transport:** SSE (Server-Sent Events)
- **Auth:** None

### OpenAPI
- **Spec:** `https://tools.moddable.games/openapi.json`

## Rate Limits

No rate limits are currently enforced. Please be respectful of shared resources.

## Agent Registration

No registration required. Connect directly to any endpoint above.
"""
    write_file(os.path.join(ROOT, 'auth.md'), auth_md)
    print('  Built: auth.md')


if __name__ == '__main__':
    build_site()
