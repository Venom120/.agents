import { atom, read, update } from 'claude-code'
import type { EngineInterface, PluginOptions, Register } from 'claude-code'

import type { Snap } from '../types'
import { autoPoint, effectivePoint, fmt, level, money, parseAmount, rewarmCost, stepPoint } from './logic'

type Dollar = EngineInterface
const PANE = 'cache-keeper'

const snapA = atom({ plugin: 'cache-keeper', key: 'snap' } as const, null)
const lastWarmA = atom({ plugin: 'cache-keeper', key: 'lastWarmAt' } as const, null)
const keepA = atom({ plugin: 'cache-keeper', key: 'keepWarm' } as const, false)
const overA = atom({ plugin: 'cache-keeper', key: 'override' } as const, null)
const refusedA = atom({ plugin: 'cache-keeper', key: 'refusedAt' } as const, null)
const handoffA = atom({ plugin: 'cache-keeper', key: 'handoff' } as const, { phase: 'idle', text: '' })
const tickA = atom({ plugin: 'cache-keeper', key: 'tick' } as const, 0)

const HANDOFF_PROMPT =
  'Write a handoff so this work can continue in a fresh session. Make your final message ONLY a self-contained summary: goal, what is done, current state and files touched, decisions and caveats, and exact next steps. Do not call tools.'

let options: PluginOptions = {}
const num = (key: string, fallback: number) => {
  const v = Number(options[key])
  return Number.isFinite(v) ? v : fallback
}
const ttlMs = (isSub: boolean) => (num('cacheTtlMinutes', 0) > 0 ? num('cacheTtlMinutes', 0) : isSub ? 60 : 5) * 60_000
const is1h = (isSub: boolean) => ttlMs(isSub) >= 30 * 60_000

let working = false
let warnedFor = 0
let isPinging = false
let awaitHandoff = false

async function refresh($: Dollar): Promise<Snap> {
  const u = await $.session.usage()
  const win = (kind: string) => u.rateLimits.find(r => r.kind === kind)
  const five = win('five_hour')
  const seven = win('seven_day')
  const snap: Snap = {
    tokens: u.context.tokens ?? null,
    window: u.context.window,
    five: five ? Math.max(0, 100 - five.percentUsed) : null,
    seven: seven ? Math.max(0, 100 - seven.percentUsed) : null,
    fiveResets: five?.resetsAt ?? null,
    sevenResets: seven?.resetsAt ?? null,
    usd: u.cost?.usd ?? null,
    isSub: u.rateLimits.length > 0,
  }
  await update($, snapA, () => snap)
  return snap
}

async function tick($: Dollar) {
  const now = await $.clock.now()
  if (working) await update($, lastWarmA, () => now)
  const snap = await refresh($)
  const last = await read($, lastWarmA)
  if (last !== null) {
    const ttl = ttlMs(snap.isSub)
    const left = last + ttl - now
    const warn = Math.min(num('warnMinutes', 5) * 60_000, ttl / 2)
    if (left > 0 && left <= warn && warnedFor !== last) {
      warnedFor = last
      $.ui.toast(`Prompt cache goes cold in ${Math.ceil(left / 60_000)} min`, { timeoutMs: 8000 })
    }
    if (left > 0 && left <= 60_000 && !working && !isPinging && (await read($, keepA))) {
      isPinging = true
      try {
        // A fork reads the cached prefix, which renews its TTL without a visible turn.
        const r = await $.model.fork({ prompt: 'Reply with just "ok".' })
        if ('isAnswered' in r && r.isAnswered) {
          const at = await $.clock.now()
          await update($, lastWarmA, () => at)
        }
      } finally {
        isPinging = false
      }
    }
  }
  await update($, tickA, n => n + 1)
}

async function refuse($: Dollar, tokens: number) {
  await update($, refusedA, () => tokens + 50_000)
  $.ui.toast(`Compaction refused; I'll retry after ${fmt(tokens + 50_000)} of context`)
}

