import { tools } from './mg-tools-common.js'

const VARIANTS = [
  { key: 'standard', label: 'Standard', group: 'Classic' },
  { key: 'chess960', label: 'Chess960', group: 'Classic' },
  { key: 'torpedo', label: 'Torpedo', group: 'Classic' },
  { key: 'atomic', label: 'Atomic', group: 'Tactical' },
  { key: 'kingOfTheHill', label: 'King of the Hill', group: 'Tactical' },
  { key: 'threeCheck', label: 'Three-Check', group: 'Tactical' },
  { key: 'antichess', label: 'Antichess', group: 'Alternate Rules' },
  { key: 'racingKings', label: 'Racing Kings', group: 'Alternate Rules' },
  { key: 'crazyhouse', label: 'Crazyhouse', group: 'Alternate Rules' },
  { key: 'duckChess', label: 'Duck Chess', group: 'Alternate Rules' },
  { key: 'horde', label: 'Horde', group: 'Asymmetric' },
  { key: 'capablanca', label: 'Capablanca', group: 'Large Boards' },
  { key: 'losAlamos', label: 'Los Alamos', group: 'Small Boards' },
  { key: 'minichess', label: 'Minichess', group: 'Small Boards' },
]

// --- Chess Explorer ---

const body = document.getElementById('chess-explorer-body')
if (body) {
  let currentVariant = 'standard'

  const controls = document.createElement('div')
  controls.className = 'chess-explorer__controls'

  const variantSelect = document.createElement('select')
  variantSelect.className = 'chess-explorer__select'
  VARIANTS.forEach(v => {
    const opt = document.createElement('option')
    opt.value = v.key
    opt.textContent = v.label
    if (v.key === currentVariant) opt.selected = true
    variantSelect.appendChild(opt)
  })
  controls.appendChild(variantSelect)

  const diffSelect = document.createElement('select')
  diffSelect.className = 'chess-explorer__select'
  ;['beginner', 'easy', 'medium', 'hard', 'expert'].forEach(d => {
    const opt = document.createElement('option')
    opt.value = d
    opt.textContent = d.charAt(0).toUpperCase() + d.slice(1)
    if (d === 'medium') opt.selected = true
    diffSelect.appendChild(opt)
  })
  controls.appendChild(diffSelect)

  const newBtn = document.createElement('button')
  newBtn.textContent = 'New Game'
  newBtn.className = 'chess-explorer__btn'
  controls.appendChild(newBtn)

  const undoBtn = document.createElement('button')
  undoBtn.textContent = 'Undo'
  undoBtn.className = 'chess-explorer__btn'
  controls.appendChild(undoBtn)

  const flipBtn = document.createElement('button')
  flipBtn.textContent = 'Flip'
  flipBtn.className = 'chess-explorer__btn'
  controls.appendChild(flipBtn)

  body.appendChild(controls)

  const wrap = document.createElement('div')
  wrap.className = 'chess-explorer__embed'
  body.appendChild(wrap)

  const embed = tools.embed.play(wrap, {
    params: { family: 'chess', variant: 'standard' },
    title: 'Play Chess',
    height: 560,
  })

  variantSelect.addEventListener('change', () => {
    currentVariant = variantSelect.value
    embed.setVariant(currentVariant)
  })
  diffSelect.addEventListener('change', () => {
    embed.setDifficulty(diffSelect.value)
  })
  newBtn.addEventListener('click', () => embed.newGame())
  undoBtn.addEventListener('click', () => embed.undo())
  flipBtn.addEventListener('click', () => embed.flip())

  const statusBar = document.createElement('div')
  statusBar.className = 'chess-explorer__status'
  statusBar.textContent = 'White to move'
  body.appendChild(statusBar)

  window.addEventListener('message', (e) => {
    if (!e.data || typeof e.data.type !== 'string') return
    const type = e.data.type
    if (type === 'game:ready' || type === 'chess:ready') {
      statusBar.textContent = 'White to move'
    }
    if (type === 'game:move' || type === 'chess:move') {
      const turn = e.data.fen && e.data.fen.includes(' b ') ? 'Black' : 'White'
      statusBar.textContent = turn + ' to move'
    }
    if (type === 'game:status' || type === 'chess:status') {
      statusBar.textContent = e.data.text === 'draw' ? 'Draw' :
        e.data.text === 'white' ? 'White wins' :
        e.data.text === 'black' ? 'Black wins' : e.data.text
    }
  })
}

// --- Puzzle Gallery ---

