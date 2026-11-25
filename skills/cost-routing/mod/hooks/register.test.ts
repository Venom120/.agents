import { expect, test } from 'claude-code/testing'

test('routes listed types, keeps explicit and unlisted ones', async ($, on) => {
  const seen: (string | undefined)[] = []
  on('agent.spawn', (_, e) => {
    seen.push(e.model)

    return { model: e.model ?? 'inherit' }
  })

  await $.agent.spawn({ prompt: 'find x', subagentType: 'Explore' })
  await $.agent.spawn({ prompt: 'find x', subagentType: 'Explore', model: 'opus' })
  await $.agent.spawn({ prompt: 'design x', subagentType: 'Plan' })

  expect(seen).toEqual(['haiku', 'opus', undefined])
})
