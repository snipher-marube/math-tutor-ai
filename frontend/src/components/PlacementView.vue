<script setup>
// The placement check: a few questions to find where a learner should start.
// The child isn't told whether each answer was right, and there are no hints:
// it's for finding the right level, not for marking. The backend chooses each
// question and decides when to stop (see backend/services/placement.py).
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { AVATARS, api } from '../lib/api.js'
import { questionText } from '../lib/counting.js'
import { releaseFocusAfterPointer } from '../lib/focus.js'
import { readAloud, setReadAloud, speak, speechAvailable, stop, toSpeech } from '../lib/speech.js'
import NumberPad from './NumberPad.vue'
import ProblemVisual from './ProblemVisual.vue'

const props = defineProps({
  learner: { type: Object, required: true },
})
const emit = defineEmits(['done', 'change-learner'])

const INTRO = "Let's see what you already know. Some questions are easy and some are hard. Just try your best!"

const stage = ref('intro') // 'intro' | 'questions' | 'done'
const step = ref(null) // the latest response from the backend
const answer = ref('')
const announce = ref('') // what the live region announces
const error = ref('')
const busy = ref(false)

const problem = computed(() => step.value?.problem ?? null)
const result = computed(() => step.value?.result ?? null)

// Counting problems need the objects on screen; the child counts them.
const question = computed(() => questionText(problem.value))

const problemVisual = computed(() =>
  problem.value?.kind === 'count'
    ? { type: 'objects', params: { count: problem.value.operands[0] } }
    : null,
)

const knownCount = computed(() => result.value?.known_skills.length ?? 0)

const doneMessage = computed(() => {
  const next = result.value?.next_skill
  const start = next?.name ? ` You will start with: ${next.name}.` : ''
  const known =
    knownCount.value > 0
      ? `You already know ${knownCount.value} ${knownCount.value === 1 ? 'skill' : 'skills'}. Well done!`
      : "Now let's learn together!"
  return `${known}${start}`
})

async function run(request) {
  busy.value = true
  error.value = ''
  try {
    const next = await request()
    step.value = next
    answer.value = ''
    if (next.finished) {
      stage.value = 'done'
      announce.value = `All done! ${doneMessage.value}`
      speak(announce.value)
    } else {
      stage.value = 'questions'
      announce.value = next.message
      speak(next.message ? `${next.message} ${question.value}` : question.value)
    }
  } catch (e) {
    error.value = e.message
  } finally {
    busy.value = false
  }
}

function start() {
  run(() => api.startPlacement(props.learner.id))
}

function check() {
  const { placement_id: placementId } = step.value
  run(() => api.answerPlacement(placementId, problem.value.id, Number(answer.value)))
}

function retry() {
  // If answering failed, the same question is still waiting; otherwise start again.
  if (stage.value === 'questions' && answer.value !== '') check()
  else start()
}

function sayQuestion() {
  speak(question.value, { force: true })
}

onMounted(() => speak(`Hi ${props.learner.nickname}! ${INTRO}`))
onBeforeUnmount(stop)
</script>

