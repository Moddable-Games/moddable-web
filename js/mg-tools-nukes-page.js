import { tools } from './mg-tools-common.js'

const embedEl = document.getElementById('nukes-tools')

if (embedEl) {
  tools.embed.nukes(embedEl, {
    card: true,
    vars: { '--embed-bg': '#f5f4ef' },
  })
}

const hexBtns = document.getElementById('hex-engine-btns')
if (hexBtns) {
  const engineUrl = location.hostname === 'localhost'
    ? '/MODDABLE/moddable-engine/'
    : 'https://engine.moddable.games/'

  const playBtn = document.createElement('a')
  playBtn.href = engineUrl
  playBtn.className = 'chess-engine-band__btn chess-engine-band__btn--primary'
  playBtn.textContent = 'Moddable Engine'
  playBtn.setAttribute('target', '_blank')
  playBtn.setAttribute('rel', 'noopener')
  hexBtns.appendChild(playBtn)

  const srcBtn = document.createElement('a')
  srcBtn.href = 'https://github.com/Moddable-Games/moddable-engine'
  srcBtn.className = 'chess-engine-band__btn chess-engine-band__btn--outline'
  srcBtn.textContent = 'View Source'
  srcBtn.setAttribute('target', '_blank')
  srcBtn.setAttribute('rel', 'noopener')
  hexBtns.appendChild(srcBtn)
}
