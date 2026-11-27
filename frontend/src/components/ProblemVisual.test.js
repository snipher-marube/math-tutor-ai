import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import { pickThing } from '../lib/counting.js'
import ProblemVisual from './ProblemVisual.vue'

const SEED = 'problem-1'
const thing = pickThing(SEED)
const show = (type, params) => mount(ProblemVisual, { props: { visual: { type, params }, seed: SEED } })
const badges = (w) => w.findAll('.count-badge').map((b) => b.text())

describe('counting with emoji', () => {
  it('shows one emoji per thing, and names them for screen readers', () => {
    const w = show('objects', { count: 7 })
    const things = w.findAll('button.thing')
    expect(things).toHaveLength(7)
    expect(things[0].text()).toContain(thing.emoji)
    expect(w.find('figure').attributes('aria-label')).toBe(
      `7 ${thing.many}. Tap each one to count it.`,
    )
  })

  it('numbers each thing as it is tapped, and un-counts on a second tap', async () => {
    const w = show('objects', { count: 5 })
    const things = w.findAll('button.thing')
    for (const i of [0, 3, 1]) await things[i].trigger('click')
    expect(badges(w)).toEqual(['1', '3', '2']) // badges in screen order
    expect(things[3].attributes('aria-label')).toBe(`${thing.one}, number 2`)

    await things[3].trigger('click')
    expect(badges(w)).toEqual(['1', '2'])
    expect(things[3].attributes('aria-pressed')).toBe('false')
  })

  it('counts on across two groups', async () => {
    const w = show('objects', { first: 2, second: 3 })
    expect(w.findAll('.things')).toHaveLength(2)
    for (const b of w.findAll('button.thing')) await b.trigger('click')
    expect(badges(w)).toEqual(['1', '2', '3', '4', '5'])
  })
})

describe('take-away pictures', () => {
  it('crosses out the things taken away, which cannot be tapped', () => {
    const w = show('objects', { count: 7, take: 3 })
    expect(w.findAll('button.thing')).toHaveLength(4)
    expect(w.findAll('.thing.taken')).toHaveLength(3)
    expect(w.find('figure').attributes('aria-label')).toContain(`7 ${thing.many}, 3 crossed out`)
  })

  it('crosses out the last dots on ten-frames', () => {
    const w = show('ten-frame', { filled: 13, size: 10, take: 5 })
    expect(w.findAll('.frame')).toHaveLength(2)
    expect(w.findAll('.dot.first')).toHaveLength(8)
    expect(w.findAll('.dot.taken')).toHaveLength(5)
  })

  it('crosses out tens and ones taken away', () => {
    const w = show('base-ten', { tens: 5, ones: 8, take_tens: 2, take_ones: 3 })
    expect(w.findAll('.rod.taken')).toHaveLength(2)
    expect(w.findAll('.cube.taken')).toHaveLength(3)
    expect(w.find('figure').attributes('aria-label')).toBe(
      '5 tens and 8 ones. Take away 2 tens and 3 ones',
    )
  })

  it("doesn't cross out ones when there aren't enough (a ten must be broken first)", () => {
    const w = show('base-ten', { tens: 5, ones: 2, take_tens: 1, take_ones: 7 })
    expect(w.findAll('.rod.taken')).toHaveLength(1)
    expect(w.findAll('.cube.taken')).toHaveLength(0)
  })
})

describe('other pictures', () => {
  it('never shows the number in the blank box of a number line', () => {
    const w = show('number-line', { start: 5, end: 8, blank: 9 })
    const items = w.findAll('li')
    expect(items.map((li) => li.text())).toEqual(['5', '6', '7', '8', '?'])
  })

  it('uses "ten" and "one" for a single ten or one', () => {
    const w = show('base-ten', { tens: 1, ones: 1 })
    expect(w.find('figure').attributes('aria-label')).toBe('1 ten and 1 one')
  })
})
