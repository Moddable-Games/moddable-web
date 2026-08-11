const sdkUrl = location.hostname === 'localhost'
  ? '/MODDABLE/moddable-tools/sdk/index.js'
  : 'https://tools.moddable.games/sdk.js'

const { ModdableTools } = await import(sdkUrl)

const base = 'https://tools.moddable.games'

const engineBase = location.hostname === 'localhost'
  ? location.origin + '/MODDABLE/moddable-engine'
  : 'https://engine.moddable.games'

const tools = new ModdableTools({ base, engineBase })

export { tools }
