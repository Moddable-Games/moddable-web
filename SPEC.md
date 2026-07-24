# moddable-web Implementation Spec

## Goal

Replace moddable-website's client-rendered pages with server-built static HTML. Same content, same styles, same URLs. The only difference: content is in the HTML source instead of injected by JS at runtime.

---

## Current state (moddable-website)

28 page JS files render all content client-side. Data comes from:
- `data/*.json` (13 files) — mods, games, news, team, tools, chess variants, TI4
- `data/articles/*.html` (14 files) — pre-rendered article bodies
- Hardcoded arrays in page JS (tools, roadmap, community, press, about, dice, talisman, nukes)
- Live API calls to `tools.moddable.games/api/call` (oracle tools, chess tools, developer API page)

---

## Pages to migrate (31 total)

### Tier 1: Pure content (no interactivity) — 14 pages
These render static content from JSON or hardcoded data. No live API calls.

| Page | Current source | Data needed |
|------|---------------|-------------|
| `/about/` | mg-about-page.js (hardcoded) | About content JSON |
| `/about/roadmap/` | mg-roadmap-page.js (hardcoded) | Roadmap milestones JSON |
| `/community/` | mg-community-page.js (hardcoded) | Community content JSON |
| `/press/` | mg-press-page.js (hardcoded) | Press stats/assets JSON |
| `/team/` | mg-team-page.js | `data/team.json` |
| `/team/mark/` | mg-team-detail-page.js | `data/team.json` + `data/news.json` |
| `/team/kevin/` | mg-team-detail-page.js | (same) |
| `/team/akmal/` | mg-team-detail-page.js | (same) |
| `/team/iqbal/` | mg-team-detail-page.js | (same) |
| `/subscribe/` | mg-subscribe-page.js | None (form only) |
| `/submit/` | mg-submit-page.js | None (form only) |
| `/developers/` | mg-developers-page.js (hardcoded) | Developer content JSON |
| `/developers/examples/` | mg-developers-examples-page.js | Examples JSON |
| `/404.html` | mg-404-page.js | None |

### Tier 2: Index pages with filter/search — 5 pages
Content renders statically; JS adds filter/search interactivity on top.

| Page | Current source | Data needed |
|------|---------------|-------------|
| `/mods/` | mg-mods-index-page.js | `data/mods.json` |
| `/games/` | mg-games-index-page.js | `data/games.json` |
| `/engines/` | mg-engines-index-page.js | `data/engines.json` |
| `/news/` | mg-news-index-page.js | `data/news.json` |
| `/tools/` | mg-tools-page.js | Tools sections JSON |

### Tier 3: Detail pages — 10 pages (templated)
Each uses the same template with different data.

| Page pattern | Current source | Data needed |
|------|---------------|-------------|
| `/mods/<slug>/` (×11) | mg-mod-page.js | `data/mods.json` |
| `/games/<slug>/` (×3) | mg-game-page.js | `data/games-content.json` |
| `/engines/moddable-chess/` | mg-engine-chess-page.js | Engine content JSON |
| `/engines/moddable-hexmaps/` | mg-engine-hexmaps-page.js | Engine content JSON |
| `/news/<slug>/` (×14) | mg-news-article-page.js | `data/news.json` + `data/articles/<slug>.html` |

### Tier 4: Tool pages — 8 pages (widgets from ENGINE, embedded here)

The interactive tools are **embeddable widgets produced by moddable-engine** (web components or iframe-ready pages). They call moddable-tools' API for compute. moddable-web embeds them to prove they're consumable.

| Page | Widget source | API backend |
|------|--------------|-------------|
| `/tools/chess/` | engine (chess widget) | tools API (move gen, puzzles) |
| `/tools/ti/` | engine (TI4 widget) | tools API (draft, objectives) |
| `/tools/oracles/` | engine (oracle widget) | tools API (oracle roll, scenes) |
| `/tools/dice/` | engine (dice widget) | tools API (dice roll) |
| `/tools/decks/` | engine (deck widget) | tools API (deck ops) |
| `/tools/talisman/` | engine (talisman widget) | tools API (character data) |
| `/tools/nukes/` | engine (nukes widget) | tools API (setup, tracking) |
| `/developers/api/` | engine (playground widget) | tools API (any tool call) |

