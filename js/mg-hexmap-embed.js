import { tools } from './mg-tools-common.js'

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

  const params = { game: config.game, style: currentStyle, random: '1', bg: 'FFFFFF' }
  if (currentSize) params.size = String(currentSize)
  if (currentLayout) params.players = String(parseInt(currentLayout))

  const embed = tools.embed.play(frameEl, {
    params,
    title: 'Hex Map: ' + config.game,
    height: 500,
  })

  if (controlsEl) {
    const controls = document.createElement('div')
    controls.className = 'hexmap-embed__control-row'

    if (config.styles.length > 1) {
      const styleSelect = document.createElement('select')
      styleSelect.className = 'hexmap-embed__select'
      config.styles.forEach(s => {
        const opt = document.createElement('option')
        opt.value = s
        opt.textContent = s.charAt(0).toUpperCase() + s.slice(1)
        if (s === currentStyle) opt.selected = true
        styleSelect.appendChild(opt)
      })
      styleSelect.addEventListener('change', () => {
        currentStyle = styleSelect.value
        embed.send('hexmap:setStyle', { style: currentStyle })
      })
      controls.appendChild(styleSelect)
    }

    if (config.sizes) {
      const sizeSelect = document.createElement('select')
      sizeSelect.className = 'hexmap-embed__select'
      config.sizes.forEach(s => {
        const opt = document.createElement('option')
        opt.value = s
        opt.textContent = 'Size ' + s
        if (s === currentSize) opt.selected = true
        sizeSelect.appendChild(opt)
      })
      sizeSelect.addEventListener('change', () => {
        currentSize = parseInt(sizeSelect.value)
        embed.send('hexmap:regenerate', { size: currentSize, random: true })
      })
      controls.appendChild(sizeSelect)
    }

    if (config.layouts) {
      const layoutSelect = document.createElement('select')
      layoutSelect.className = 'hexmap-embed__select'
      config.layouts.forEach(l => {
        const opt = document.createElement('option')
        opt.value = l
        opt.textContent = l.toUpperCase()
        if (l === currentLayout) opt.selected = true
        layoutSelect.appendChild(opt)
      })
      layoutSelect.addEventListener('change', () => {
        currentLayout = layoutSelect.value
        embed.send('hexmap:regenerate', { players: parseInt(currentLayout), random: true })
      })
      controls.appendChild(layoutSelect)
    }

    const regenBtn = document.createElement('button')
    regenBtn.className = 'hexmap-embed__btn'
    regenBtn.textContent = 'Regenerate'
    regenBtn.addEventListener('click', () => embed.send('hexmap:regenerate', { random: true }))
    controls.appendChild(regenBtn)

    controlsEl.appendChild(controls)
  }

  if (actionsEl) {
    const exportBtn = document.createElement('button')
    exportBtn.className = 'hexmap-embed__btn'
    exportBtn.textContent = 'Export SVG'
    exportBtn.addEventListener('click', () => embed.send('hexmap:exportSvg', {}))
    actionsEl.appendChild(exportBtn)
  }

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
