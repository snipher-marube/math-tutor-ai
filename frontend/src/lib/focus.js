// After a mouse or touch click, take focus off the button, so a child who then
// types an answer and presses Enter submits it instead of pressing that button
// again. Keyboard activation (event.detail === 0) keeps focus, for accessibility.
export function releaseFocusAfterPointer(event) {
  if (event?.detail > 0) event.currentTarget?.blur?.()
}
