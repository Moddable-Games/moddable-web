import { tools } from './mg-tools-common.js'

const panelEl = document.getElementById('oracle-panel')

if (panelEl) {
  tools.embed.oracles(panelEl, {
    card: true,
    vars: { '--embed-bg': '#f5f4ef' },
  })
}
