const ENGINE_BASE = location.hostname === 'localhost'
  ? '/MODDABLE/moddable-engine/play/'
  : 'https://engine.moddable.games/play/'

const GAME_MAP = {
  'nukes-hexmap': { game: 'nukes', styles: ['artistic', 'classic', 'kenney'], sizes: [2, 3, 4, 5, 6], defaultSize: 4 },
  'talisman-hexmap': { game: 'talisman', styles: ['artistic', 'classic'], sizes: [3, 4, 5], defaultSize: 3 },
  'ti-galaxy': { game: 'twilight', styles: ['artistic', 'classic'], layouts: ['3p', '4p', '5p', '6p', '7p', '8p'], defaultLayout: '6p' },
}

const embedCard = document.querySelector('.hexmap-embed')
if (embedCard) {
  const config = GAME_MAP[embedCard.id] || GAME_MAP['nukes-hexmap']
  const controlsEl = document.getElementById('hexmap-controls')
  const frameEl = document.getElementById('hexmap-frame-wrap')
  const actionsEl = document.getElementById('hexmap-actions')

  let currentStyle = config.styles[0]
  let currentSize = config.defaultSize || null
  let currentLayout = config.defaultLayout || null
  let hexIframe = null

  function sendMessage(type, data = {}) {
    if (hexIframe && hexIframe.contentWindow) {
      hexIframe.contentWindow.postMessage({ type, ...data }, '*')
    }
  }

  // Controls
  if (controlsEl) {
    const controls = document.createElement('div')
    controls.className = 'hexmap-embed__control-row'

    if (config.styles.length > 1) {
      const styleSelect = document.createElement('select')
      styleSelect.className = 'chess-explorer__select'
      config.styles.forEach(s => {
        const opt = document.createElement('option')
        opt.value = s
        opt.textContent = s.charAt(0).toUpperCase() + s.slice(1)
        if (s === currentStyle) opt.selected = true
        styleSelect.appendChild(opt)
      })
      styleSelect.addEventListener('change', () => {
        currentStyle = styleSelect.value
        sendMessage('hexmap:setStyle', { style: currentStyle })
      })
      controls.appendChild(styleSelect)
    }

    if (config.sizes) {
      const sizeSelect = document.createElement('select')
      sizeSelect.className = 'chess-explorer__select'
      config.sizes.forEach(s => {
        const opt = document.createElement('option')
        opt.value = s
        opt.textContent = 'Size ' + s
        if (s === currentSize) opt.selected = true
        sizeSelect.appendChild(opt)
      })
      sizeSelect.addEventListener('change', () => {
        currentSize = parseInt(sizeSelect.value)
        sendMessage('hexmap:regenerate', { size: currentSize, random: true })
      })
      controls.appendChild(sizeSelect)
    }

    if (config.layouts) {
      const layoutSelect = document.createElement('select')
      layoutSelect.className = 'chess-explorer__select'
      config.layouts.forEach(l => {
        const opt = document.createElement('option')
        opt.value = l
        opt.textContent = l.toUpperCase()
        if (l === currentLayout) opt.selected = true
        layoutSelect.appendChild(opt)
      })
      layoutSelect.addEventListener('change', () => {
        currentLayout = layoutSelect.value
        const players = parseInt(currentLayout)
        sendMessage('hexmap:regenerate', { players, random: true })
      })
      controls.appendChild(layoutSelect)
    }

    const regenBtn = document.createElement('button')
    regenBtn.className = 'chess-explorer__btn'
    regenBtn.textContent = 'Regenerate'
    regenBtn.addEventListener('click', () => sendMessage('hexmap:regenerate', { random: true }))
    controls.appendChild(regenBtn)

    controlsEl.appendChild(controls)
  }

  // Iframe
  if (frameEl) {
    hexIframe = document.createElement('iframe')
    const params = new URLSearchParams({
      embed: '1',
      game: config.game,
      style: currentStyle,
      random: '1',
    })
    if (currentSize) params.set('size', currentSize)
    if (currentLayout) params.set('players', parseInt(currentLayout))
    params.set('bg', 'F8F9FC')
    hexIframe.src = ENGINE_BASE + '?' + params.toString()
    hexIframe.className = 'hexmap-embed__iframe'
    hexIframe.style.width = '100%'
    hexIframe.style.aspectRatio = '4 / 3'
    hexIframe.style.border = 'none'
    hexIframe.style.borderRadius = '8px'
    hexIframe.setAttribute('title', 'Hex Map: ' + config.game)
    hexIframe.setAttribute('scrolling', 'no')
    frameEl.appendChild(hexIframe)
  }

  // Actions
  if (actionsEl) {
    const exportBtn = document.createElement('button')
    exportBtn.className = 'chess-explorer__btn'
    exportBtn.textContent = 'Export SVG'
    exportBtn.addEventListener('click', () => sendMessage('hexmap:exportSvg'))
    actionsEl.appendChild(exportBtn)
  }

  // Listen for responses
  window.addEventListener('message', (e) => {
    if (!e.data || typeof e.data.type !== 'string') return
    if (e.data.type === 'hexmap:svgData' && e.data.svg) {
      const blob = new Blob([e.data.svg], { type: 'image/svg+xml' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = config.game + '-map.svg'
      a.click()
      URL.revokeObjectURL(url)
    }
  })
}