<template>
  <section class="placement">
    <header class="top">
      <span class="who">
        <span aria-hidden="true">{{ AVATARS[learner.avatar] ?? '🙂' }}</span>
        {{ learner.nickname }}
      </span>
      <span class="controls">
        <button
          v-if="speechAvailable"
          type="button"
          :aria-pressed="readAloud ? 'true' : 'false'"
          @click="setReadAloud(!readAloud), releaseFocusAfterPointer($event)"
        >
          <span aria-hidden="true">{{ readAloud ? '🔊' : '🔇' }}</span> Read aloud
        </button>
        <button type="button" @click="emit('change-learner')">Change learner</button>
      </span>
    </header>

    <p class="visually-hidden" aria-live="polite">{{ announce }}</p>

    <p v-if="error" role="alert" class="error">
      {{ error }}
      <button type="button" :disabled="busy" @click="retry">Try again</button>
    </p>

    <div v-if="stage === 'intro'" class="intro pop">
      <p class="big" aria-hidden="true">👋</p>
      <h1>Hi {{ learner.nickname }}!</h1>
      <p class="lead">{{ INTRO }}</p>
      <button type="button" class="primary wide" :disabled="busy" @click="start">
        Let's start →
      </button>
      <button type="button" class="link" @click="emit('done')">
        Skip for now (start from the beginning)
      </button>
    </div>

    <template v-else-if="stage === 'questions' && problem">
      <p class="count">
        Question {{ step.problem_number }}
        <span class="dots" aria-hidden="true">
          <span
            v-for="n in step.max_problems"
            :key="n"
            class="dot"
            :class="{ on: n <= step.problem_number }"
          />
        </span>
      </p>

      <p v-if="step.message" class="thanks pop" aria-hidden="true">{{ step.message }}</p>

      <div class="question-row">
        <h1 class="question" :aria-label="`Question: ${toSpeech(question)}`">
          {{ question }}
        </h1>
        <button
          v-if="speechAvailable"
          type="button"
          class="say"
          aria-label="Read the question aloud"
          @click="sayQuestion(), releaseFocusAfterPointer($event)"
        >
          🔊
        </button>
      </div>

      <ProblemVisual
        v-if="problemVisual"
        :key="problem.id"
        :visual="problemVisual"
        :seed="problem.id"
      />

      <output class="answer" :class="{ empty: !answer }" aria-label="Your answer">
        {{ answer || '?' }}
      </output>

      <NumberPad v-model="answer" :disabled="busy" @submit="check" />
    </template>

    <div v-else-if="stage === 'done' && result" class="done pop">
      <p class="big" aria-hidden="true">🎉</p>
      <h1>All done, {{ learner.nickname }}!</h1>
      <p class="lead">{{ doneMessage }}</p>
      <button type="button" class="primary wide" @click="emit('done')">Start learning →</button>
    </div>
  </section>
</template>

<style scoped>
.placement {
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

.controls {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.controls button[aria-pressed='true'] {
  border-color: var(--brand);
  background: var(--brand-soft);
}

.who {
  font-weight: 700;
  font-size: 1.1rem;
}

.who span {
  font-size: 1.6rem;
}

.intro,
.done {
  display: grid;
  justify-items: center;
  gap: 0.8rem;
  text-align: center;
}

.intro h1,
.done h1 {
  margin: 0;
}

.big {
  font-size: 4rem;
  margin: 0;
}

.lead {
  margin: 0;
  max-inline-size: 30rem;
  font-size: 1.2rem;
}

.wide {
  min-inline-size: 14rem;
  font-size: 1.3rem;
}

.link {
  border: none;
  background: none;
  color: var(--muted);
  text-decoration: underline;
  font-size: 0.95rem;
}

.count {
  margin: 0;
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  align-items: center;
  gap: 0.6rem;
  color: var(--muted);
  font-weight: 600;
}

.dots {
  display: inline-flex;
  gap: 0.3rem;
}

.dot {
  inline-size: 0.7rem;
  block-size: 0.7rem;
  border-radius: 50%;
  background: var(--brand-soft);
  border: 2px solid var(--brand);
}

.dot.on {
  background: var(--brand);
}

.thanks {
  margin: 0;
  text-align: center;
  font-weight: 700;
  color: var(--brand);
}

.question-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 0.6rem;
}

.question {
  margin: 0;
  text-align: center;
  font-size: clamp(2.2rem, 9vw, 3.6rem);
}

.say {
  font-size: 1.6rem;
  border-radius: 50%;
  padding: 0;
  inline-size: 3.4rem;
  block-size: 3.4rem;
}

.answer {
  justify-self: center;
  display: flex;
  align-items: center;
  justify-content: center;
  min-inline-size: 7rem;
  min-block-size: 4.5rem;
  padding: 0 1rem;
  border: 3px solid var(--brand);
  border-radius: 16px;
  background: var(--surface);
  font-size: 2.6rem;
  font-weight: 800;
}

.answer.empty {
  color: var(--muted);
  border-style: dashed;
}

.error {
  color: var(--try);
  font-weight: 600;
}
</style>
