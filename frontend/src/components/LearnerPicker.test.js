import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError, api } from '../lib/api.js'
import LearnerPicker from './LearnerPicker.vue'

vi.mock('../lib/api.js', async (importOriginal) => ({
  ...(await importOriginal()),
  api: { listLearners: vi.fn(), createLearner: vi.fn() },
}))

const AMANI = { id: 1, nickname: 'Amani', avatar: 'zebra', created_at: '' }

async function picker(learners = [AMANI]) {
  api.listLearners.mockResolvedValue(learners)
  const w = mount(LearnerPicker)
  await flushPromises()
  return w
}

beforeEach(() => vi.resetAllMocks())
afterEach(() => vi.restoreAllMocks())

// happy-dom checks `pattern` without Unicode support, so the nickname pattern
// ([\p{L}]...) never matches there. Real browsers do support it, so for the form
// tests the browser's own check is treated as passing. The backend checks too.
function browserAcceptsNickname() {
  vi.spyOn(HTMLFormElement.prototype, 'checkValidity').mockReturnValue(true)
}

describe('LearnerPicker', () => {
  it('lists learners and picks one', async () => {
    const w = await picker()
    await w.find('button.learner').trigger('click')
    expect(w.emitted('chosen')[0]).toEqual([AMANI])
  })

  it('opens the new learner form straight away on a new device', async () => {
    const w = await picker([])
    expect(w.find('form.new').exists()).toBe(true)
    expect(w.find('details.grown-ups').exists()).toBe(false)
  })

  it('keeps "Check level" in a closed section for teachers and parents', async () => {
    const w = await picker()
    const section = w.find('details.grown-ups')
    expect(section.attributes('open')).toBeUndefined()
    expect(section.find('summary').text()).toBe('For teachers and parents')
    const check = section.find('button')
    expect(check.text()).toContain('Check level for Amani')
    await check.trigger('click')
    expect(w.emitted('check-level')[0]).toEqual([AMANI])
  })

  it('creates a learner card with a nickname and an animal', async () => {
    const created = { id: 2, nickname: 'Baraka', avatar: 'lion', created_at: '' }
    api.createLearner.mockResolvedValue(created)
    browserAcceptsNickname()
    const w = await picker([])
    await w.find('#nickname').setValue('  Baraka ')
    await w.find('form.new').trigger('submit')
    await flushPromises()
    expect(api.createLearner).toHaveBeenCalledWith('Baraka', 'lion')
    expect(w.emitted('chosen')[0]).toEqual([created])
  })

  it('asks for letters only when the browser rejects the nickname', async () => {
    vi.spyOn(HTMLFormElement.prototype, 'checkValidity').mockReturnValue(false)
    const w = await picker([])
    await w.find('#nickname').setValue('0712345678')
    await w.find('form.new').trigger('submit')
    expect(w.find('#nickname-error').text()).toContain('Use letters only')
    expect(api.createLearner).not.toHaveBeenCalled()
  })

  it('says kindly when a nickname is taken', async () => {
    api.createLearner.mockRejectedValue(new ApiError(409, 'taken'))
    browserAcceptsNickname()
    const w = await picker([])
    await w.find('#nickname').setValue('Amani')
    await w.find('form.new').trigger('submit')
    await flushPromises()
    expect(w.find('#nickname-error').text()).toContain('That nickname is already used')
    expect(w.find('#nickname').attributes('aria-invalid')).toBe('true')
  })
})
