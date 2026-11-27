// Friendly things to count instead of plain dots: fruit, animals and toys a
// Kenyan child knows. Each problem always shows the same thing (picked from its
// id), so the question, the hints and a page reload all match.

export const THINGS = [
  { emoji: '🥭', one: 'mango', many: 'mangoes' },
  { emoji: '🍌', one: 'banana', many: 'bananas' },
  { emoji: '🍊', one: 'orange', many: 'oranges' },
  { emoji: '🍉', one: 'watermelon', many: 'watermelons' },
  { emoji: '🥑', one: 'avocado', many: 'avocados' },
  { emoji: '🐐', one: 'goat', many: 'goats' },
  { emoji: '🐄', one: 'cow', many: 'cows' },
  { emoji: '🐔', one: 'chicken', many: 'chickens' },
  { emoji: '🐟', one: 'fish', many: 'fish' },
  { emoji: '🦋', one: 'butterfly', many: 'butterflies' },
  { emoji: '⚽', one: 'ball', many: 'balls' },
  { emoji: '⭐', one: 'star', many: 'stars' },
]

// A small, stable hash (FNV-1a) so the same seed always picks the same thing.
function hash(text) {
  let h = 0x811c9dc5
  for (const ch of String(text)) {
    h ^= ch.codePointAt(0)
    h = Math.imul(h, 0x01000193) >>> 0
  }
  return h
}

export function pickThing(seed) {
  return THINGS[hash(seed ?? '') % THINGS.length]
}

// "1 mango", "7 mangoes"
export function countOf(n, thing) {
  return `${n} ${n === 1 ? thing.one : thing.many}`
}

// The question to show and read for a problem. A counting problem names the
// things on screen ("How many mangoes are there?") instead of "the objects".
export function questionText(problem) {
  if (problem?.kind !== 'count') return problem?.question ?? ''
  return `How many ${pickThing(problem.id).many} are there?`
}
