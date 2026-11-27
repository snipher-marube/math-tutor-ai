import { describe, expect, it, vi } from 'vitest'
import { ApiError } from './api.js'
import { needsPlacement } from './placement.js'

function fakeApi({ placement, progress = [] }) {
  return {
    latestPlacement: vi.fn(async () => {
      if (placement instanceof Error) throw placement
      return placement
    }),
    progress: vi.fn(async () => progress),
  }
}

const notFound = new ApiError(404, 'No finished placement check for this learner yet.')

describe('needsPlacement', () => {
  it('sends a brand-new learner to the placement check', async () => {
    expect(await needsPlacement(fakeApi({ placement: notFound }), 1)).toBe(true)
  })

  it('skips the check once the learner has been placed', async () => {
    const api = fakeApi({ placement: { known_skills: [] } })
    expect(await needsPlacement(api, 1)).toBe(false)
    expect(api.progress).not.toHaveBeenCalled()
  })

  it('skips the check for a learner who has already practised', async () => {
    const api = fakeApi({ placement: notFound, progress: [{ skill_id: 'count-to-20' }] })
    expect(await needsPlacement(api, 1)).toBe(false)
  })

  it('passes other errors on, so the app can show them', async () => {
    const api = fakeApi({ placement: new ApiError(0, "Can't reach the tutor.") })
    await expect(needsPlacement(api, 1)).rejects.toThrow("Can't reach the tutor.")
  })
})
