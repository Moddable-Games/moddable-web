(function() {
  'use strict';

  var TOOLS_API = 'https://tools.moddable.games/api/call';

  var INDEX = [
    {type:'mod', title:'Dungeon Chess', desc:'Chess reimagined as asymmetric dungeon skirmish', href:'/mods/dungeon-chess/'},
    {type:'mod', title:'Talisman Worlds', desc:'Open-world hex system replacing the Talisman board', href:'/mods/talisman-worlds/'},
    {type:'mod', title:'Hyper Imperium', desc:'Faster ruleset for TI4 + Prophecy of Kings', href:'/mods/hyper-imperium/'},
    {type:'mod', title:'Econopoly', desc:'Monopoly with a working economy and dynamic pricing', href:'/mods/econopoly/'},
    {type:'mod', title:'Nukes: Siege', desc:'Asymmetric attacker/defender variant for Nukes', href:'/mods/nukes-siege/'},
    {type:'mod', title:'Nukes: Asymmetric Powers', desc:'Faction abilities and unique unit compositions', href:'/mods/nukes-asymmetric-powers/'},
    {type:'mod', title:'Nukes: Fallout', desc:'Post-war survival expansion with irradiated terrain', href:'/mods/nukes-fallout/'},
    {type:'game', title:'Nukes', desc:'Cold-war territory control on a hex map', href:'/games/nukes/'},
    {type:'game', title:'Planet Mongo', desc:'Hex-based territory control in the Flash Gordon universe', href:'/games/planet-mongo/'},
    {type:'game', title:'Endless Skies', desc:'4X space exploration with worker placement and fleet management', href:'/games/endless-skies/'},
    {type:'engine', title:'Moddable Engine', desc:'133 variants across 6 game families — chess, draughts, go, shogi, xiangqi, reversi', href:'/developers/engine/'},
    {type:'tool', title:'Dice Roller', desc:'Roll any combination of dice for any game', href:'/tools/dice/'},
    {type:'tool', title:'Card Deck Builder', desc:'Build and shuffle custom card decks', href:'/tools/decks/'},
    {type:'tool', title:'TI4 Tools', desc:'Galaxy maps, faction picker, objectives, agendas', href:'/tools/ti/'},
    {type:'tool', title:'Talisman Tools', desc:'Character lottery, hex board generator, encounters', href:'/tools/talisman/'},
    {type:'tool', title:'Chess Variant Explorer', desc:'100 variants with 5 AI difficulty levels', href:'/tools/chess/'},
    {type:'tool', title:'Nukes Tools', desc:'Hex map generator, combat calculator, hostage tracker', href:'/tools/nukes/'},
    {type:'tool', title:'Oracles & RPG', desc:'Scene Forge, RPG Browser, Encounter Builder for 10 systems', href:'/tools/oracles/'},
    {type:'page', title:'About', desc:'Our story and what we believe', href:'/about/'},
    {type:'page', title:'Developers', desc:'Engine, Tools API, build examples', href:'/developers/'},
    {type:'page', title:'Tools API', desc:'81 AI-callable tools across 8 namespaces', href:'/developers/api/'},
    {type:'page', title:'Community', desc:'Join the Discord — designers, playtesters, rule-tinkerers', href:'/community/'},
    {type:'page', title:'Subscribe', desc:'Crowdfunding updates, playtest invites, game launches', href:'/subscribe/'},
    {type:'page', title:'Submit a Mod', desc:'Share your homebrew with the community', href:'/submit/'},
    {type:'page', title:'News', desc:'Essays, announcements, and build logs', href:'/news/'},
    {type:'page', title:'Press Kit', desc:'Logos, screenshots, brand colours for editorial use', href:'/press/'},
  ];

  var overlay = null;
  var activeIdx = 0;

  function searchRulesAPI(query) {
    return fetch(TOOLS_API, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tool: 'rules_search', args: { query: query, limit: 5 } }),
    })
      .then(function(r) { return r.json(); })
      .then(function(d) {
        return (d.results || []).map(function(entry) {
          return {
            type: 'rule',
            title: entry.heading,
            desc: entry.gameTitle + ' — ' + entry.section,
            href: 'https://rules.moddable.games/' + (entry.variantUrl || ('dist/' + entry.game + '/')) + '#' + entry.anchor
          };
        });
      })
      .catch(function() { return []; });
  }

  function renderResults(container, query, rulesHits) {
    container.innerHTML = '';
    if (!query) {
      container.innerHTML = '<div class="mg-search-panel__empty"><div class="mg-search-panel__empty-title">Start typing to search</div><div class="mg-search-panel__empty-hint">Mods, games, rules, news, and tools</div></div>';
      return;
    }
    var q = query.toLowerCase();
    var localMatches = INDEX.filter(function(item) {
      return item.title.toLowerCase().indexOf(q) !== -1 || item.desc.toLowerCase().indexOf(q) !== -1;
    });
    var matches = localMatches.concat(rulesHits || []).slice(0, 10);
    if (matches.length === 0) {
      container.innerHTML = '<div class="mg-search-panel__empty"><div class="mg-search-panel__empty-title">No results</div><div class="mg-search-panel__empty-hint">Try a different search term</div></div>';
      return;
    }
    activeIdx = 0;
    matches.forEach(function(item, i) {
      var a = document.createElement('a');
      a.href = item.href;
      a.className = 'mg-search-result' + (i === 0 ? ' mg-search-result--active' : '');
      if (item.href.indexOf('http') === 0) { a.target = '_blank'; a.rel = 'noopener'; }
      a.innerHTML = '<span class="mg-search-result__type mg-search-result__type--' + item.type + '">' + item.type + '</span>' +
        '<div class="mg-search-result__content"><div class="mg-search-result__title">' + item.title + '</div>' +
        '<div class="mg-search-result__desc">' + item.desc + '</div></div>';
      container.appendChild(a);
    });
  }

  function openSearch() {
    if (overlay) { closeSearch(); return; }

    overlay = document.createElement('div');
    overlay.className = 'mg-search-overlay';

    var panel = document.createElement('div');
    panel.className = 'mg-search-panel';

    var header = document.createElement('div');
    header.className = 'mg-search-panel__header';
    var input = document.createElement('input');
    input.type = 'text';
    input.className = 'mg-search-panel__input';
    input.placeholder = 'Search mods, games, rules, tools…';
    header.appendChild(input);
    panel.appendChild(header);

    var results = document.createElement('div');
    results.className = 'mg-search-panel__results';
    panel.appendChild(results);

    var footer = document.createElement('div');
    footer.className = 'mg-search-panel__footer';
    footer.innerHTML = '<div class="mg-search-panel__footer-hint"><span><kbd>↑↓</kbd> navigate</span><span><kbd>↵</kbd> open</span><span><kbd>esc</kbd> close</span></div>';
    panel.appendChild(footer);

    overlay.appendChild(panel);
    document.body.appendChild(overlay);

    requestAnimationFrame(function() { overlay.classList.add('mg-search-overlay--visible'); input.focus(); });
    renderResults(results, '', []);

    var rulesTimer = null;
    input.addEventListener('input', function() {
      var val = input.value.trim();
      renderResults(results, val, []);
      clearTimeout(rulesTimer);
      if (val.length >= 2) {
        rulesTimer = setTimeout(function() {
          searchRulesAPI(val).then(function(hits) { renderResults(results, val, hits); });
        }, 300);
      }
    });

    input.addEventListener('keydown', function(e) {
      var items = results.querySelectorAll('.mg-search-result');
      if (e.key === 'ArrowDown') { e.preventDefault(); activeIdx = Math.min(activeIdx + 1, items.length - 1); }
      else if (e.key === 'ArrowUp') { e.preventDefault(); activeIdx = Math.max(activeIdx - 1, 0); }
      else if (e.key === 'Enter' && items[activeIdx]) { e.preventDefault(); items[activeIdx].click(); return; }
      else if (e.key === 'Escape') { closeSearch(); return; }
      else return;
      items.forEach(function(it, i) { it.classList.toggle('mg-search-result--active', i === activeIdx); });
    });

    overlay.addEventListener('click', function(e) { if (e.target === overlay) closeSearch(); });
  }

  function closeSearch() {
    if (!overlay) return;
    overlay.classList.remove('mg-search-overlay--visible');
    var ref = overlay;
    setTimeout(function() { if (ref.parentNode) ref.parentNode.removeChild(ref); }, 200);
    overlay = null;
  }

  document.addEventListener('keydown', function(e) {
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') { e.preventDefault(); openSearch(); }
    if (e.key === 'Escape') closeSearch();
  });

  var trigger = document.querySelector('.mg-search-trigger');
  if (trigger) {
    trigger.addEventListener('click', function(e) { e.preventDefault(); openSearch(); });
  }
})();
