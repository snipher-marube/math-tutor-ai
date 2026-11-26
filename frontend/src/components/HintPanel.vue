<script setup>
// Shows the hint ladder one step at a time: nudge, picture, worked example.
import { ref, watch } from 'vue'
import { api } from '../lib/api.js'
import ProblemVisual from './ProblemVisual.vue'

const props = defineProps({
  problemId: { type: String, required: true },
  start: { type: String, default: 'nudge' },
})

const hints = ref([])
const shown = ref(0)
const error = ref('')

async function load() {
  error.value = ''
  try {
    hints.value = await api.hints(props.problemId, props.start)
    shown.value = 1
  } catch (e) {
    error.value = e.message
  }
}

watch(() => [props.problemId, props.start], load, { immediate: true })
</script>

<template>
  <section class="hints" aria-label="Hints">
    <p v-if="error" role="alert">{{ error }}</p>
    <article v-for="hint in hints.slice(0, shown)" :key="hint.step" class="hint pop">
      <p class="hint-text">💡 {{ hint.text }}</p>
      <ProblemVisual v-if="hint.visual" :visual="hint.visual" />
      <div v-if="hint.example" class="example">
        <p class="example-question">{{ hint.example.question }}</p>
        <ProblemVisual
          v-if="hint.example.kind === 'count'"
          :visual="{ type: 'objects', params: { count: hint.example.operands[0] } }"
        />
        <ol>
          <li v-for="(step, i) in hint.example.steps" :key="i">{{ step }}</li>
        </ol>
      </div>
    </article>
    <button v-if="shown < hints.length" type="button" @click="shown++">Show me more help</button>
  </section>
</template>

<style scoped>
.hints {
  display: grid;
  gap: 0.8rem;
}

.hint {
  display: grid;
  gap: 0.6rem;
  padding: 0.8rem 1rem;
  border-radius: 16px;
  background: var(--try-soft);
}

.hint-text {
  margin: 0;
  font-weight: 600;
}

.example {
  background: var(--surface);
  border-radius: 12px;
  padding: 0.6rem 1rem;
}

.example-question {
  margin: 0;
  font-size: 1.4rem;
  font-weight: 700;
}

.example ol {
  margin: 0.4rem 0 0;
  padding-inline-start: 1.4rem;
}
</style>
