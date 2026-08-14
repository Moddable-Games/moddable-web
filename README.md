# moddable-web

Static site generator for [moddable.games](https://moddable.games) — replaces the current client-rendered `moddable-website` repo with server-side built HTML.

## Architecture

### Four-repo model

| Repo | Domain | Hosting | Role |
|------|--------|---------|------|
| **moddable-engine** | engine.moddable.games | GitHub Pages (static) | Game logic SDK (play modules, AI, validation) + asset galleries (pieces, boards, tiles) |
| **moddable-rules** | rules.moddable.games | GitHub Pages (static) | Rulebooks (markdown → HTML) + JSON API (metadata, oracles, entities) |
| **moddable-web** (this) | moddable.games | Cloudflare Workers (static assets) | Marketing site (Python SSG) + JSON API (mods, news, team, stats) |
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
6. **moddable-website deprecated** — this repo replaces it; the old site is being archived
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
| Universal stats API | `tools.moddable.games/api/stats` fetched at build time | Live counts from all 4 projects → `data/counts.json` |
| Local JSON | `data/*.json` with `{{counts.X}}` substitution | Marketing content: page copy, descriptions, features, hero configs, nav, team, news, meta |

**Universal stats** = the build fetches `tools.moddable.games/api/stats` which aggregates live counts from engine, rules, tools, and web. These are written to `data/counts.json` and substituted into all data files via `{{counts.X}}` placeholders. Falls back gracefully if offline.

**Local JSON** = authored marketing content for the site. Structured as JSON (not markdown) so the same data can be served via API to other consumers (Discord bot, AI agents, partner integrations). Numbers in these files ALWAYS use `{{counts.X}}` — never hardcode stats.

**Web's own stats** = the build generates `.well-known/stats.json` with page count, news articles, mods listed, etc. This feeds back into the universal endpoint.

Rules content lives at rules.moddable.games — this site links to it but does not import or render it.

### Build process

```
python build/build.py
```

1. Fetches universal stats from `tools.moddable.games/api/stats` → refreshes `data/counts.json`
2. Loads all data JSON (with `{{counts.X}}` substitution applied)
3. Renders all templates → writes static HTML
4. Generates `.well-known/stats.json` (Web's contribution to universal endpoint)
5. Generates discovery files (sitemap.xml, llms.txt, .well-known/*)
6. Bundles CSS per page

Output goes directly to repo root. Cloudflare Pages deploys from `main`.

## Universal stats

All stats across the ecosystem are dynamically derived — zero hardcoded numbers.

```
engine.moddable.games/api/stats.json  ─┐
rules.moddable.games/api/stats.json   ─┤
tools (local stats)                    ─┼─→ tools.moddable.games/api/stats (universal)
moddable.games/.well-known/stats.json  ─┘
                                            │
                                            ▼
                              build.py fetches → data/counts.json → {{counts.X}} in templates
```

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

#### 2026-08-09
- Universal stats system: build fetches `tools.moddable.games/api/stats` at start, refreshes all counts dynamically
- Web generates `.well-known/stats.json` (page count, news, mods, tools showcased) — feeds into universal endpoint
- All data JSON files converted to `{{counts.X}}` — zero hardcoded stats remaining
- Added counts keys: rules_variants, rules_families, rpg_systems, oracle_tables, entities, engine_board_families
- Removed duplicate counts (chess_variants vs engine_variants clarified: chess=family-specific playable, engine=total playable)
- Fixed stale values across site: pieces 96→115, tools 81→84, puzzles 1557→1876, games 3→46, variants 147→296
- Agent-readiness: build now generates full discovery layer (sitemap.xml, robots.txt, llms.txt, auth.md, .well-known/mcp.json, .well-known/mcp/server-card.json, .well-known/api-catalog, .well-known/agent-skills/index.json)
- Added _headers file for Cloudflare Pages Link response headers (RFC 8288 agent discovery)
- MCP server card updated to SEP-1649 format (serverInfo.name, serverInfo.version, transport, capabilities)
- API catalog added per RFC 9727 (linkset+json pointing to REST API and MCP endpoints)
- Content-Signal directives in robots.txt (ai-train=yes, search=yes, ai-input=yes)
- Created issues for agent-readiness across all repos: moddable-tools #24/#25, moddable-engine #104, moddable-rules #251

#### 2026-08-14
- chess_variants now derived from engine.playableByFamily.chess API (was hardcoded to 100, now 136)
- Community page bot commands fetched dynamically from tools.moddable.games/api/bot-commands at build time
- Removed stale commands (/validate, /openings, /moves, /analyze), added 12 new ones (32 total across 10 groups)
- Added User-Agent header to all API fetches (Cloudflare was blocking Python's default UA, causing silent fallback)
- Stats refreshed: engine_variants 133→169, chess_variants 100→136, tool_count 84→85

#### 2026-08-11
- Switched to hosted SDK from tools.moddable.games/sdk.js (deleted local copy)
- Tools index page now embeds live rules widget and tabbed gamenight widget
- Fixed single-tab widgets showing unnecessary tab bar (source fix in moddable-tools)
- API page namespace cards now deep-link to anchored sections on tools.moddable.games
- Decks page supports hash-based tab selection (#custom deep-links to custom builder)
- Embedded interactive API explorer widget on /developers/api/ page (dark theme, inside CTA card)
- Added embed section type and js_files support to page template
- Added SDK explorer() method + theme param to moddable-tools SDK
- Fixed explorer embed infinite resize loop (100vh → fixed height)
- Added predeploy sync script to eliminate SDK source drift in moddable-tools
- Closed #10, #11, #12, #13, #14

#### 2026-08-07
- PRODUCTION LAUNCH — moddable.games now served by this repo via Cloudflare Workers
- Wired oracles, talisman, and nukes embed widgets (all three now live from tools.moddable.games)
- All 7 tool pages fully functional with production embeds — zero remaining stub pages
- Added wrangler.jsonc + .assetsignore for Cloudflare Pages Worker deployment
- Created dev branch (local development); main = production deploys
- moddable-website archived
- Closed final open issue (#1 Visual QA)
- All API URLs switched from staging to production (tools.moddable.games is live with 81 tools)
- New unified Engine page at /developers/engine/ (133 variants, 6 families, assets, SDK)
- New /developers/api/ page (8 namespaces, connection methods, CTA to live explorer)
- New /developers/examples/ page (6 build ideas)
- Cmd+K universal search overlay (local index + rules API search)
- Engines removed from top-level nav, consolidated under Developers
- Legacy /engines/* URLs meta-redirect to /developers/engine/
- Updated tool/variant counts (all derived from universal stats API)
- Added icon-card style to section-cards partial (accent borders, 3-col grid)
- Developers index now 2x2 grid with 4 cards
- Version bumped to 2.1.0

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