async function compact($: Dollar, tokens: number): Promise<'done' | 'refused' | 'busy'> {
  try {
    const r = await $.session.compact()
    if (r.skip) {
      await refuse($, tokens)
      return 'refused'
    }
    await update($, refusedA, () => null)
    const at = await $.clock.now()
    await update($, lastWarmA, () => at)
    return 'done'
  } catch (err) {
    if (/turn|running|busy/i.test(String(err))) return 'busy'
    await refuse($, tokens)
    return 'refused'
  }
}

// Only called after a finished answer; retries a few times while the turn winds down.
async function autoCompact($: Dollar, attempt = 0): Promise<void> {
  const snap = await refresh($)
  const point = effectivePoint(snap.window, await read($, overA), num('autoCompactTokens', 0))
  if (point === null || snap.tokens === null || snap.tokens < point) return
  const refused = await read($, refusedA)
  if (refused !== null && snap.tokens < refused) return
  const result = await compact($, snap.tokens)
  if (result === 'busy' && attempt < 4) $.clock.after(2000, () => void autoCompact($, attempt + 1).catch(() => {}))
  if (result === 'done') $.ui.toast('Auto-compacted the conversation')
}

async function startHandoff($: Dollar) {
  if (working) return $.ui.toast('Wait for the current answer to finish, then press 🤝')
  const commands = await $.command.list()
  const skill = commands.find(c => /^(.+:)?handoff(:save)?$/.test(c.name))
  awaitHandoff = true
  await update($, handoffA, () => ({ phase: 'running', text: '' }))
  try {
    await $.prompt.submit({ text: skill ? `/${skill.name}` : HANDOFF_PROMPT })
  } catch (err) {
    awaitHandoff = false
    await update($, handoffA, () => ({ phase: 'idle', text: '' }))
    $.ui.toast(`Handoff failed: ${String(err)}`)
  }
}

async function clearAndContinue($: Dollar) {
  const { text } = await read($, handoffA)
  if (!text) return $.ui.toast('The handoff is empty; run 🤝 again')
  await $.command.run({ command: 'clear' })
  await $.prompt.submit({ text: `Continuing from a handoff of the previous conversation:\n\n${text}` })
  await update($, handoffA, () => ({ phase: 'idle', text: '' }))
}

async function setOverride($: Dollar, pick: (current: number, window: number, ov: 'off' | number | null) => 'off' | number | null) {
  const snap = await read($, snapA)
  if (!snap) return
  const ov = await read($, overA)
  const current = effectivePoint(snap.window, ov, num('autoCompactTokens', 0)) ?? autoPoint(snap.window)
  await update($, overA, () => pick(current, snap.window, ov))
  await update($, refusedA, () => null)
}


