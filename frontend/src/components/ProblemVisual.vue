<script setup>
// Draws a visual from the backend: { type, params }.
// Types and params are described in backend/services/hints.py (Visual).
import { computed } from 'vue'

const props = defineProps({
  visual: { type: Object, required: true },
})

const p = computed(() => props.visual.params)

const range = (n) => Array.from({ length: Math.max(0, n) }, (_, i) => i)

// Ten-frames: cells filled with the first group, then the second group ("extra").
const frames = computed(() => {
  const size = p.value.size ?? 10
  const filled = p.value.filled ?? 0
  const extra = p.value.extra ?? 0
  const total = Math.max(size, filled + extra)
  const count = Math.ceil(total / 10)
  return range(count).map((f) =>
    range(10).map((c) => {
      const i = f * 10 + c
      if (i < filled) return 'first'
      if (i < filled + extra) return 'second'
      return i < size || f > 0 ? 'empty' : 'off'
    }),
  )
})

// Number line: labels from start to end, plus one empty box the child fills in.
// The blank box never shows its number.
const numberLine = computed(() => {
  const { start, end, blank } = p.value
  const from = Math.min(start, blank)
  const to = Math.max(end, blank)
  return range(to - from + 1).map((i) => {
    const n = from + i
    return { n, blank: n === blank }
  })
})

// Base-ten blocks: one number (tens, ones) or two (a_*, b_*).
const groups = computed(() => {
  const v = p.value
  if ('a_tens' in v) {
    return [
      { tens: v.a_tens, ones: v.a_ones },
      { tens: v.b_tens, ones: v.b_ones },
    ]
  }
  return [{ tens: v.tens, ones: v.ones }]
})

const label = computed(() => {
  const v = p.value
  switch (props.visual.type) {
    case 'objects':
      return 'count' in v
        ? `${v.count} counters`
        : `${v.first} counters and ${v.second} more counters`
    case 'ten-frame':
      return `A ten-frame with ${v.filled} dots${v.extra ? ` and ${v.extra} more dots` : ''}`
    case 'number-line':
      return `A number line from ${numberLine.value[0].n} to ${numberLine.value.at(-1).n} with one empty box`
    case 'base-ten':
      return groups.value.map((g) => `${g.tens} tens and ${g.ones} ones`).join(', plus ')
    default:
      return 'A picture'
  }
})
</script>

<template>
  <figure class="visual" role="img" :aria-label="label">
    <!-- Counters -->
    <div v-if="visual.type === 'objects'" class="objects">
      <template v-if="'count' in p">
        <span v-for="i in range(p.count)" :key="i" class="dot first" />
      </template>
      <template v-else>
        <span class="group">
          <span v-for="i in range(p.first)" :key="i" class="dot first" />
        </span>
        <span class="plus" aria-hidden="true">+</span>
        <span class="group">
          <span v-for="i in range(p.second)" :key="i" class="dot second" />
        </span>
      </template>
    </div>

    <!-- Ten-frames -->
    <div v-else-if="visual.type === 'ten-frame'" class="frames">
      <div v-for="(cells, f) in frames" :key="f" class="frame">
        <span v-for="(cell, c) in cells" :key="c" class="cell" :class="cell">
          <span v-if="cell === 'first' || cell === 'second'" class="dot" :class="cell" />
        </span>
      </div>
    </div>

    <!-- Number line -->
    <ol v-else-if="visual.type === 'number-line'" class="number-line">
      <li v-for="item in numberLine" :key="item.n" :class="{ blank: item.blank }">
        <span v-if="!item.blank">{{ item.n }}</span>
        <span v-else class="question" aria-hidden="true">?</span>
      </li>
    </ol>

    <!-- Base-ten blocks -->
    <div v-else-if="visual.type === 'base-ten'" class="base-ten">
      <template v-for="(g, gi) in groups" :key="gi">
        <span v-if="gi > 0" class="plus" aria-hidden="true">+</span>
        <span class="group">
          <span v-for="i in range(g.tens)" :key="`t${i}`" class="rod" />
          <span class="cubes">
            <span v-for="i in range(g.ones)" :key="`o${i}`" class="cube" />
          </span>
        </span>
      </template>
    </div>
  </figure>
</template>

<style scoped>
.visual {
  margin: 0;
  padding: 1rem;
  border-radius: 16px;
  background: var(--surface);
  border: 2px solid var(--border);
  display: flex;
  justify-content: center;
  overflow-x: auto;
}

.objects,
.base-ten {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 0.6rem;
  max-inline-size: 30rem;
}

.group {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 0.4rem;
  max-inline-size: 14rem;
}

.plus {
  font-size: 2rem;
  font-weight: 700;
  color: var(--muted);
}

.dot {
  display: inline-block;
  inline-size: 1.6rem;
  block-size: 1.6rem;
  border-radius: 50%;
}

.dot.first {
  background: var(--brand);
}

.dot.second {
  background: var(--accent);
}

.frames {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  justify-content: center;
}

.frame {
  display: grid;
  grid-template-columns: repeat(5, 2.4rem);
  grid-auto-rows: 2.4rem;
  border: 3px solid var(--text);
  border-radius: 6px;
}

.cell {
  display: grid;
  place-items: center;
  border: 1px solid var(--border);
}

.cell.off {
  visibility: hidden;
}

.number-line {
  display: flex;
  list-style: none;
  margin: 0;
  padding: 0 0 0.6rem;
  border-block-end: 4px solid var(--text);
}

.number-line li {
  display: grid;
  place-items: center;
  min-inline-size: 3rem;
  font-size: 1.3rem;
  font-weight: 700;
}

.number-line li.blank {
  border: 3px dashed var(--brand);
  border-radius: 10px;
  min-block-size: 3rem;
}

.question {
  color: var(--brand);
}

.rod {
  display: inline-block;
  inline-size: 0.9rem;
  block-size: 9rem;
  background: repeating-linear-gradient(
    to bottom,
    var(--brand) 0 calc(0.9rem - 2px),
    var(--surface) calc(0.9rem - 2px) 0.9rem
  );
  border-radius: 3px;
}

.cubes {
  display: grid;
  grid-template-columns: repeat(2, 0.9rem);
  gap: 2px;
  align-content: end;
}

.cube {
  inline-size: 0.9rem;
  block-size: 0.9rem;
  background: var(--accent);
  border-radius: 2px;
}
</style>
