import { tools } from './mg-tools-common.js'

const panelEl = document.getElementById('decks-panel')

if (panelEl) {
  tools.embed.decks(panelEl, {
    card: true,
    vars: { '--embed-bg': '#f5f4ef' },
  })
}