const puzzleBody = document.getElementById('chess-puzzle-body')
if (puzzleBody) {
  let allPuzzles = []
  let puzzleVariants = []
  let currentPuzzleVariant = ''
  let filteredPuzzles = []
  let puzzleIdx = 0
  let svgCache = {}

  function variantLabel(key) {
    return key.replace(/([A-Z])/g, ' $1').replace(/^./, c => c.toUpperCase()).trim()
  }

  async function initPuzzles() {
    puzzleBody.innerHTML = '<div class="chess-puzzle__loading">Loading puzzles...</div>'
    try {
      const engineBase = location.hostname === 'localhost'
        ? location.origin + '/MODDABLE/moddable-engine/api/'
        : 'https://engine.moddable.games/api/'
      const res = await fetch(engineBase + 'puzzles/index.json')
      const data = await res.json()
      allPuzzles = []
      if (data.standard) allPuzzles.push(...data.standard.map(p => ({ ...p, variant: p.variant || 'standard' })))
      if (data.variants) allPuzzles.push(...data.variants)
      const varSet = new Set(allPuzzles.map(p => p.variant))
      puzzleVariants = Array.from(varSet).sort()
      currentPuzzleVariant = ''
      applyPuzzleFilter()
      renderPuzzle()
    } catch (e) {
      puzzleBody.innerHTML = '<div class="chess-puzzle__error">Could not load puzzles.</div>'
    }
  }

  function applyPuzzleFilter() {
    filteredPuzzles = currentPuzzleVariant
      ? allPuzzles.filter(p => p.variant === currentPuzzleVariant)
      : allPuzzles
    puzzleIdx = 0
  }

  function renderPuzzle() {
    puzzleBody.innerHTML = ''

    const controls = document.createElement('div')
    controls.className = 'chess-puzzle__controls'

    const sel = document.createElement('select')
    sel.className = 'chess-explorer__select'
    const allOpt = document.createElement('option')
    allOpt.value = ''
    allOpt.textContent = 'All variants (' + allPuzzles.length + ')'
    if (!currentPuzzleVariant) allOpt.selected = true
    sel.appendChild(allOpt)
    puzzleVariants.forEach(v => {
      const count = allPuzzles.filter(p => p.variant === v).length
      const opt = document.createElement('option')
      opt.value = v
      opt.textContent = variantLabel(v) + ' (' + count + ')'
      if (v === currentPuzzleVariant) opt.selected = true
      sel.appendChild(opt)
    })
    sel.addEventListener('change', () => {
      currentPuzzleVariant = sel.value
      applyPuzzleFilter()
      renderPuzzle()
      loadPuzzleBoard()
    })
    controls.appendChild(sel)
    puzzleBody.appendChild(controls)

    if (!filteredPuzzles.length) {
      puzzleBody.appendChild(Object.assign(document.createElement('div'), {
        className: 'chess-puzzle__loading', textContent: 'No puzzles found.'
      }))
      return
    }

    const p = filteredPuzzles[puzzleIdx]

    const meta = document.createElement('div')
    meta.className = 'chess-puzzle__meta'
    meta.appendChild(Object.assign(document.createElement('span'), {
      className: 'chess-puzzle__tag', textContent: variantLabel(p.variant)
    }))
    if (p.themes && p.themes.length) {
      meta.appendChild(Object.assign(document.createElement('span'), {
        className: 'chess-puzzle__tag chess-puzzle__tag--type', textContent: p.themes[0]
      }))
    }
    if (p.rating) {
      meta.appendChild(Object.assign(document.createElement('span'), {
        className: 'chess-puzzle__tag', textContent: 'Rating: ' + p.rating
      }))
    }
    puzzleBody.appendChild(meta)

    const boardWrap = document.createElement('div')
    boardWrap.className = 'chess-puzzle__board'
    boardWrap.id = 'puzzle-board'
    if (svgCache[p.id]) {
      boardWrap.innerHTML = svgCache[p.id]
    } else {
      boardWrap.innerHTML = '<div class="chess-puzzle__loading">Rendering board...</div>'
    }
    puzzleBody.appendChild(boardWrap)

    if (p.fen) {
      const fenWrap = document.createElement('div')
      fenWrap.className = 'chess-puzzle__fen'
      fenWrap.innerHTML = '<span class="chess-puzzle__fen-label">FEN</span><code class="chess-puzzle__fen-value">' + p.fen + '</code>'
      puzzleBody.appendChild(fenWrap)
    }

    const toMove = p.fen ? (p.fen.split(' ')[1] === 'w' ? 'White' : 'Black') : ''
    const hint = document.createElement('div')
    hint.className = 'chess-puzzle__hint'
    hint.textContent = toMove ? toMove + ' to move. Find the winning move.' : 'Find the winning move.'
    puzzleBody.appendChild(hint)

    const solWrap = document.createElement('div')
    solWrap.className = 'chess-puzzle__sol-wrap'
    const solBtn = document.createElement('button')
    solBtn.className = 'chess-explorer__btn'
    solBtn.textContent = 'Show solution'
    solBtn.addEventListener('click', () => {
      const moves = Array.isArray(p.solution) ? p.solution.join(', ') : p.solution
      solBtn.replaceWith(Object.assign(document.createElement('div'), {
        className: 'chess-puzzle__solution', textContent: moves
      }))
      loadPuzzleBoardHighlight(p)
    })
    solWrap.appendChild(solBtn)
    puzzleBody.appendChild(solWrap)

    const nav = document.createElement('div')
    nav.className = 'chess-puzzle__nav'
    const prevBtn = document.createElement('button')
    prevBtn.className = 'chess-explorer__btn'
    prevBtn.textContent = 'Prev'
    prevBtn.addEventListener('click', () => {
      puzzleIdx = (puzzleIdx - 1 + filteredPuzzles.length) % filteredPuzzles.length
      renderPuzzle()
      loadPuzzleBoard()
    })
    const counter = document.createElement('span')
    counter.className = 'chess-puzzle__counter'
    counter.textContent = (puzzleIdx + 1) + ' / ' + filteredPuzzles.length
    const nextBtn = document.createElement('button')
    nextBtn.className = 'chess-explorer__btn'
    nextBtn.textContent = 'Next'
    nextBtn.addEventListener('click', () => {
      puzzleIdx = (puzzleIdx + 1) % filteredPuzzles.length
      renderPuzzle()
      loadPuzzleBoard()
    })
    nav.appendChild(prevBtn)
    nav.appendChild(counter)
    nav.appendChild(nextBtn)
    puzzleBody.appendChild(nav)

    if (!svgCache[p.id]) loadPuzzleBoard()
  }

  async function loadPuzzleBoard() {
    const p = filteredPuzzles[puzzleIdx]
    if (!p || svgCache[p.id]) return
    try {
      const result = await tools.chess.renderSvg({ variant: p.variant, fen: p.fen })
      const svg = (result.result || result).svg
      if (svg) {
        svgCache[p.id] = svg
        const boardEl = document.getElementById('puzzle-board')
        if (boardEl && filteredPuzzles[puzzleIdx] && filteredPuzzles[puzzleIdx].id === p.id) {
          boardEl.innerHTML = svg
        }
      }
    } catch (e) {}
  }

  async function loadPuzzleBoardHighlight(p) {
    const move = Array.isArray(p.solution) ? p.solution[0] : p.solution
    if (!move) return
    const highlights = [move.slice(0, 2), move.slice(2, 4)]
    try {
      const result = await tools.chess.renderSvg({ variant: p.variant, fen: p.fen, highlights })
      const svg = (result.result || result).svg
      if (svg) {
        const boardEl = document.getElementById('puzzle-board')
        if (boardEl) boardEl.innerHTML = svg
      }
    } catch (e) {}
  }

  initPuzzles()
}

// --- Engine CTA buttons ---

const engineBtns = document.getElementById('engine-btns')
if (engineBtns) {
  const engineUrl = location.hostname === 'localhost'
    ? '/MODDABLE/moddable-engine/'
    : 'https://engine.moddable.games/'

  const playBtn = document.createElement('a')
  playBtn.href = engineUrl
  playBtn.className = 'chess-engine-band__btn chess-engine-band__btn--primary'
  playBtn.textContent = 'Moddable Engine'
  playBtn.setAttribute('target', '_blank')
  playBtn.setAttribute('rel', 'noopener')
  engineBtns.appendChild(playBtn)

  const srcBtn = document.createElement('a')
  srcBtn.href = 'https://github.com/Moddable-Games/moddable-engine'
  srcBtn.className = 'chess-engine-band__btn chess-engine-band__btn--outline'
  srcBtn.textContent = 'View Source'
  srcBtn.setAttribute('target', '_blank')
  srcBtn.setAttribute('rel', 'noopener')
  engineBtns.appendChild(srcBtn)
}
