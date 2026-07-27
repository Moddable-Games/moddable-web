# moddable-web

Static site generator for [moddable.games](https://moddable.games) — replaces the current client-rendered `moddable-website` repo with server-side built HTML.

## Architecture

### Four-repo model

| Repo | Domain | Hosting | Role |
|------|--------|---------|------|
| **moddable-engine** | engine.moddable.games | GitHub Pages (static) | Game logic SDK (play modules, AI, validation) + asset galleries (pieces, boards, tiles) |
| **moddable-rules** | rules.moddable.games | GitHub Pages (static) | Rulebooks (markdown → HTML) + JSON API (metadata, oracles, entities) |
| **moddable-web** (this) | moddable.games | GitHub Pages (static) | Marketing site (Python SSG) + JSON API (mods, news, team, stats) |
| **moddable-tools** | tools.moddable.games | Cloudflare Worker (private) | MCP server, REST API, game sessions, Discord bot — the ONLY compute |

### Data flow

```
moddable-engine (static: SDK modules + gallery JSON)
moddable-rules  (static: markdown + metadata JSON API)
moddable-web    (static: marketing JSON API)
       │  │  │
       ▼  ▼  ▼
moddable-tools (Worker: imports engine SDK at bundle time,
                fetches rules + web + engine APIs at runtime,
                runs all compute, serves MCP + REST + game sessions)
```

### Key principles

1. **Tools is the only compute** — the single Cloudflare Worker, the only private repo; imports engine SDK, fetches from all three static APIs at runtime
2. **Engine is a public library, not a service** — publishes importable JS modules (move gen, AI, validation, rendering, play modules for local/pass-and-play); tools bundles them at deploy time; engine's static site serves galleries and enables local play without sessions
3. **Every other repo serves static JSON APIs** — predictable URLs at their domains, no Workers needed, consumable by tools or any external client
4. **Web is the marketing site** — moddable.games; all content JSON-driven so tools, Discord bot, and agents can consume the same material
5. **Rules stays separate** — rules.moddable.games renders its own markdown; also exposes structured JSON (game metadata, oracle tables, entity indexes) for tools to fetch at runtime
6. **moddable-website stays live** — this repo replaces it incrementally; the old site runs untouched until web can fully replicate its content
7. **Tools is private** — holds secrets, Durable Objects for multiplayer sessions, player state, PvP logic; the only repo that needs to be private. Engine handles local play (vs AI, pass-and-play) publicly; tools adds the networked/session layer on top

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
| Engine publishes SDK modules | moddable-engine | Extract game logic into importable JS; expose static gallery APIs |
| Engine absorbs chess/hexmaps | moddable-engine | Import game logic from moddable-chess/hexmaps, replace those repos |
| Rules exposes JSON API | moddable-rules | Serve metadata, oracle tables, entity indexes as static JSON |
| Tools becomes standalone | moddable-tools (new, private) | Extract Worker from moddable-website; import engine SDK; fetch APIs |
| Web pages built incrementally | moddable-web | This plan — page-by-page migration |
| Agent-readiness | all repos | Issues #129, #60, #235, #34 |

### Dependency chain

- Engine SDK must exist before tools can import it (currently tools bundles chess/hex JS directly)
- Rules JSON API must exist before tools stops bundling oracle-data.json / rules-index.json
- Web JSON API must exist before tools fetches marketing content at runtime
- None of this blocks the web SSG migration (web reads its own local JSON for now, transitions to serving it as API later)

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

#### 2026-07-27
- Integrated @moddable/tools-sdk (v0.2.0) for all tool page embeds and API calls
- All tool pages now use SDK embed helpers instead of manual iframe creation
- Chess puzzles use tools.chess.renderSvg() instead of raw fetch
- Dice, decks, oracles: full-width tabbed layout (embed provides own chrome)
- TI4, nukes, talisman: hex map card + embed section below (awaiting tools-side deploy for tools embeds)
- Hexmap controls reclassed to proper hexmap-embed CSS (no longer borrowing chess styles)
- Removed redundant jumpnavs where embed widgets provide internal navigation
- Template extended with embed_id section for bare embed containers below cards
- Closed #2 (superseded by SDK approach), closed #4 (SDK integration complete)
- Created moddable-tools #19 (chess SVG missing pieces), #20 (embed card mode)

#### 2026-07-25
- Tool sub-pages: 7 per-game tool page shells built (ti, talisman, nukes, dice, decks, chess, oracles)
- New template: tools-page.html handles 3 layout variants (card-based, tabbed, duo) via data flags
- tools-pages.json: per-page config (slug, CSS/JS, jumpnav, tool cards, engine bands)
- Per-game CSS copied from original site (9 files)
- Heroes + meta entries for all 7 tool sub-pages
- 52 pages total, 12 templates
- GitHub issue #2: complete inventory of 48 interactive mount points awaiting moddable-tools JS
- Phase 3 complete: detail pages (7 mods, 3 games, 2 engines, 4 team members)
- News articles: 14 pages from markdown with HTML passthrough (callouts, figures, video embeds)
- Markdown converter with lede detection, HTML block passthrough, heading ID generation
- counts.json: single-source dynamic numbers (tool count, variant count, etc.) substituted at build time
- Image consolidation: all assets under img/ (press, team, news, og, tools)
- OG image generation scripts (Pillow-based, data-driven from heroes.json/meta.json)
- Subscribe/submit pages fixed to match original (3-step form, benefits section, correct class prefixes)
- Article template: 3-column layout with author card, TOC, share buttons, related posts
- Detail template: fully section-driven (each page declares its own section order, types, headings)

#### 2026-07-24
- Phase 0-2 complete: SSG infrastructure, 15 pages built
- Custom Python template engine with nested block support
- Per-page CSS bundling (build-time concatenation)
- --base flag for local development under subdirectories
- 7 templates producing all pages (page.html handles 8 via data-driven sections)
- Homepage built with all sections (hero, gallery, featured, dev band, nukes, news, community)
- All CSS and fonts carried from moddable-website
- UX-only JS (hamburger, dropdown, parallax, scroll-reveal)

#### 2026-07-23
- Repository created
- Architecture plan documented
- Parallel workstream model established
