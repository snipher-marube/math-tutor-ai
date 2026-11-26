import { describe, expect, it, vi } from 'vitest'
import { releaseFocusAfterPointer } from './focus.js'

describe('releaseFocusAfterPointer', () => {
  it('blurs the button after a mouse or touch click', () => {
    const blur = vi.fn()
    releaseFocusAfterPointer({ detail: 1, currentTarget: { blur } })
    expect(blur).toHaveBeenCalledOnce()
  })

  it('keeps focus after keyboard activation, for keyboard users', () => {
    const blur = vi.fn()
    releaseFocusAfterPointer({ detail: 0, currentTarget: { blur } })
    expect(blur).not.toHaveBeenCalled()
  })
})
