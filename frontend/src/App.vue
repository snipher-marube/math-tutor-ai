<script setup>
// The app has two screens: choose a learner, then the lesson.
import { ref } from 'vue'
import LearnerPicker from './components/LearnerPicker.vue'
import LessonView from './components/LessonView.vue'

const learner = ref(null)
</script>

<template>
  <main class="app">
    <LessonView v-if="learner" :key="learner.id" :learner="learner" @change-learner="learner = null" />
    <LearnerPicker v-else @chosen="learner = $event" />
  </main>
</template>

<style scoped>
.app {
  inline-size: min(100% - 2rem, 40rem);
  margin-inline: auto;
  padding-block: 1.5rem 3rem;
}
</style>
