import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import App from './App.vue'
import { needsPlacement } from './lib/placement.js'

vi.mock('./lib/placement.js', () => ({ needsPlacement: vi.fn() }))

const AMANI = { id: 1, nickname: 'Amani', avatar: 'zebra' }
// The screens are tested on their own; here we only check which one shows.
const stubs = {
  LearnerPicker: { template: '<div class="picker" />', emits: ['chosen', 'check-level'] },
  PlacementView: { template: '<div class="placement" />', emits: ['done', 'change-learner'] },
  LessonView: { template: '<div class="lesson" />', emits: ['change-learner'] },
}
const app = () => mount(App, { global: { stubs } })
const screen = (w) => ['picker', 'placement', 'lesson'].find((s) => w.find(`.${s}`).exists())

beforeEach(() => vi.resetAllMocks())

describe('App screens', () => {
  it('sends a new learner to the placement check, then the lesson', async () => {
    needsPlacement.mockResolvedValue(true)
    const w = app()
    w.findComponent(stubs.LearnerPicker).vm.$emit('chosen', AMANI)
    await flushPromises()
    expect(screen(w)).toBe('placement')
    w.findComponent(stubs.PlacementView).vm.$emit('done')
    await flushPromises()
    expect(screen(w)).toBe('lesson')
  })

  it('sends a returning learner straight to the lesson', async () => {
    needsPlacement.mockResolvedValue(false)
    const w = app()
    w.findComponent(stubs.LearnerPicker).vm.$emit('chosen', AMANI)
    await flushPromises()
    expect(screen(w)).toBe('lesson')
    w.findComponent(stubs.LessonView).vm.$emit('change-learner')
    await flushPromises()
    expect(screen(w)).toBe('picker')
  })

  it('lets a teacher re-run the check from the learner screen', async () => {
    const w = app()
    w.findComponent(stubs.LearnerPicker).vm.$emit('check-level', AMANI)
    await flushPromises()
    expect(screen(w)).toBe('placement')
    expect(needsPlacement).not.toHaveBeenCalled()
  })

  it('stays on the learner screen and shows the error if the backend is unreachable', async () => {
    needsPlacement.mockRejectedValue(new Error("Can't reach the tutor."))
    const w = app()
    w.findComponent(stubs.LearnerPicker).vm.$emit('chosen', AMANI)
    await flushPromises()
    expect(screen(w)).toBe('picker')
    expect(w.find('[role="alert"]').text()).toBe("Can't reach the tutor.")
  })
})