export const register: Register = (on, opts) => {
  options = opts

  on('session.start', async ($, e, next) => {
    await $.command.register({
      name: 'cache-keeper',
      description: 'Cache keeper: autocompact <250k|off|auto> sets this session\'s auto-compact point',
      argumentHint: 'autocompact <250k|off|auto>',
    })
    void tick($).catch(() => {})
    $.clock.every(15_000, () => void tick($).catch(() => {}))

    return next(e)
  })

  on('command.run', { command: 'cache-keeper' }, async ($, e) => {
    const [sub, value = ''] = e.args.trim().split(/\s+/)
    const parsed = sub === 'autocompact' ? parseAmount(value) : undefined
    if (parsed === undefined) return { text: 'Usage: /cache-keeper autocompact <250k|off|auto>' }
    await update($, overA, () => parsed)
    await update($, refusedA, () => null)
    const snap = await read($, snapA)
    const point = effectivePoint(snap?.window ?? 200_000, parsed, num('autoCompactTokens', 0))

    return { text: point === null ? 'Auto-compact is off for this session.' : `Auto-compact at ${fmt(point)} tokens for this session.` }
  })

  on('turn.start', async ($, e, next) => {
    working = true
    const at = await $.clock.now()
    await update($, lastWarmA, () => at)

    return next(e)
  })

  on('turn.complete', async ($, e, next) => {
    if (e.agentId !== undefined) return next(e)
    working = false
    const at = await $.clock.now()
    await update($, lastWarmA, () => at)
    if (awaitHandoff) {
      awaitHandoff = false
      const last = (await $.session.messages()).filter(m => m.role === 'assistant').at(-1)
      await update($, handoffA, () => ({ phase: last?.text ? 'ready' : 'idle', text: last?.text ?? '' }))
    }
    $.clock.after(1500, () => void autoCompact($).catch(() => {}))

    return next(e)
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    const snap = await read($, snapA)
    await read($, tickA)
    if (e.props.hasSurvey || snap === null) return next(e)
    // Other mods' bands (e.g. Source Control) sit in the same row instead of being replaced.
    const rest = await next(e)

    const now = await $.clock.now()
    const last = await read($, lastWarmA)
    const keep = await read($, keepA)
    const handoff = await read($, handoffA)
    const ov = await read($, overA)
    const { Box, Button, Text } = $.ui.resolve(e)

    const ttl = ttlMs(snap.isSub)
    const left = last === null ? null : last + ttl - now
    const isCold = left !== null && left <= 0
    const price = num('inputPricePerMTok', 5)
    const rewarm = snap.tokens === null ? null : rewarmCost(snap.tokens, price, is1h(snap.isSub))
    const warn = Math.min(num('warnMinutes', 5) * 60_000, ttl / 2)

    const pill = (key: string, dot: string, text: string) => (
      <Box key={key} borderStyle="round" borderColor="inactive" paddingX={1}>
        <Text color={dot}>● </Text>
        <Text dimColor>{text}</Text>
      </Box>
    )

    const cacheText =
      left === null ? 'cache –' : isCold ? 'cache cold' : `cache ${left < 60_000 ? '<1m' : `${Math.ceil(left / 60_000)}m`} left`
    const cacheDot = left === null ? 'inactive' : isCold ? 'error' : left <= warn ? 'warning' : 'success'

    const point = effectivePoint(snap.window, ov, num('autoCompactTokens', 0))
    const ctxText =
      snap.tokens === null
        ? 'context –'
        : `context ${fmt(snap.tokens)} / ${point === null ? `${fmt(snap.window)} (auto-compact off)` : fmt(point)}`
    const ctxDot = snap.tokens === null ? 'inactive' : level(snap.tokens / (point ?? snap.window))

    const limitParts = [
      snap.five !== null ? `5h ${Math.round(snap.five)}% left` : null,
      snap.seven !== null ? `week ${Math.round(snap.seven)}% left` : null,
    ].filter(Boolean)
    const minLeft = Math.min(snap.five ?? 100, snap.seven ?? 100)
    const limitDot = limitParts.length === 0 ? 'inactive' : minLeft > 30 ? 'success' : minLeft > 10 ? 'warning' : 'error'

    return (
      <Box flexDirection="row" flexWrap="wrap" gap={1} alignItems="center">
        {pill('cache', cacheDot, rewarm === null ? cacheText : `${cacheText} · re-warm ${money(rewarm)}`)}
        {pill('ctx', ctxDot, ctxText)}
        {pill('limits', limitDot, limitParts.length ? limitParts.join(' · ') : 'limits n/a')}
        {left !== null && !isCold && (
          <Button key="warm" plain label="🔥" variant={keep ? 'primary' : undefined} onPress={() => update($, keepA, v => !v)} />
        )}
        <Button
          key="compact"
          plain
          label="📦"
          onPress={async () => {
            const s = await refresh($)
            const r = await compact($, s.tokens ?? 0)
            if (r === 'done') $.ui.toast('Compacted the conversation')
            if (r === 'busy') $.ui.toast('Wait for the current answer to finish, then compact')
          }}
        />
        {handoff.phase === 'running' ? (
          <Text dimColor>🤝 writing…</Text>
        ) : (
          <Button key="handoff" plain label="🤝" onPress={() => startHandoff($)} />
        )}
        {handoff.phase === 'ready' && (
          <Button key="clear" label="Clear & continue" variant="primary" onPress={() => clearAndContinue($)} />
        )}
        <Button key="details" plain label="📊" onPress={() => $.ui.open({ id: PANE, title: 'Cache keeper' })} />
        {rest}
      </Box>
    )
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const snap = await read($, snapA)
    await read($, tickA)
    const { Box, Button, Text } = $.ui.resolve(e)
    if (snap === null) return <Text dimColor>Waiting for the first reading…</Text>

    const now = await $.clock.now()
    const last = await read($, lastWarmA)
    const keep = await read($, keepA)
    const ov = await read($, overA)
    const ttl = ttlMs(snap.isSub)
    const left = last === null ? null : last + ttl - now
    const price = num('inputPricePerMTok', 5)
    const point = effectivePoint(snap.window, ov, num('autoCompactTokens', 0))
    const source = ov !== null ? 'session override' : num('autoCompactTokens', 0) > 0 ? 'setting' : 'automatic'
    const minutes = (ms: number) => `${Math.floor(ms / 60_000)}m ${Math.floor((ms % 60_000) / 1000)}s`
    const reset = (iso: string | null) => (iso ? ` (resets ${new Date(iso).toLocaleString()})` : '')

    return (
      <Box flexDirection="column" gap={1}>
        <Box flexDirection="column">
          <Text weight="bold">Prompt cache</Text>
          <Text>{left === null ? 'No request yet.' : left <= 0 ? 'Cold.' : `Warm for ${minutes(left)} of ${Math.round(ttl / 60_000)} min.`}</Text>
          <Text dimColor>
            Re-warm cost: {snap.tokens === null ? 'unknown' : money(rewarmCost(snap.tokens, price, is1h(snap.isSub)))} (at ${price}/M input,{' '}
            {is1h(snap.isSub) ? '2x' : '1.25x'} write). Keep-warm is {keep ? 'on' : 'off'}.
          </Text>
        </Box>
        <Box flexDirection="column">
          <Text weight="bold">Context</Text>
          <Text>
            {snap.tokens === null ? 'No reading yet' : `${snap.tokens.toLocaleString()} tokens`} of {snap.window.toLocaleString()}
            {snap.tokens === null ? '' : ` (${Math.round((snap.tokens / snap.window) * 100)}%)`}
          </Text>
          <Text dimColor>
            Auto-compact: {point === null ? 'off' : `at ${point.toLocaleString()} tokens`} ({source})
          </Text>
        </Box>
        <Box flexDirection="column">
          <Text weight="bold">Limits left</Text>
          <Text>5-hour: {snap.five === null ? 'n/a' : `${snap.five.toFixed(1)}%${reset(snap.fiveResets)}`}</Text>
          <Text>Weekly: {snap.seven === null ? 'n/a' : `${snap.seven.toFixed(1)}%${reset(snap.sevenResets)}`}</Text>
        </Box>
        <Box flexDirection="column">
          <Text weight="bold">Session cost (API prices)</Text>
          <Text>{snap.usd === null ? 'n/a' : `$${snap.usd.toFixed(2)}`}</Text>
        </Box>
        <Box flexDirection="row" gap={1} flexWrap="wrap">
          <Button key="minus" label="−50k" onPress={() => setOverride($, (cur, win) => stepPoint(cur, win, -1))} />
          <Button key="plus" label="+50k" onPress={() => setOverride($, (cur, win) => stepPoint(cur, win, 1))} />
          <Button key="toggle" label={point === null ? 'Turn on' : 'Turn off'} onPress={() => setOverride($, (_c, _w, o) => (o === 'off' ? null : 'off'))} />
          <Button key="reset" label="Reset" onPress={() => setOverride($, () => null)} />
        </Box>
      </Box>
    )
  })
}
