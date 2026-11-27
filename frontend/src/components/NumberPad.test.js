import { mount } from '@vue/test-utils'
import { afterEach, describe, expect, it } from 'vitest'
import NumberPad from './NumberPad.vue'

let wrapper

function pad(props = {}) {
  wrapper = mount(NumberPad, {
    props: {
      modelValue: '',
      'onUpdate:modelValue': (v) => wrapper.setProps({ modelValue: v }),
      ...props,
    },
    attachTo: document.body,
  })
  return wrapper
}

const button = (w, text) => w.findAll('button').find((b) => b.text() === text)
const typed = (w) => w.props('modelValue')

afterEach(() => wrapper?.unmount())

describe('NumberPad', () => {
  it('types digits, with no leading zero', async () => {
    const w = pad()
    await button(w, '0').trigger('click')
    await button(w, '7').trigger('click')
    expect(typed(w)).toBe('7')
    await button(w, '2').trigger('click')
    expect(typed(w)).toBe('72')
  })

  it('stops at the maximum length', async () => {
    const w = pad({ modelValue: '123' })
    await button(w, '4').trigger('click')
    expect(typed(w)).toBe('123')
  })

  it('deletes the last digit', async () => {
    const w = pad({ modelValue: '45' })
    await w.find('[aria-label="Delete"]').trigger('click')
    expect(typed(w)).toBe('4')
  })

  it('only checks when there is an answer', async () => {
    const w = pad()
    expect(button(w, 'Check').attributes('disabled')).toBeDefined()
    await w.setProps({ modelValue: '5' })
    await button(w, 'Check').trigger('click')
    expect(w.emitted('submit')).toHaveLength(1)
  })

  it('works with the keyboard: digits, Backspace and Enter', async () => {
    const w = pad()
    for (const key of ['1', '2', 'Backspace', '8']) {
      window.dispatchEvent(new KeyboardEvent('keydown', { key }))
      await w.vm.$nextTick()
    }
    expect(typed(w)).toBe('18')
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter' }))
    expect(w.emitted('submit')).toHaveLength(1)
  })

  it('does nothing while disabled', async () => {
    const w = pad({ disabled: true })
    window.dispatchEvent(new KeyboardEvent('keydown', { key: '3' }))
    await w.vm.$nextTick()
    expect(typed(w)).toBe('')
  })
})
