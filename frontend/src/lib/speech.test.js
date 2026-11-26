import { describe, expect, it } from 'vitest'
import { offlineEnglishVoices, toSpeech } from './speech.js'

describe('toSpeech: maths read the way a teacher would say it', () => {
  it.each([
    ['6 + 4 = ?', '6 plus 4 equals what'],
    ['4 + ? = 10', '4 plus what equals 10'],
    ['72 + 18 = ?', '72 plus 18 equals what'],
    ['52 − 17 = ?', '52 minus 17 equals what'],
    ['So 8 + 7 = 15.', 'So 8 plus 7 equals 15.'],
    ['Ones: 7 + 9 = 16.', 'Ones: 7 plus 9 equals 16.'],
  ])('%s', (text, spoken) => {
    expect(toSpeech(text)).toBe(spoken)
  })

  it('keeps the question mark at the end of a sentence for question intonation', () => {
    expect(toSpeech('Count the objects. How many are there?')).toBe(
      'Count the objects. How many are there?',
    )
    expect(toSpeech('What number comes after 39?')).toBe('What number comes after 39?')
  })

  it('leaves hyphenated names alone', () => {
    expect(toSpeech('Well done, Wa-Njeri!')).toBe('Well done, Wa-Njeri!')
  })

  it('says fractions and shillings in words', () => {
    expect(toSpeech('½ of 8')).toBe('a half of 8')
    expect(toSpeech('It costs KSh 20.')).toBe('It costs 20 shillings.')
  })

  it('drops emoji and symbols that would be read out oddly', () => {
    expect(toSpeech('💡 Make 10 first.')).toBe('Make 10 first.')
    expect(toSpeech('⚠️ Use letters only.')).toBe('Use letters only.')
  })
})

describe('offlineEnglishVoices: only voices installed on the device', () => {
  const voice = (name, lang, localService) => ({ name, lang, localService })

  it('never uses online voices, which send the text to a server', () => {
    const voices = [voice('Google US English', 'en-US', false), voice('Google UK', 'en-GB', false)]
    expect(offlineEnglishVoices(voices)).toEqual([])
  })

  it('prefers Kenyan, then British, then US English, and skips other languages', () => {
    const voices = [
      voice('US', 'en-US', true),
      voice('Swahili', 'sw-KE', true),
      voice('Kenya', 'en-KE', true),
      voice('Online Kenya', 'en-KE', false),
      voice('UK', 'en-GB', true),
    ]
    expect(offlineEnglishVoices(voices).map((v) => v.name)).toEqual(['Kenya', 'UK', 'US'])
  })
})
