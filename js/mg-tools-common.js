import { ModdableTools } from './mg-tools-sdk.js'

const base = location.hostname === 'localhost'
  ? 'https://moddable-tools-staging.neuroware.workers.dev'
  : 'https://tools.moddable.games'

const engineBase = location.hostname === 'localhost'
  ? location.origin + '/MODDABLE/moddable-engine'
  : 'https://engine.moddable.games'

const tools = new ModdableTools({ base, engineBase })

export { tools }
