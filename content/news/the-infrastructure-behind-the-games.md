The future of tabletop gaming is not bound by cardboard and plastic. We believe that board gaming will never reach its full potential if held back by physical boards. The modern tabletop community is growing faster than ever, yet the tools that power creativity, collaboration and global play remain limited in their scope or overflowing with complexities. Physical board games are beautiful, tactile and social, but they are also constrained by their components and environment, which can often limit the creativity that goes into games.

So, we are building a bridge.

Behind the scenes, we have been developing moddable online engines that launched alongside our first game, [Nukes](/games/nukes/). They serve as digital companions to our games, but they also act as a foundation for a new ecosystem where physical and digital coexist, where creators thrive and where the boundaries of what a "board game" can be are rewritten by the people actually playing them.

## Infinite hex worlds

Our core engine is built specifically for hex-based systems. Hexagonal grids are the backbone of many of the world's most loved strategy games: Catan, Twilight Imperium, Suburbia, Memoir 44. The format spans every genre from resource trading to wargaming. Our engine currently powers six of our own games and mods, but the architecture is designed to support any hex-based system.

The reason we are building our own is to push the limits towards infinite maps and truly open worlds. Imagine thousands of players interacting on a single, continuous world, where exploration never ends and where every action ripples across a shared universe. We want to build games that have the capability to work with any number of players, and the only way to prove that they can is by building a platform to enable a board to be any size with support for any number of players.

We want to be able to build moddable games, and for those games to be easily moddable by its users. You.

## Moddable Hexmaps

[Hexmaps](/engines/moddable-hexmaps/) is that platform made real. It generates, renders, and edits hex-based game boards via Canvas. Flat-top or pointy-top, any ring count, seeded RNG for reproducible generation, click-to-edit, JSON export/import, and a full URL param API for embedding. Six games already consume it:

- **[Nukes](/games/nukes/)** — territory maps with terrain generation across 2-6 rings
- **[Talisman Worlds](/mods/talisman-worlds/)** — ring-based adventure boards with encounters
- **[Twilight Imperium](/mods/hyper-imperium/)** — galaxy layouts from 3 to 8 players
- **Colony** — Seafarers-style terrain with number token constraints
- **[Planet Mongo](/games/planet-mongo/)** — 127-hex planetary conquest maps
- **[Endless Skies](/games/endless-skies/)** — frontier exploration with wormholes and nebulae

Each game registers through `HexApp.registerGame` with its own terrain palette, generation rules, and editor controls. The engine handles coordinate math, rendering, sidebar UI, and embed bridging. The game plugin handles flavour.

[![Hexmaps engine rendering a Nukes game board](/img/news/nukes-online.png)](https://hex.moddable.games)

## Moddable Chess Engine

While Hexmaps powers our spatial games, [MCE](/engines/moddable-chess/) powers everything with pieces that move. A modular chess engine with 74 playable variants across boards from 4x8 to 12x8. Its architecture is plugin-based: each variant is a self-contained file that registers custom pieces, rules, win conditions, and board layouts through a declarative API.

[Dungeon Chess](/mods/dungeon-chess/) is the most extreme consumer. Four factions, 24 units, terrain hazards, special abilities, and AI opponents, all running on the same engine as Fischer Random and Atomic Chess. It needed everything: custom rendering, terrain, capture interception, multi-step turns. The engine had to become a platform, not a library.

[![Dungeon Chess board running on the Moddable Chess Engine](/img/news/the-infrastructure-behind-the-games.jpg)](https://chess.moddable.games)

## Moddable Rules

The third pillar in our open engine architecture is still in development. Moddable Rules is a shared rulebook system that builds themed, paginated rulebooks from structured content. Every game and mod gets a versioned rulebook built from the same design tokens, fonts, and layout components.

It already ships rulebooks for [Nukes](/games/nukes/), [Hyper Imperium](/mods/hyper-imperium/), [Econopoly](/mods/econopoly/), [Dungeon Chess](/mods/dungeon-chess/), and [Talisman Worlds](/mods/talisman-worlds/). The build system generates OG images, search indices, and print-ready PDFs from the same source files. When it stabilises, it becomes the content layer that feeds into everything else. The engines handle play. The rules handle publishing. One game definition, multiple outputs.

## Plugin architecture

The four MCE developer guides demonstrate different categories of extensibility:

1. **[Orda](https://chess.moddable.games/docs/guide-orda.html)** — separate move logic from capture logic
2. **[Crazyhouse](https://chess.moddable.games/docs/guide-crazyhouse.html)** — moves from hand, not board (hand management)
3. **[Poison](https://chess.moddable.games/docs/guide-poison.html)** — state on tiles, not pieces (timed effects)
4. **[Dungeon Chess](https://chess.moddable.games/docs/guide-dungeon-chess.html)** — all of the above plus terrain and interception

Together they proved that one engine can host everything from a five-line rule tweak to a complete standalone game. The same principle drives Hexmaps: Nukes needs combat mechanics on hexes while Talisman needs encounter draws, but both share coordinate math, rendering, and generation.

## Open-source everything

This means designing something new and open, whilst also building a business around it. For designers, this means rapid prototyping on hex-based games of any scale. For players, it means completely new types of shared experiences. For the games themselves, it means a platform and community, not just a product.

**Build on our engines**
Both engines are MIT-licensed. Fork them, embed them, build your own game on top. No permission needed. Game rules are CC BY-SA, so you can remix any of our published content and release your own version. If you can write a JSON config and a few lines of JavaScript, you can ship a playable variant today.

Three engines. One philosophy. The rules define the game. The engines make it playable. The platform makes it shareable. Everything is open, everything connects, and everything is designed to be taken apart by someone with a better idea. If you're building a hex game, a chess variant, or something we've not imagined yet, the infrastructure is here and waiting. [Come build with us.](/community/)
