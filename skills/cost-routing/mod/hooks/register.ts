import type { Register } from 'claude-code'

// The tuning knob: agent type -> model alias. Unlisted types keep their own model.
const ROUTES: Record<string, string> = {
  Explore: 'haiku',
  'claude-code-guide': 'haiku',
  'general-purpose': 'sonnet',
}

export const register: Register = on => {
  on('agent.spawn', ($, e, next) => {
    const model = Object.hasOwn(ROUTES, e.subagentType) ? ROUTES[e.subagentType] : undefined

    if (e.model || !model) return next(e)

    $.ui.toast(`cost-routing: ${e.subagentType} -> ${model}`)

    return next({ ...e, model })
  })
}
