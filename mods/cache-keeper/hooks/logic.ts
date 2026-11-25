import type { Override } from '../types'

export const MIN_POINT = 100_000
const STEP = 50_000

export const autoPoint = (window: number) =>
  window >= 1_000_000 ? 300_000 : Math.max(MIN_POINT, Math.floor(window * 0.7))

// null = auto-compact off. Per-session override > setting > automatic rule.
export function effectivePoint(window: number, override: Override, setting: number): number | null {
  if (override === 'off') return null
  const n = typeof override === 'number' ? override : setting > 0 ? setting : autoPoint(window)
  return Math.max(MIN_POINT, n)
}

export const stepPoint = (current: number, window: number, dir: 1 | -1) =>
  Math.min(Math.max(MIN_POINT, current + dir * STEP), Math.max(MIN_POINT, window))

// undefined = invalid, null = auto, 'off', or a token count. A bare number under 10000 means thousands.
export function parseAmount(raw: string): Override | undefined {
  const s = raw.trim().toLowerCase()
  if (s === 'off') return 'off'
  if (s === 'auto') return null
  const m = /^(\d+(?:\.\d+)?)([km])?$/.exec(s)
  if (!m) return undefined
  let n = Number(m[1])
  if (m[2] === 'm') n *= 1e6
  else if (m[2] === 'k' || n < 10_000) n *= 1e3
  return Math.round(n)
}

// Cache write price: 1.25x input for the 5-minute cache, 2x for the 1-hour one.
export const rewarmCost = (tokens: number, pricePerMTok: number, is1h: boolean) =>
  (tokens / 1e6) * pricePerMTok * (is1h ? 2 : 1.25)

export const fmt = (n: number) =>
  n >= 1e6 ? `${(n / 1e6).toFixed(1)}M` : `${Math.round(n / 1000)}k`

export const money = (n: number) => `$${n < 10 ? n.toFixed(2) : n.toFixed(0)}`

export const level = (ratio: number): 'success' | 'warning' | 'error' =>
  ratio < 0.7 ? 'success' : ratio < 0.9 ? 'warning' : 'error'
