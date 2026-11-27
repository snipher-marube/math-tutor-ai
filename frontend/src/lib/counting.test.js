import { describe, expect, it } from 'vitest'
import { THINGS, countOf, pickThing, questionText } from './counting.js'

describe('pickThing', () => {
  it('always picks the same thing for the same problem', () => {
    expect(pickThing('3f9c2a1b7d4e5f60')).toBe(pickThing('3f9c2a1b7d4e5f60'))
  })

  it('picks different things across problems', () => {
    const picked = new Set(Array.from({ length: 50 }, (_, i) => pickThing(`problem-${i}`).emoji))
    expect(picked.size).toBeGreaterThan(5)
  })

  it('works without a seed', () => {
    expect(THINGS).toContain(pickThing(undefined))
  })
})

describe('countOf', () => {
  const mango = THINGS[0]
  it('uses the right word for one and many', () => {
    expect(countOf(1, mango)).toBe('1 mango')
    expect(countOf(7, mango)).toBe('7 mangoes')
  })
})

describe('questionText', () => {
  it('names the things to count', () => {
    const problem = { id: 'abc', kind: 'count', question: 'Count the objects. How many are there?' }
    expect(questionText(problem)).toBe(`How many ${pickThing('abc').many} are there?`)
  })

  it('leaves other questions as they are', () => {
    expect(questionText({ id: 'abc', kind: 'add', question: '3 + 4 = ?' })).toBe('3 + 4 = ?')
  })
})
