<script setup>
// One problem at a time: answer with the number pad, get kind feedback,
// ask for hints, and move on. The answer is checked by the backend.
import { computed, onMounted, ref } from 'vue'
import { AVATARS, api } from '../lib/api.js'
import HintPanel from './HintPanel.vue'
import NumberPad from './NumberPad.vue'
import ProblemVisual from './ProblemVisual.vue'

const props = defineProps({
  learner: { type: Object, required: true },
})
const emit = defineEmits(['change-learner'])

const skill = ref(null) // { skill_id, name, grade, status, reason }
const problem = ref(null) // { id, kind, question, operands }
const answer = ref('')
const result = ref(null) // last answer result from the backend
const feedback = ref('') // what the live region announces
const hintStart = ref(null) // set when hints are open
const newSkill = ref('')
const allDone = ref(false)
const error = ref('')
const busy = ref(false)

const solved = computed(() => result.value?.correct === true)

// Counting problems need the objects on screen; the child counts them.
const problemVisual = computed(() =>
  problem.value?.kind === 'count'
    ? { type: 'objects', params: { count: problem.value.operands[0] } }
    : null,
)

async function nextProblem() {
  busy.value = true
  error.value = ''
  try {
    const previous = skill.value?.skill_id
    const next = await api.nextSkill(props.learner.id)
    if (!next.skill_id) {
      allDone.value = true
      feedback.value = next.reason
      return
    }
    newSkill.value = previous && previous !== next.skill_id ? next.name : ''
    skill.value = next
    problem.value = await api.newProblem(next.skill_id, props.learner.id)
    answer.value = ''
    result.value = null
    hintStart.value = null
    feedback.value = newSkill.value ? `New skill: ${newSkill.value}!` : ''
  } catch (e) {
    error.value = e.message
  } finally {
    busy.value = false
  }
}

async function check() {
  busy.value = true
  error.value = ''
  try {
    const given = Number(answer.value)
    result.value = await api.answer(problem.value.id, given)
    feedback.value = result.value.feedback
    if (!result.value.correct) answer.value = ''
  } catch (e) {
    error.value = e.message
  } finally {
    busy.value = false
  }
}

function showHints() {
  hintStart.value = result.value?.next_hint ?? 'nudge'
}

onMounted(nextProblem)
</script>

<template>
  <section class="lesson">
    <header class="top">
      <span class="who">
        <span aria-hidden="true">{{ AVATARS[learner.avatar] ?? '🙂' }}</span>
        {{ learner.nickname }}
      </span>
      <button type="button" @click="emit('change-learner')">Change learner</button>
    </header>

    <!-- One polite live region for feedback, so screen readers announce it. -->
    <p class="visually-hidden" aria-live="polite">{{ feedback }}</p>

    <p v-if="error" role="alert" class="error">
      {{ error }}
      <button type="button" @click="nextProblem">Try again</button>
    </p>

    <div v-if="allDone" class="done pop">
      <p class="big">🎉</p>
      <h1>{{ feedback }}</h1>
    </div>

    <template v-else-if="problem">
      <p class="skill">
        <span v-if="newSkill" class="new-skill pop">New skill!</span>
        {{ skill.name }}
      </p>

      <h1 class="question" :aria-label="`Question: ${problem.question.replace('?', 'what')}`">
        {{ problem.question }}
      </h1>

      <ProblemVisual v-if="problemVisual" :visual="problemVisual" />

      <output class="answer" :class="{ empty: !answer && !solved, solved }" aria-label="Your answer">
        {{ answer || '?' }}<span v-if="solved" aria-label="correct"> ✓</span>
      </output>

      <div
        v-if="result"
        class="feedback pop"
        :class="result.correct ? 'good' : 'try'"
        aria-hidden="true"
      >
        {{ result.feedback }}
      </div>

      <template v-if="solved">
        <button type="button" class="primary next" :disabled="busy" @click="nextProblem">
          Next problem →
        </button>
      </template>

      <template v-else>
        <NumberPad v-model="answer" :disabled="busy" @submit="check" />
        <button v-if="!hintStart" type="button" class="hint-button" @click="showHints">
          💡 I need a hint
        </button>
        <HintPanel v-else :problem-id="problem.id" :start="hintStart" />
      </template>
    </template>
  </section>
</template>

<style scoped>
.lesson {
  display: grid;
  gap: 1rem;
}

.top {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  gap: 0.6rem;
}

.who {
  font-weight: 700;
  font-size: 1.1rem;
}

.who span {
  font-size: 1.6rem;
}

.skill {
  margin: 0;
  text-align: center;
  color: var(--muted);
  font-weight: 600;
}

.new-skill {
  display: inline-block;
  margin-inline-end: 0.4rem;
  padding: 0.1rem 0.6rem;
  border-radius: 999px;
  background: var(--brand);
  color: var(--brand-text);
}

.question {
  margin: 0;
  text-align: center;
  font-size: clamp(2.2rem, 9vw, 3.6rem);
}

.answer {
  justify-self: center;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.3em;
  min-inline-size: 7rem;
  min-block-size: 4.5rem;
  padding: 0 1rem;
  border: 3px solid var(--brand);
  border-radius: 16px;
  background: var(--surface);
  font-size: 2.6rem;
  font-weight: 800;
}

.answer.solved {
  border-style: solid;
  background: var(--good-soft);
  color: var(--good);
}

.answer.empty {
  color: var(--muted);
  border-style: dashed;
}

.feedback {
  padding: 0.8rem 1rem;
  border-radius: 16px;
  text-align: center;
  font-weight: 700;
  font-size: 1.15rem;
}

.feedback.good {
  background: var(--good-soft);
  color: var(--good);
}

.feedback.try {
  background: var(--try-soft);
  color: var(--try);
}

.next,
.hint-button {
  justify-self: center;
  min-inline-size: 14rem;
}

.next {
  font-size: 1.3rem;
}

.done {
  text-align: center;
}

.big {
  font-size: 4rem;
  margin: 0;
}

.error {
  color: var(--try);
  font-weight: 600;
}
</style>
