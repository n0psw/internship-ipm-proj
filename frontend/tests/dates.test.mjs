import test from 'node:test'
import assert from 'node:assert/strict'

// Fixed zone (UTC+5, no DST) so results do not depend on the machine running the tests.
process.env.TZ = 'Asia/Almaty'
const { parseDay, todayISO, isPastDay, formatDay, formatDateTime, toLocalInput, fromLocalInput } = await import(
  '../src/utils/dates.js'
)

const shift = (days) => {
  const d = new Date()
  d.setDate(d.getDate() + days)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

test('parseDay gives local midnight, not UTC midnight', () => {
  const d = parseDay('2026-10-22')
  assert.deepEqual([d.getFullYear(), d.getMonth(), d.getDate(), d.getHours()], [2026, 9, 22, 0])
})

test('parseDay of empty value is null', () => {
  assert.equal(parseDay(null), null)
  assert.equal(parseDay(''), null)
  assert.equal(parseDay(undefined), null)
})

test('todayISO matches the local calendar date', () => {
  assert.equal(todayISO(), shift(0))
})

test('only dates before today are past: yesterday yes, today no, tomorrow no', () => {
  assert.equal(isPastDay(shift(-1)), true)
  assert.equal(isPastDay(shift(0)), false)
  assert.equal(isPastDay(shift(1)), false)
  assert.equal(isPastDay(null), false)
})

test('formatDay never shows "Invalid Date"', () => {
  assert.equal(formatDay(null), '')
  assert.equal(formatDay('2026-10-22'), '22 Oct')
  assert.equal(formatDay('2026-10-22', true), '22 Oct 2026')
})

test('interview timestamp is shown in the viewer local time (UTC+5)', () => {
  assert.equal(formatDateTime('2026-10-22T10:00:00Z'), '22 Oct, 15:00')
  assert.equal(formatDateTime(null), '')
})

test('datetime-local input round-trips through UTC', () => {
  assert.equal(toLocalInput('2026-10-22T10:00:00Z'), '2026-10-22T15:00')
  assert.equal(fromLocalInput('2026-10-22T15:00'), '2026-10-22T10:00:00.000Z')
  assert.equal(toLocalInput(null), '')
  assert.equal(fromLocalInput(''), null)
})
