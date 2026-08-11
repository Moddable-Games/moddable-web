import { tools } from './mg-tools-common.js'

const rulesBody = document.getElementById('rules-body')
if (rulesBody) {
  tools.embed._create('rules', rulesBody, {
    height: 500,
    card: true,
    vars: { '--embed-bg': '#f5f4ef', '--embed-card-border': 'none', '--embed-card-radius': '0', '--embed-card-padding': '24px 0 0' },
  })
}

const gamenightBody = document.getElementById('gamenight-body')
if (gamenightBody) {
  tools.embed._create('gamenight', gamenightBody, {
    height: 600,
    card: true,
    vars: { '--embed-bg': '#f5f4ef' },
  })
}
