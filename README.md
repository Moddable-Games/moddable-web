# moddable-web

Static site generator for [moddable.games](https://moddable.games) — replaces the current client-rendered `moddable-website` repo with server-side built HTML.

## Architecture

### Three-repo model

| Repo | Role | Owns |
|------|------|------|
| **moddable-engine** | Game logic, tools, MCP server | Chess engine, hex maps, piece gallery, oracles, game tools, Worker |
| **moddable-rules** | Content as markdown | Game rulesets, variant descriptions, oracle tables, entity data |
| **moddable-web** (this) | Static site build | Templates, CSS, interactive JS, build script, deploy |

### Data flow

```
moddable-rules (markdown)
       │
       ▼
moddable-engine (consumes rules, serves tools API)
       │
       ▼
moddable-web (SSG consumes engine API + rules markdown → static HTML)
       │
       ▼
GitHub Pages / Cloudflare Pages (moddable.games)
```

### Key principles

1. **Engine is the single provider** — web calls `tools.moddable.games/api/*` for all dynamic data, never imports game logic directly
2. **Engine has no game knowledge** — variant descriptions, flavour text, rules, and oracle tables live in moddable-rules; engine consumes them
3. **Rules is pure markdown** — structured content that both humans and AI agents can consume natively
4. **Web is pure output** — Python SSG renders templates using data from engine API + markdown from rules; no game logic in this repo
5. **moddable-website stays live** — this repo replaces it incrementally; the old site runs untouched until web can fully replicate its content

### Agent-readiness by design

The SSG produces real HTML content (not JS-rendered shells), making pages natively consumable by AI agents. Discovery files (robots.txt, llms.txt, .well-known/mcp.json, agent-skills) are generated as part of the build.

## SSG: Custom Python (zero dependencies)

A single `build/build.py` script using only Python standard library. No pip, no venv, no node_modules.

### Template engine

- `{{variable}}` — substitution
- `{{{raw}}}` — unescaped HTML
- `{{>partial}}` — includes
- `{{#each items}}...{{/each}}` — loops
- `{{#if value}}...{{/if}}` — conditionals

### Data sources

Dynamic data is API-driven. Content flows from the rules repo as markdown.

| Source | Method | Content |
|--------|--------|---------|
| Engine API | HTTP fetch at build time | Dynamic data: tool listings, variant counts, piece gallery stats, game states, live stats |
| Rules markdown | Git submodule or file path | Content: game descriptions, rulebooks, articles, oracle table descriptions, flavour text |
| Local config | `data/*.json` | Build config: template paths, hero layout params, nav structure, CSS class mappings, page metadata |

**API-driven** = anything that changes when the engine deploys (tool counts go up, new variants added, piece sets change). The build fetches this live so the site stays current without manual updates.

**Content** = authored markdown in moddable-rules. Flows into templates as rendered HTML. Changes when someone writes or edits a rulebook.

**Config** = how pages are assembled and styled. Changes only when we redesign a page layout.

### Build process

```
python build/build.py
```

1. Fetches ALL content from engine API (tools, games, mods, rules markdown, stats, team, news)
2. Renders all templates with fetched data → writes static HTML
3. Generates discovery files (sitemap.xml, llms.txt, .well-known/*)
4. Stamps version + cache-busting params

Output goes directly to repo root (GitHub Pages compatible). No /dist folder.

The build fails loudly if the engine API is unreachable — no fallback to stale local data. This ensures the site always reflects current engine state.

## Migration plan

This repo grows incrementally while moddable-website continues serving production traffic.

### Phase 0: Scaffold (current)
- Repo structure, build script skeleton, base templates
- CSS copied from moddable-website (shared design system unchanged)
- Prove with one simple page (e.g. about)

### Phase 1: Simple content pages
- About, press, community, team, subscribe, 404
- These pages have no interactive widgets — pure template rendering
- Validate: page-for-page visual match with current site

### Phase 2: Index pages
- Mods, games, engines, news indexes
- Card rendering in templates (not JS)
- Search/filter stays as client-side JS enhancement

### Phase 3: Detail pages
- Mod detail pages, news articles, team profiles
- Articles sourced from rules markdown where applicable

### Phase 4: Complex pages
- Tools hub and tool sub-pages (content is static HTML; tools themselves are iframes/embeds from engine)
- Home page (hero animations via CSS/UX JS, content is static)
- Developers/API page

### Phase 5: Cutover
- DNS switch: moddable.games points to this repo's deploy
- moddable-website archived
- Old repo's Workers (discord bot, forms API) already independent

## Parallel workstreams

These happen independently and don't block each other:

| Stream | Repo | Work |
|--------|------|------|
| Engine absorbs chess/hexmaps | moddable-engine | Import game logic, replace moddable-chess |
| MCP Worker moves to engine | moddable-engine | Issue moddable-website#139 |
| Web pages built incrementally | moddable-web | This plan |
| Rules content grows | moddable-rules | More games, variants, oracle tables |
| Agent-readiness issues | all repos | Issues #129, #60, #235, #34 |

## JavaScript philosophy

JS is for interface/UX only — never for content rendering or data fetching at runtime.

**JS does:**
- Hamburger menu toggle
- Dropdown hover interactions
- Scroll-reveal animations
- Hero parallax effects
- Cmd+K search overlay
- Mobile nav behaviour

**JS does NOT:**
- Render cards, lists, or page content
- Fetch data from APIs at runtime
- Build navigation or footer
- Inject text, stats, or descriptions

Everything the user reads is baked into HTML at build time. If a page has no JS enabled, all content is still visible and readable.

## Directory structure (target)

```
/
├── build/
│   ├── build.py              ← main build script
│   └── templates/
│       ├── _base.html        ← document shell (head, body open/close)
│       ├── _navbar.html      ← static navbar partial
│       ├── _footer.html      ← static footer partial
│       ├── _hero.html        ← hero section partial
│       ├── _card-mod.html    ← mod card partial
│       ├── _card-game.html   ← game card partial
│       ├── about.html
│       ├── community.html
│       ├── mods-index.html
│       ├── mod-detail.html
│       └── ...
├── data/
│   ├── nav.json              ← navigation structure
│   ├── heroes.json           ← hero configs per page
│   └── meta.json             ← OG tags, page titles, descriptions
├── css/
│   └── _mg.css               ← shared design system (carried from current site)
├── js/
│   └── mg-enhance.js         ← thin UX-only JS (hamburger, parallax, reveal, search)
├── img/                       ← static assets
├── .well-known/               ← agent discovery files (generated by build)
├── robots.txt                 ← generated by build
├── sitemap.xml                ← generated by build
├── llms.txt                   ← generated by build
├── version.txt
├── bump.sh
└── index.html                 ← built output (committed, serves via GitHub Pages)
```

## What this is NOT

- Not a rewrite of the design system (CSS stays the same)
- Not a new visual design (pixel-for-pixel match with current site)
- Not a framework migration (no React, no Astro, no Next)
- Not blocking on engine migration (can start now with direct data file reads)

## Changelog

#### 2026-07-23
- Repository created
- Architecture plan documented
- Parallel workstream model established
