<script setup>
// Choose who is learning, or add a new learner (nickname + animal picture).
// Nicknames only, never real names. See docs/CHILD_SAFETY.md.
import { computed, onMounted, ref } from 'vue'
import { AVATARS, api } from '../lib/api.js'

const emit = defineEmits(['chosen', 'check-level'])

const learners = ref([])
const loadError = ref('')
const adding = ref(false)
const nickname = ref('')
const avatar = ref('lion')
const formError = ref('')
const saving = ref(false)

// Same rule as the backend: letters only, single spaces/hyphens/apostrophes between words.
const NICKNAME_PATTERN = "[\\p{L}]+(?:[ '\\-][\\p{L}]+)*"

const describedBy = computed(() => (formError.value ? 'nickname-hint nickname-error' : 'nickname-hint'))

async function load() {
  loadError.value = ''
  try {
    learners.value = await api.listLearners()
    adding.value = learners.value.length === 0
  } catch (e) {
    loadError.value = e.message
  }
}

async function add(event) {
  formError.value = ''
  if (!event.target.checkValidity()) {
    formError.value = 'Use letters only, like Simba or Wa-Njeri (up to 20).'
    return
  }
  saving.value = true
  try {
    const learner = await api.createLearner(nickname.value.trim(), avatar.value)
    emit('chosen', learner)
  } catch (e) {
    formError.value =
      e.status === 409
        ? 'That nickname is already used. Try another one.'
        : e.status === 422
          ? 'Use letters only, like Simba or Wa-Njeri (up to 20).'
          : e.message
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<template>
  <section class="picker">
    <h1>Who is learning today?</h1>

    <p v-if="loadError" role="alert" class="error">
      {{ loadError }}
      <button type="button" @click="load">Try again</button>
    </p>

    <ul v-if="learners.length" class="learners">
      <li v-for="learner in learners" :key="learner.id">
        <button type="button" class="learner" @click="emit('chosen', learner)">
          <span class="avatar" aria-hidden="true">{{ AVATARS[learner.avatar] ?? '🙂' }}</span>
          {{ learner.nickname }}
        </button>
      </li>
    </ul>

    <button v-if="!adding && !loadError" type="button" class="primary" @click="adding = true">
      I'm new here
    </button>

    <!-- Kept closed and out of the lesson, so children don't open it by accident. -->
    <details v-if="learners.length" class="grown-ups">
      <summary>For teachers and parents</summary>
      <p class="hint">
        Run the placement check again to find where a learner should start. The new result
        replaces the old one.
      </p>
      <ul>
        <li v-for="learner in learners" :key="learner.id">
          <span>
            <span aria-hidden="true">{{ AVATARS[learner.avatar] ?? '🙂' }}</span>
            {{ learner.nickname }}
          </span>
          <button type="button" @click="emit('check-level', learner)">
            Check level<span class="visually-hidden"> for {{ learner.nickname }}</span>
          </button>
        </li>
      </ul>
    </details>

    <form v-if="adding" class="new" novalidate @submit.prevent="add">
      <h2>Make your learner card</h2>

      <div class="field">
        <label for="nickname">Your nickname</label>
        <span id="nickname-hint" class="hint">A nickname, not your real name. Letters only.</span>
        <input
          id="nickname"
          v-model="nickname"
          name="nickname"
          required
          maxlength="20"
          :pattern="NICKNAME_PATTERN"
          autocomplete="off"
          :aria-describedby="describedBy"
          :aria-invalid="formError ? 'true' : 'false'"
        />
        <p v-if="formError" id="nickname-error" class="error">
          <span role="img" aria-label="Error">⚠️</span> {{ formError }}
        </p>
      </div>

      <fieldset class="avatars">
        <legend>Pick your animal</legend>
        <label v-for="(emoji, name) in AVATARS" :key="name" class="avatar-choice">
          <input v-model="avatar" type="radio" name="avatar" :value="name" />
          <span class="avatar" aria-hidden="true">{{ emoji }}</span>
          <span class="visually-hidden">{{ name }}</span>
        </label>
      </fieldset>

      <button type="submit" class="primary" :disabled="saving">Let's start!</button>
    </form>
  </section>
</template>

<style scoped>
.picker {
  display: grid;
  gap: 1.2rem;
  justify-items: center;
  text-align: center;
}

.learners {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 0.8rem;
  list-style: none;
  padding: 0;
  margin: 0;
}

.learner {
  display: grid;
  justify-items: center;
  gap: 0.2rem;
  min-inline-size: 8rem;
  padding: 0.8rem 1rem;
  font-size: 1.2rem;
  font-weight: 700;
}

.avatar {
  font-size: 2.6rem;
  line-height: 1;
}

.new {
  display: grid;
  gap: 1rem;
  inline-size: min(100%, 26rem);
  text-align: start;
  padding: 1.2rem;
  border-radius: 20px;
  background: var(--surface);
  border: 2px solid var(--border);
}

.new h2 {
  margin: 0;
  text-align: center;
}

.field {
  display: grid;
  gap: 0.3rem;
}

.field label {
  font-weight: 700;
}

.hint {
  color: var(--muted);
  font-size: 0.85rem;
}

.field input {
  padding: 0.4rem 0.8rem;
  border: 2px solid var(--border);
  border-radius: 12px;
  background: var(--bg);
}

.field input[aria-invalid='true'] {
  border-color: var(--try);
}

.error {
  margin: 0;
  color: var(--try);
  font-weight: 600;
}

.avatars {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  border: none;
  padding: 0;
  margin: 0;
}

.avatars legend {
  font-weight: 700;
  margin-block-end: 0.4rem;
}

.avatar-choice {
  position: relative;
  cursor: pointer;
}

.avatar-choice input {
  position: absolute;
  opacity: 0;
  inset: 0;
  margin: 0;
  cursor: pointer;
}

.grown-ups {
  inline-size: min(100%, 26rem);
  margin-block-start: 1.5rem;
  text-align: start;
  color: var(--muted);
}

.grown-ups summary {
  cursor: pointer;
  font-weight: 600;
  text-align: center;
}

.grown-ups ul {
  display: grid;
  gap: 0.4rem;
  list-style: none;
  padding: 0;
  margin: 0;
}

.grown-ups li {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.6rem;
  color: var(--text);
}

/* The picture is the visible control. Sibling selectors work in every browser. */
.avatar-choice .avatar {
  display: grid;
  place-items: center;
  inline-size: 3.6rem;
  block-size: 3.6rem;
  border: 3px solid transparent;
  border-radius: 14px;
}

.avatar-choice input:checked + .avatar {
  border-color: var(--brand);
  background: var(--brand-soft);
}

.avatar-choice input:focus-visible + .avatar {
  outline: 4px solid var(--focus);
  outline-offset: 2px;
}
</style>
