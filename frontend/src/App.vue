<script setup>
// The app's screens: choose a learner, then (for a new learner) the placement
// check, then the lesson. Teachers can re-run the check from the lesson screen.
import { ref } from 'vue'
import LearnerPicker from './components/LearnerPicker.vue'
import LessonView from './components/LessonView.vue'
import PlacementView from './components/PlacementView.vue'
import { api } from './lib/api.js'
import { needsPlacement } from './lib/placement.js'

const learner = ref(null)
const screen = ref('pick') // 'pick' | 'placement' | 'lesson'
const error = ref('')

async function choose(chosen) {
  error.value = ''
  try {
    screen.value = (await needsPlacement(api, chosen.id)) ? 'placement' : 'lesson'
    learner.value = chosen
  } catch (e) {
    error.value = e.message
  }
}

function changeLearner() {
  learner.value = null
  screen.value = 'pick'
}
</script>

<template>
  <main class="app">
    <p v-if="error" role="alert" class="error">{{ error }}</p>
    <PlacementView
      v-if="learner && screen === 'placement'"
      :key="`placement-${learner.id}`"
      :learner="learner"
      @done="screen = 'lesson'"
      @change-learner="changeLearner"
    />
    <LessonView
      v-else-if="learner && screen === 'lesson'"
      :key="`lesson-${learner.id}`"
      :learner="learner"
      @change-learner="changeLearner"
      @check-level="screen = 'placement'"
    />
    <LearnerPicker v-else @chosen="choose" />
  </main>
</template>

<style scoped>
.app {
  inline-size: min(100% - 2rem, 40rem);
  margin-inline: auto;
  padding-block: 1.5rem 3rem;
}

.error {
  color: var(--try);
  font-weight: 600;
}
</style>