**Separation of concerns:**
- **Engine** produces the widgets (UI components, embeddable, data-driven)
- **Tools** provides the API backend (compute, data fetching from rules)
- **Web** embeds the widgets on `/tools/*` pages (proves they're consumable, marketing showcase)

**What moddable-web does:** Renders static `/tools/` hub page listing all tools (from tools API at build time). Each sub-page embeds the engine's widget and provides the surrounding marketing context (description, related tools, CTAs). The widget does the interactive work; web just hosts it.

### Tier 5: Home page — 1 page
Complex hero, featured content, multiple sections.

| Page | Current source | Data needed |
|------|---------------|-------------|
| `/` | mg-home-page.js | `data/mods.json`, `data/news.json`, hardcoded stats |

---

## Data extraction plan

Content currently hardcoded in page JS must move to `data/*.json`:

| New JSON file | Source | Content |
|---------------|--------|---------|
| `data/about.json` | mg-about-page.js | Mission text, links, sidebar |
| `data/roadmap.json` | mg-roadmap-page.js | Milestones, vision items, timeline |
| `data/community.json` | mg-community-page.js | Stats, channels, mod jams, Discord info |
| `data/press.json` | mg-press-page.js | Brand stats, colour values, asset links |
| `data/developers.json` | mg-developers-page.js | Feature cards, integration steps |
| `data/examples.json` | mg-developers-examples-page.js | Code examples array |
| `data/tools-sections.json` | mg-tools-page.js | Tool sections, presets, tool cards |
| `data/home.json` | mg-home-page.js | Featured content, stats, tab configs |
| `data/heroes.json` | All page JS hero configs | Eyebrow, title, lede, accent per page |
| `data/nav.json` | mg-navbar.js | Navigation structure, active states |

Existing `data/*.json` files carry over unchanged.

---

## API endpoints needed from tools (at build time)

The build script fetches these from `tools.moddable.games` to get live counts/stats:

| Endpoint | Data used |
|----------|-----------|
| `GET /api/tools` | Total tool count, namespace counts, tool names |
| `GET /.well-known/agent-skills/index.json` | Skill descriptions |

That's it for build time. The interactive tool pages (Tier 4) still call the API at runtime in the browser — that doesn't change.

---

## Build phases

### Phase 0: Infrastructure
- [ ] `build/build.py` — template engine (substitute, loops, conditionals, partials)
- [ ] `build/templates/_base.html` — document shell
- [ ] `build/templates/_navbar.html` — static navbar partial
- [ ] `build/templates/_footer.html` — static footer partial
- [ ] `build/templates/_hero.html` — hero section partial
- [ ] `css/` — copy all CSS from moddable-website unchanged
- [ ] `js/mg-enhance.js` — thin UX JS (hamburger, parallax, reveal, search)
- [ ] `data/nav.json` + `data/heroes.json` — extracted from current JS
- [ ] Prove with `/about/` — visual comparison must be pixel-identical

### Phase 1: Tier 1 pages (14 pages)
- [ ] Extract hardcoded content → JSON for each page
- [ ] Write templates for: about, roadmap, community, press, team, team-detail, subscribe, submit, developers, examples, 404
- [ ] Build generates all 14 pages
- [ ] Visual diff: screenshot comparison vs live site

### Phase 2: Tier 2 index pages (5 pages)
- [ ] Templates for: mods-index, games-index, engines-index, news-index, tools-hub
- [ ] Card partials: `_card-mod.html`, `_card-game.html`, `_card-news.html`
- [ ] Filter/search JS preserved as enhancement (works without JS, enhanced with JS)
- [ ] Extract tools-sections hardcoded data → JSON

### Phase 3: Tier 3 detail pages (28+ pages from templates)
- [ ] Mod detail template (×11 pages from `data/mods.json`)
- [ ] Game detail template (×3 pages from `data/games-content.json`)
- [ ] Engine detail templates (chess, hexmaps)
- [ ] News article template (×14 pages from `data/news.json` + article HTML bodies)
- [ ] Build generates all detail pages from data

### Phase 4: Tier 4 interactive tool pages (8 pages)
- [ ] Static content rendered in template (descriptions, headings, layouts)
- [ ] Interactive widgets as standalone JS modules (not content renderers)
- [ ] Tools that call `tools.moddable.games/api/call` keep that pattern (client-side fetch)
- [ ] Tools with hardcoded data (dice, talisman, nukes): move data to JSON, render labels statically

### Phase 5: Home page
- [ ] Extract home page data → `data/home.json`
- [ ] Home template with hero, featured sections, stats, news feed
- [ ] Hero animations via CSS + UX JS (not content JS)

### Phase 6: Discovery files + deploy
- [ ] Build generates: `robots.txt`, `sitemap.xml`, `llms.txt`, `.well-known/*`
- [ ] `bump.sh` stamps version across all CSS/JS refs
- [ ] GitHub Pages / Cloudflare Pages deploy config
- [ ] Full visual regression: every page compared to live site

### Phase 7: Cutover
- [ ] DNS: moddable.games points to this repo
- [ ] Verify: all URLs return 200, all content matches
- [ ] Archive moddable-website (read-only)

---

## Hosting: Cloudflare Pages

Both moddable-web and moddable-tools are the first projects to use **Cloudflare Pages** (not GitHub Pages). Benefits:

- `_headers` file for Link headers, Content-Type overrides, cache control
- `_redirects` file for URL management
- Build command integration (run `python build/build.py` on deploy)
- Preview deployments per branch
- Edge caching with instant purge
- Free tier (unlimited sites, unlimited bandwidth, 500 builds/month)

---

## Template strategy: minimal templates, maximum reuse

### Principle: as few templates as possible

The 31 pages are produced from **7 templates** (not 31). Templates use conditionals and loops to adapt based on JSON data — sections appear or disappear based on what's in the data.

| Template | Produces | Pages |
|----------|----------|-------|
| `_base.html` | Document shell (wraps everything) | All 31 |
| `page.html` | Generic content page | about, roadmap, community, press, developers, examples, subscribe, submit, 404 (9) |
| `index.html` | Card grid with optional filter | mods, games, engines, news, tools indexes (5) |
| `detail.html` | Detail page with hero + content sections | mod details (11), game details (3), engine details (2), team details (4) = 20 |
| `article.html` | News article with TOC + author | news articles (14) |
| `team-index.html` | Team grid | team index (1) |
| `home.html` | Home page (unique layout) | home (1) |

**Total: 7 templates produce 31+ pages.**

### How templates stay minimal

The `page.html` template handles 9 different pages because it's data-driven:

```html
{{>_base}}
{{>_hero}}

{{#each sections}}
  {{#if type "cards"}}{{>_section-cards}}{{/if}}
  {{#if type "stats"}}{{>_section-stats}}{{/if}}
  {{#if type "text"}}{{>_section-text}}{{/if}}
  {{#if type "cta"}}{{>_section-cta}}{{/if}}
  {{#if type "grid"}}{{>_section-grid}}{{/if}}
{{/each}}
```

The JSON for each page declares which sections appear and in what order. The template just iterates.

Similarly, `detail.html` handles mods, games, engines, AND team detail pages because they all follow the same pattern: hero → content blocks → related items → CTA. The differences are in the data, not the template.

### Shared partials (snippets reused across all templates)

| Partial | Used by | Purpose |
|---------|---------|---------|
| `_base.html` | All templates | Document shell (head, body open/close, CSS/JS refs) |
| `_navbar.html` | All (via _base) | Main navigation (single source, active state from data) |
| `_footer.html` | All (via _base) | Footer (single source) |
| `_hero.html` | All page templates | Hero section (adapts via data: dark/light, eyebrow, title, lede, accent) |
| `_meta.html` | All (via _base) | OG tags, Twitter cards, JSON-LD (driven by page metadata) |
| `_card-mod.html` | index, home | Mod card component |
| `_card-game.html` | index, home | Game card component |
| `_card-news.html` | index, home | News card component |
| `_section-cards.html` | page, home | Generic card grid section |
| `_section-stats.html` | page, detail | Stats row (numbers + labels) |
| `_section-text.html` | page, detail | Rich text block |
| `_section-cta.html` | page, detail | Call-to-action band |

**Navbar, footer, and hero are NEVER hardcoded into page templates.** They are always `{{>_partial}}` includes — one source file, rendered everywhere. Change the nav once, every page updates on next build.

---

## Template engine requirements

The template engine must support:

- `{{>partial}}` — includes (critical for nav/footer/hero reuse)
- `{{#each items}}...{{/each}}` — loops (card grids, sections, lists)
- `{{#if value}}...{{/if}}` — conditionals (show/hide sections based on data)
- `{{#if key "value"}}` — equality checks (section type matching)
- `{{variable}}` — escaped substitution
- `{{{raw}}}` — unescaped HTML (for pre-rendered content like article bodies)
- Nested partials (a partial can include other partials)
- Data passed to partials (hero partial receives hero config from page data)

---

## Validation criteria

A page is "done" when:
1. HTML source contains all readable content (no empty shells)
2. Disabling JS shows all content (interactive widgets may be non-functional)
3. Screenshot comparison with live site shows no visual difference
4. All links work (relative paths correct for depth)
5. OG meta tags present and correct
6. Page appears in generated sitemap.xml

---

## What does NOT change

- CSS files (carried over byte-for-byte where possible)
- Design tokens, colours, fonts, spacing
- Page URLs and structure
- OG images
- Content copy (every word stays the same)
- Interactive tool behaviour (chess explorer, dice roller, oracle — all work identically)
