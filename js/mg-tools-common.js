const TOOLS_API = location.hostname === 'localhost'
  ? 'https://moddable-tools-staging.neuroware.workers.dev'
  : 'https://tools.moddable.games'

function el(tag, attrs, ...children) {
  const e = document.createElement(tag)
  if (attrs) {
    for (const [k, v] of Object.entries(attrs)) {
      if (k === 'style' && typeof v === 'object') Object.assign(e.style, v)
      else if (k === 'html') e.innerHTML = v
      else if (k === 'textContent') e.textContent = v
      else if (k === 'className') e.className = v
      else if (k.startsWith('on')) e.addEventListener(k.slice(2).toLowerCase(), v)
      else e.setAttribute(k, v)
    }
  }
  for (const c of children) {
    if (c == null) continue
    e.appendChild(typeof c === 'string' ? document.createTextNode(c) : c)
  }
  return e
}

function btn(label, variant, onClick) {
  const b = el('button', { class: 'mg-btn mg-btn--' + variant })
  b.textContent = label
  if (onClick) b.addEventListener('click', onClick)
  return b
}

function track(event, params) {
  if (window.gtag) window.gtag('event', event, params)
}

export { TOOLS_API, el, btn, track }
