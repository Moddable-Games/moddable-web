# moddable-web

Static site generator for [moddable.games](https://moddable.games) — replaces the current client-rendered `moddable-website` repo with server-side built HTML.

## Architecture

### Three-repo model

| Repo | Role | Owns |
|------|------|------|
| **moddable-engine** | Game logic, tools, MCP server | Chess engine, hex maps, piece gallery, oracles, game tools, Worker |
| **moddable-rules** | Rulebooks as markdown → HTML | Game rulesets, variant rules, oracle tables — rendered at rules.moddable.games |
| **moddable-web** (this) | Marketing site (moddable.games) | Templates, CSS, UX JS, build script — consumes engine API for dynamic data |

### Data flow

```
moddable-engine (serves tools API — dynamic counts, stats, listings)
       │
       ▼
moddable-web (SSG fetches API at build time → renders static HTML)
       │
       ▼
GitHub Pages / Cloudflare Pages (moddable.games)
```

Rules remains its own project and domain (rules.moddable.games). Web links to it but does not consume its markdown directly.

### Key principles

1. **Engine is the single API provider** — web calls `tools.moddable.games/api/*` for all dynamic data (tool counts, variant listings, game stats, piece gallery)
2. **Web is the marketing site** — moddable.games, presenting the project to humans and AI agents; all content is JSON-driven so other consumers can reuse the same data
3. **Rules stays separate** — rules.moddable.games renders its own markdown to HTML; web links to it but doesn't import from it
4. **JSON-driven content** — all marketing content (descriptions, stats, features, copy) lives in JSON so the engine API, Discord bot, and any future consumer can access the same material
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

All content is JSON-driven so that multiple consumers (website, Discord bot, API clients, AI agents) can access the same material.

| Source | Method | Content |
|--------|--------|---------|
| Engine API | HTTP fetch at build time | Dynamic data: tool listings, variant counts, piece gallery stats, game states, live stats |
| Local JSON | `data/*.json` | Marketing content: page copy, descriptions, features, hero configs, nav structure, team, news, meta |

**API-driven** = anything that changes when the engine deploys (tool counts go up, new variants added, piece sets change). The build fetches this live so the site stays current without manual updates.

**Local JSON** = authored marketing content for the site. Structured as JSON (not markdown) so the same data can be served via API to other consumers (Discord bot, AI agents, partner integrations).

Rules content lives at rules.moddable.games — this site links to it but does not import or render it.

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

- **Not a redesign** — all pages look identical to the current site
- **Not a rewrite** — same content, same copy, same styles; the only changes are structural (templates instead of JS rendering)
- **Not a restyling** — CSS is carried over as-is, not refactored or rewritten
- **Not a content refresh** — all text, descriptions, and copy stay exactly as they are
- **Not a framework migration** — no React, no Astro, no Next
- **Not blocking on engine migration** — can start now with direct data file reads

The goal is to move from client-rendered to server-built while changing as little as possible. If a page looks different after migration, that's a bug.

## Changelog

#### 2026-07-23
- Repository created
- Architecture plan documented
- Parallel workstream model established
