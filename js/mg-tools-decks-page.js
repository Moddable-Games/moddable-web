import { tools } from './mg-tools-common.js'

const panelEl = document.getElementById('decks-panel')

if (panelEl) {
  const defaultTab = window.location.hash.slice(1) || undefined

  tools.embed.decks(panelEl, {
    tab: defaultTab,
    card: true,
    vars: { '--embed-bg': '#f5f4ef' },
    onTab: (tab) => {
      window.location.hash = tab
    },
  })
}
