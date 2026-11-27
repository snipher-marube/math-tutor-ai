import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { api } from '../lib/api.js'
import PlacementView from './PlacementView.vue'

vi.mock('../lib/api.js', async (importOriginal) => ({
  ...(await importOriginal()),
  api: { startPlacement: vi.fn(), answerPlacement: vi.fn() },
}))

const LEARNER = { id: 3, nickname: 'Zawadi', avatar: 'hippo' }
const step = (n, message = '') => ({
  placement_id: 9,
  finished: false,
  message,
  problem: { id: `p${n}`, skill_id: 'make-10', kind: 'missing-addend', question: `${n} + ? = 10`, operands: [n, 10] },
  problem_number: n,
  max_problems: 10,
  result: null,
})
const done = (known) => ({
  placement_id: 9,
  finished: true,
  message: 'All done.',
  problem: null,
  problem_number: null,
  max_problems: 10,
  result: {
    placement_id: 9,
    finished_at: '2026-11-27T08:00:00+00:00',
    stop_reason: 'all-decided',
    known_skills: known,
    next_skill: { skill_id: 'add-within-20', name: 'Add within 20', grade: 1, status: 'not-started', review: false, reason: '' },
  },
})

const button = (w, text) => w.findAll('button').find((b) => b.text().includes(text))
const answer = async (w, digit) => {
  await w.findAll('.pad button').find((b) => b.text() === digit).trigger('click')
  await button(w, 'Check').trigger('click')
  await flushPromises()
}

beforeEach(() => vi.resetAllMocks())

describe('PlacementView', () => {
  it('starts with a friendly intro, and can be skipped', async () => {
    const w = mount(PlacementView, { props: { learner: LEARNER } })
    expect(w.find('h1').text()).toBe('Hi Zawadi!')
    await button(w, 'Skip for now').trigger('click')
    expect(w.emitted('done')).toHaveLength(1)
    expect(api.startPlacement).not.toHaveBeenCalled()
  })

  it('asks questions without saying right or wrong, then shows where to start', async () => {
    api.startPlacement.mockResolvedValue(step(1))
    api.answerPlacement
      .mockResolvedValueOnce(step(2, 'Thank you! Here is the next one.'))
      .mockResolvedValueOnce(done(['count-to-20', 'add-within-10', 'make-10']))
    const w = mount(PlacementView, { props: { learner: LEARNER } })

    await button(w, "Let's start").trigger('click')
    await flushPromises()
    expect(api.startPlacement).toHaveBeenCalledWith(3)
    expect(w.find('h1.question').text()).toBe('1 + ? = 10')
    expect(w.find('.count').text()).toContain('Question 1')
    expect(w.findAll('.dot')).toHaveLength(10)

    await answer(w, '9')
    expect(api.answerPlacement).toHaveBeenCalledWith(9, 'p1', 9)
    expect(w.find('.thanks').text()).toBe('Thank you! Here is the next one.')
    expect(w.find('.feedback').exists()).toBe(false) // never marked right or wrong
    expect(w.findAll('.dot.on')).toHaveLength(2)

    await answer(w, '8')
    expect(w.find('.done h1').text()).toBe('All done, Zawadi!')
    expect(w.find('.done').text()).toContain('You already know 3 skills. Well done!')
    expect(w.find('.done').text()).toContain('You will start with: Add within 20.')
    await button(w, 'Start learning').trigger('click')
    expect(w.emitted('done')).toHaveLength(1)
  })

  it('is encouraging when no skills are known yet', async () => {
    api.startPlacement.mockResolvedValue(done([]))
    const w = mount(PlacementView, { props: { learner: LEARNER } })
    await button(w, "Let's start").trigger('click')
    await flushPromises()
    expect(w.find('.done').text()).toContain("Now let's learn together!")
  })

  it('keeps the answer when sending fails, so "Try again" resends it', async () => {
    api.startPlacement.mockResolvedValue(step(1))
    api.answerPlacement.mockRejectedValueOnce(new Error("Can't reach the tutor.")).mockResolvedValueOnce(step(2))
    const w = mount(PlacementView, { props: { learner: LEARNER } })
    await button(w, "Let's start").trigger('click')
    await flushPromises()

    await answer(w, '9')
    expect(w.find('[role="alert"]').text()).toContain("Can't reach the tutor.")
    await button(w, 'Try again').trigger('click')
    await flushPromises()
    expect(api.answerPlacement).toHaveBeenLastCalledWith(9, 'p1', 9)
    expect(w.find('h1.question').text()).toBe('2 + ? = 10')
  })
})
