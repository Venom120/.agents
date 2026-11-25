import { expect, test } from 'claude-code/testing'

import { autoPoint, effectivePoint, parseAmount, rewarmCost, stepPoint } from './logic'

test('auto-compact point: 300k on 1M, 70% elsewhere, never below 100k', () => {
  expect(autoPoint(1_000_000)).toBe(300_000)
  expect(autoPoint(200_000)).toBe(140_000)
  expect(autoPoint(100_000)).toBe(100_000)
})

test('override beats setting beats automatic; off disables', () => {
  expect(effectivePoint(200_000, null, 0)).toBe(140_000)
  expect(effectivePoint(200_000, null, 120_000)).toBe(120_000)
  expect(effectivePoint(200_000, 250_000, 120_000)).toBe(250_000)
  expect(effectivePoint(200_000, 50_000, 0)).toBe(100_000)
  expect(effectivePoint(200_000, 'off', 0)).toBe(null)
})

test('command argument parsing and stepping', () => {
  expect(parseAmount('250k')).toBe(250_000)
  expect(parseAmount('250')).toBe(250_000)
  expect(parseAmount('off')).toBe('off')
  expect(parseAmount('auto')).toBe(null)
  expect(parseAmount('banana')).toBe(undefined)
  expect(stepPoint(120_000, 200_000, -1)).toBe(100_000)
  expect(stepPoint(190_000, 200_000, 1)).toBe(200_000)
})

test('re-warm cost: 1.25x for the 5-minute cache, 2x for 1 hour', () => {
  expect(rewarmCost(1_000_000, 5, false)).toBe(6.25)
  expect(rewarmCost(1_000_000, 5, true)).toBe(10)
})
