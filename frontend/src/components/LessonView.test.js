import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { api } from '../lib/api.js'
import LessonView from './LessonView.vue'

vi.mock('../lib/api.js', async (importOriginal) => ({
  ...(await importOriginal()),
  api: { nextSkill: vi.fn(), newProblem: vi.fn(), answer: vi.fn(), hints: vi.fn() },
}))

const LEARNER = { id: 1, nickname: 'Amani', avatar: 'zebra' }
const skill = (id, name, extra = {}) => ({ skill_id: id, name, grade: 1, status: 'practising', review: false, reason: '', ...extra })
const problem = (id, question, kind = 'add', operands = [3, 4]) => ({ id, skill_id: 'x', kind, question, operands })

async function lesson() {
  const w = mount(LessonView, { props: { learner: LEARNER }, attachTo: document.body })
  await flushPromises()
  return w
}

const pressDigits = async (w, digits) => {
  for (const d of digits) await w.findAll('.pad button').find((b) => b.text() === d).trigger('click')
}
const button = (w, text) => w.findAll('button').find((b) => b.text().includes(text))

beforeEach(() => {
  vi.resetAllMocks()
  api.nextSkill.mockResolvedValue(skill('add-within-10', 'Add within 10'))
  api.newProblem.mockResolvedValue(problem('p1', '3 + 4 = ?'))
  api.hints.mockResolvedValue([{ step: 'nudge', text: 'Start at 4. Count on 3 more.', visual: null, example: null }])
})

describe('LessonView', () => {
  it('shows the skill and the question', async () => {
    const w = await lesson()
    expect(w.find('.skill').text()).toContain('Add within 10')
    expect(w.find('h1.question').text()).toBe('3 + 4 = ?')
    expect(api.newProblem).toHaveBeenCalledWith('add-within-10', 1)
  })

  it('praises a right answer and offers the next problem', async () => {
    api.answer.mockResolvedValue({ correct: true, feedback: 'Well done! You worked it out.', next_hint: null, attempts: 1 })
    const w = await lesson()
    await pressDigits(w, '7')
    await button(w, 'Check').trigger('click')
    await flushPromises()

    expect(api.answer).toHaveBeenCalledWith('p1', 7)
    expect(w.find('.feedback.good').text()).toBe('Well done! You worked it out.')
    expect(w.find('output').text()).toContain('✓')
    expect(button(w, 'Next problem')).toBeTruthy()
    expect(w.find('.pad').exists()).toBe(false)
  })

  it('after a wrong answer, clears it and opens hints from the suggested step', async () => {
    api.answer.mockResolvedValue({ correct: false, feedback: 'Not quite yet.', next_hint: 'picture', attempts: 1 })
    const w = await lesson()
    await pressDigits(w, '9')
    await button(w, 'Check').trigger('click')
    await flushPromises()

    expect(w.find('.feedback.try').text()).toBe('Not quite yet.')
    expect(w.find('output').text()).toBe('?')
    await button(w, 'I need a hint').trigger('click')
    await flushPromises()
    expect(api.hints).toHaveBeenCalledWith('p1', 'picture')
    expect(w.text()).toContain('Start at 4. Count on 3 more.')
  })

  it('names the things in a counting question', async () => {
    api.newProblem.mockResolvedValue(problem('p2', 'Count the objects. How many are there?', 'count', [6]))
    const w = await lesson()
    expect(w.find('h1.question').text()).toMatch(/^How many .+ are there\?$/)
    expect(w.findAll('button.thing')).toHaveLength(6)
  })

  it('shows "Quick review" for a review, and no "New skill!" when coming back', async () => {
    api.nextSkill
      .mockResolvedValueOnce(skill('add-within-10', 'Add within 10'))
      .mockResolvedValueOnce(skill('count-to-20', 'Count objects to 20', { review: true, status: 'mastered' }))
      .mockResolvedValueOnce(skill('add-within-10', 'Add within 10'))
      .mockResolvedValueOnce(skill('make-10', 'Make 10'))
    api.answer.mockResolvedValue({ correct: true, feedback: 'Well done!', next_hint: null, attempts: 1 })
    const w = await lesson()

    const solveAndNext = async () => {
      await pressDigits(w, '7')
      await button(w, 'Check').trigger('click')
      await flushPromises()
      await button(w, 'Next problem').trigger('click')
      await flushPromises()
    }

    await solveAndNext()
    expect(w.find('.review-badge').exists()).toBe(true)
    await solveAndNext()
    expect(w.find('.review-badge').exists()).toBe(false)
    expect(w.find('.new-skill').exists()).toBe(false) // back to the same skill
    await solveAndNext()
    expect(w.find('.new-skill').text()).toBe('New skill!')
  })

  it('celebrates when every skill is mastered', async () => {
    api.nextSkill.mockResolvedValue({ skill_id: null, name: null, grade: null, status: null, review: false, reason: 'Every skill is mastered. Well done!' })
    const w = await lesson()
    expect(w.find('.done').text()).toContain('Every skill is mastered')
  })

  it('shows an error with a way to try again', async () => {
    api.nextSkill.mockRejectedValueOnce(new Error("Can't reach the tutor."))
    const w = await lesson()
    expect(w.find('[role="alert"]').text()).toContain("Can't reach the tutor.")
    await button(w, 'Try again').trigger('click')
    await flushPromises()
    expect(w.find('h1.question').text()).toBe('3 + 4 = ?')
  })
})
