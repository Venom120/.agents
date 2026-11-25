export type Override = number | 'off' | null
export type Snap = {
  tokens: number | null
  window: number
  five: number | null
  seven: number | null
  fiveResets: string | null
  sevenResets: string | null
  usd: number | null
  isSub: boolean
}
export type Handoff = { phase: 'idle' | 'running' | 'ready'; text: string }

declare module 'claude-code' {
  interface PluginState {
    'cache-keeper': {
      snap: Snap | null
      lastWarmAt: number | null
      keepWarm: boolean
      override: Override
      refusedAt: number | null
      handoff: Handoff
      tick: number
    }
  }
}
