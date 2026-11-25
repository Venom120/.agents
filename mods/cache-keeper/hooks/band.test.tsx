import { expect, test } from 'claude-code/testing'

const BAND = {
  plugin: 'cache-keeper',
  component: 'AbovePrompt',
  props: { hasSurvey: false, isWorking: false, maxRows: 10, bodyColumns: 100, scroll: { offset: 0, bodyRows: 10 }, view: {} },
} as const

const snap = { tokens: 120_000, window: 1_000_000, five: 80, seven: 50, fiveResets: null, sevenResets: null, usd: 1.5, isSub: true }

test("another mod's band stays in the same row as the pills", async ($, on) => {
  on('clock.now', () => ({ value: 1_000_000 }))
  on('state.get', (_, e) => ({ value: e.key === 'snap' ? { value: snap, version: 1 } : { version: 0 } }))
  // The engine's bottom stands for a second mod's band (e.g. Source Control).
  on('ui.render', ($, e) => {
    const { Text } = $.ui.resolve(e)

    return <Text>Source Control</Text>
  })

  for (const surface of ['terminal', 'desktop'] as const) {
    const ui = await $.ui.mount({ ...BAND, surface })
    expect(await ui.find({ type: 'Text', text: /Source Control/ })).toBeTruthy()
    expect(await ui.find({ type: 'Text', text: /context 120k/ })).toBeTruthy()
    await ui.unmount()
  }
})
