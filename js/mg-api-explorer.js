import { tools } from './mg-tools-common.js'

const el = document.getElementById('api-explorer')

if (el) {
  tools.embed.explorer(el, {
    theme: 'dark',
  })
}
