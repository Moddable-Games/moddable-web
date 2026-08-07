import { ModdableTools } from './mg-tools-sdk.js'

const base = 'https://tools.moddable.games'

const engineBase = location.hostname === 'localhost'
  ? location.origin + '/MODDABLE/moddable-engine'
  : 'https://engine.moddable.games'

const tools = new ModdableTools({ base, engineBase })

export { tools }
