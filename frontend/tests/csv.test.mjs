import test from 'node:test'
import assert from 'node:assert/strict'
import { applicationsToCsv } from '../src/utils/csv.js'

const HEADER_COLUMNS = 14
const app = (over = {}) => ({ company: 'Kaspi', position: 'Backend Intern', status: 'Saved', ...over })

// Minimal RFC 4180 parser so the tests check what Excel would actually see.
function parse(csv) {
  const rows = []
  let row = [], cur = '', quoted = false
  for (let i = 0; i < csv.length; i++) {
    const c = csv[i]
    if (quoted) {
      if (c === '"' && csv[i + 1] === '"') { cur += '"'; i++ }
      else if (c === '"') quoted = false
      else cur += c
    } else if (c === '"') quoted = true
    else if (c === ',') { row.push(cur); cur = '' }
    else if (c === '\r' && csv[i + 1] === '\n') { row.push(cur); rows.push(row); row = []; cur = ''; i++ }
    else cur += c
  }
  row.push(cur); rows.push(row)
  return rows
}

test('no applications: header row only', () => {
  const rows = parse(applicationsToCsv([]))
  assert.equal(rows.length, 1)
  assert.equal(rows[0].length, HEADER_COLUMNS)
  assert.equal(rows[0][0], 'Company')
})

test('header plus one row per application', () => {
  const rows = parse(applicationsToCsv(Array.from({ length: 20 }, (_, i) => app({ company: `C${i}` }))))
  assert.equal(rows.length, 21)
  assert.ok(rows.every((r) => r.length === HEADER_COLUMNS))
})

test('commas, quotes and line breaks stay inside their cell', () => {
  const rows = parse(applicationsToCsv([app({ company: 'Kaspi, Inc.', notes: 'say "hi"\nsecond line' })]))
  assert.equal(rows.length, 2)
  assert.equal(rows[1][0], 'Kaspi, Inc.')
  assert.equal(rows[1][12], 'say "hi"\nsecond line')
  assert.equal(rows[1].length, HEADER_COLUMNS)
})

test('Kazakh and Russian text is kept exactly', () => {
  const rows = parse(applicationsToCsv([app({ company: 'Қазақтелеком', position: 'Стажёр-аналитик' })]))
  assert.deepEqual(rows[1].slice(0, 2), ['Қазақтелеком', 'Стажёр-аналитик'])
})

test('null and undefined fields become empty cells', () => {
  const rows = parse(applicationsToCsv([app({ location: null, notes: undefined })]))
  assert.equal(rows[1][3], '')
  assert.equal(rows[1][12], '')
})

test('cells that start like spreadsheet formulas are neutralised', () => {
  for (const evil of ['=HYPERLINK("http://evil")', '+1+1', '-2+3', '@SUM(A1)']) {
    const rows = parse(applicationsToCsv([app({ notes: evil })]))
    assert.ok(rows[1][12].startsWith("'"), `not neutralised: ${evil}`)
  }
})

test('rows are separated by CRLF', () => {
  assert.ok(applicationsToCsv([app()]).includes('\r\n'))
})
