<script setup>
// Big number buttons for children who are still learning to type.
// On a laptop, the number keys, Backspace and Enter work too.
import { onBeforeUnmount, onMounted } from 'vue'

const props = defineProps({
  modelValue: { type: String, required: true },
  maxLength: { type: Number, default: 3 },
  disabled: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue', 'submit'])

function press(digit) {
  if (props.disabled || props.modelValue.length >= props.maxLength) return
  // Avoid leading zeros like "07", but allow a single "0".
  const next = props.modelValue === '0' ? String(digit) : props.modelValue + digit
  emit('update:modelValue', next)
}

function erase() {
  if (!props.disabled) emit('update:modelValue', props.modelValue.slice(0, -1))
}

function submit() {
  if (!props.disabled && props.modelValue !== '') emit('submit')
}

function onKey(e) {
  // Leave typing alone when focus is in a text field.
  if (e.target instanceof HTMLInputElement || e.altKey || e.ctrlKey || e.metaKey) return
  if (/^[0-9]$/.test(e.key)) press(Number(e.key))
  else if (e.key === 'Backspace') erase()
  else if (e.key === 'Enter' && !(e.target instanceof HTMLButtonElement)) submit()
}

onMounted(() => window.addEventListener('keydown', onKey))
onBeforeUnmount(() => window.removeEventListener('keydown', onKey))
</script>

<template>
  <div class="pad" role="group" aria-label="Number pad">
    <button v-for="d in [1, 2, 3, 4, 5, 6, 7, 8, 9]" :key="d" type="button" :disabled="disabled" @click="press(d)">
      {{ d }}
    </button>
    <button type="button" class="erase" :disabled="disabled || modelValue === ''" aria-label="Delete" @click="erase">
      ⌫
    </button>
    <button type="button" :disabled="disabled" @click="press(0)">0</button>
    <button type="button" class="primary check" :disabled="disabled || modelValue === ''" @click="submit">
      Check
    </button>
  </div>
</template>

<style scoped>
.pad {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.6rem;
  max-inline-size: 22rem;
  margin-inline: auto;
}

.pad button {
  min-block-size: 4rem;
  font-size: 1.8rem;
  font-weight: 700;
}

.pad .check {
  font-size: 1.2rem;
}
</style>
