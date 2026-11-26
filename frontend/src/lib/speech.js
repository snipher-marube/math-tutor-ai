// Read-aloud for children who are still learning to read.
//
// Uses the browser's built-in speech (Web Speech API) with English voices that
// are installed on the device only. Online voices (like Chrome's "Google" voices)
// are never used, because they send the text to a server. If there is no
// on-device English voice, the read-aloud buttons are hidden.

import { ref } from 'vue'

const STORAGE_KEY = 'math-tutor:read-aloud'
const RATE = 0.9 // a little slower than normal, for young listeners

// Turn maths text into words a child should hear: "6 + ? = 10" -> "6 plus what equals 10".
export function toSpeech(text) {
  return text
    .replace(/(\d)\s*\+\s*(?=[\d?])/g, '$1 plus ')
    .replace(/(\d)\s*[−-]\s*(?=[\d?])/g, '$1 minus ')
    .replace(/\s*=\s*/g, ' equals ')
    .replace(/(^|\s)\?(?=\s|$|[.,])/g, '$1what')
    .replace(/½/g, 'a half')
    .replace(/¼/g, 'a quarter')
    .replace(/KSh\s?(\d+)/g, '$1 shillings')
    .replace(/[💡🎉✓⚠️]/gu, '')
    .replace(/\s+/g, ' ')
    .trim()
}

export const speechSupported =
  typeof window !== 'undefined' &&
  'speechSynthesis' in window &&
  typeof window.SpeechSynthesisUtterance === 'function'

// On-device English voices, best first: Kenyan English, then British, then US, then any.
export function offlineEnglishVoices(voices) {
  const rank = (v) => ({ 'en-KE': 0, 'en-GB': 1, 'en-US': 2 })[v.lang] ?? 3
  return voices
    .filter((v) => v.localService && v.lang?.toLowerCase().startsWith('en'))
    .sort((a, b) => rank(a) - rank(b))
}

// True once the device has an on-device English voice. Voices can load late, so
// listen for "voiceschanged". Some devices (e.g. Linux without speech packages) have none.
export const speechAvailable = ref(false)

if (speechSupported) {
  const update = () => {
    speechAvailable.value = offlineEnglishVoices(window.speechSynthesis.getVoices()).length > 0
  }
  update()
  window.speechSynthesis.addEventListener?.('voiceschanged', update)
}

function loadEnabled() {
  try {
    return localStorage.getItem(STORAGE_KEY) !== 'off'
  } catch {
    return true // storage can be blocked; default to reading aloud
  }
}

// On by default: the youngest learners need it most.
export const readAloud = ref(loadEnabled())

export function setReadAloud(on) {
  readAloud.value = on
  try {
    localStorage.setItem(STORAGE_KEY, on ? 'on' : 'off')
  } catch {
    // Not saved, but still works for this visit.
  }
  if (!on) stop()
}


// Say `text` now, replacing anything already being said.
// `force` speaks even when read-aloud is off (for the repeat button).
export function speak(text, { force = false } = {}) {
  if (!speechAvailable.value || !text || (!readAloud.value && !force)) return
  const synth = window.speechSynthesis
  synth.cancel()
  const voice = offlineEnglishVoices(synth.getVoices())[0]
  if (!voice) return
  const utterance = new window.SpeechSynthesisUtterance(toSpeech(text))
  utterance.voice = voice
  utterance.lang = voice.lang
  utterance.rate = RATE
  synth.speak(utterance)
}

export function stop() {
  if (speechSupported) window.speechSynthesis.cancel()
}
