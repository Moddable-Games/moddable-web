<p class="lede">If chess was designed today, how would it differ? It's a question that's occupied a decade of research, several prototypes and can only be answered after first understanding where deterministic strategy games come from.</p>

Three classical games define the space:

- **[Checkers](https://rules.moddable.games/dist/draughts/)** (5,000 years ago) established simplicity as the standard. Minimal components, minimal rules, maximum accessibility.
- **[Go](https://rules.moddable.games/dist/go/)** (4,000 years ago) introduced epic scope whilst remaining teachable in minutes. Two piece types with more possibilities than atoms in the universe.
- **[Chess](https://rules.moddable.games/dist/moddable-chess/)** (1,500 years ago) pioneered unique pieces with individual movement rules. Miniature components. Character and narrative baked into the mechanics.

All three share constraints. They only support two players, have static boards, and fixed starting positions. For 5,000 years, that was the template.

## The predictability problem

Chess's opening theory is so deeply mapped that grandmasters routinely play 15-20 moves from memory before original thought begins. The fixed 8x8 grid with identical starting positions means the game's possibility space, while enormous, is increasingly charted. Computers solved this before most of us were born.

The game has become, in large part, a game of memorization rather than strategy. That is not a criticism of chess. It is an observation about what happens to any game played on the same board a billion times. Even with 70+ [variants](https://chess.moddable.games):

<figure>
  <a href="https://chess.moddable.games" target="_blank" rel="noopener"><img src="/img/engine-chess-screenshot.png" alt="Moddable Chess Engine showing Grand Chess variant on a 10x10 board" loading="lazy"></a>
  <figcaption>70+ variants on one engine. What if you changed everything else?</figcaption>
</figure>

## Hexagons and infinite setups

The solution begins with the board. Replace squares with hexagons. Six neighbours instead of four. No diagonal ambiguity. Clean adjacency that scales naturally to any number of players.

Then make it modular. Boards should have an infinite number of possible setups, which also enables an infinite number of players. Introduce biomes: terrain types that modify movement and engagement. Suddenly, every game starts from a unique configuration. Memorization becomes worthless. Only strategy survives.

> "If you change the board, you change the game. If you make the board modular, you make the game infinite."

This is the principle behind our [Hexmaps engine](/engines/moddable-hexmaps/): procedural hex grids that generate a different board every session. The same engine powers [Nukes](/games/nukes/), [Talisman Worlds](/mods/talisman-worlds/), and [Endless Skies](/games/endless-skies/).

## Accessibility first

Modern board games have trended toward increasing complexity and cost. Hundreds of miniatures, 60-page rulebooks, four-figure investments. Chess's genius was always its accessibility: 32 pieces, 64 squares, rules you can teach in ten minutes.

Go proved the same point differently: two piece types, one placement rule, infinite depth. Any modern reimagining must honour that accessibility while expanding the strategic canvas. Fewer unique components with more emergent complexity. Simple rules, yet infinite expression. This defined our scope:

<div class="prose-callout">
  <strong>Design constraints</strong>
  <ul>
    <li>A simple system that allows for any number of players</li>
    <li>A modular board with endless possibilities</li>
    <li>As few unique components as possible</li>
  </ul>
</div>

## The game we built

The result of that decade of thinking is [Nukes](/games/nukes/): a deterministic hex strategy game with 2 component types, 5 biomes, and infinite board configurations. No dice. No cards. No hidden information. Any number of players.

Where chess has 7 distinct piece types and 10^40 possible games, Nukes has 2 component types and effectively infinite possibilities. Go achieves 10^800 positions with a 19x19 grid, whereas Nukes matches that scope with just 44 modular hex tiles.

<figure>
  <a href="https://nukes.moddable.games" target="_blank" rel="noopener"><img src="/img/news/nukes-online.png" alt="Nukes game board showing hex tiles and token positions" loading="lazy"></a>
  <figcaption>44 hex tiles &amp; zero dice. Playable at nukes.moddable.games.</figcaption>
</figure>

The philosophy behind it: modular boards, emergent strategy and [open-source rules](/news/open-sourcing-tabletop-games/). It has become the foundation of everything we publish. Read the full story in [Nuking Catan](/news/nuking-catan/), where we explain how 45 million people already own the board.
