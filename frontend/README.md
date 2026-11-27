# Frontend

Vue 3 + Vite web app for learners: pick or create a nickname, then practise one problem at a time with big number buttons, kind feedback and hints.

| File | What it does |
| --- | --- |
| `src/App.vue` | Choose a learner, then the placement check (new learners only), then the lesson |
| `src/components/LearnerPicker.vue` | List learners, or make a learner card (nickname and animal). "For teachers and parents" re-runs a learner's placement check |
| `src/components/PlacementView.vue` | The placement check: a few questions to find where a new learner should start |
| `src/components/LessonView.vue` | One problem at a time: answer, feedback, hints, next problem |
| `src/components/NumberPad.vue` | Big number buttons (laptop number keys, Backspace and Enter work too) |
| `src/components/HintPanel.vue` | The hint ladder, one step at a time |
| `src/components/ProblemVisual.vue` | Draws emoji to count (tap each one to count it), ten-frames, number lines and tens-and-ones blocks |
| `src/lib/api.js` | Calls the backend at `/api` |
| `src/lib/speech.js` | Read-aloud: turns maths into words and speaks with an on-device voice |
| `src/lib/focus.js` | Takes focus off a button after a mouse or touch click, so Enter always checks the answer |
| `src/lib/placement.js` | Decides when a learner takes the placement check (new learners only) |
| `src/lib/counting.js` | Picks the emoji to count (mangoes, goats, balls...) and names them in counting questions |

```bash
npm ci
npm run dev     # http://localhost:5173
npm run build   # production build in dist/
```

The backend must be running (see [../docs/SETUP.md](../docs/SETUP.md)). In development, Vite sends `/api` requests to `http://localhost:8000`. To use a backend on another port, set `VITE_API_TARGET`:

```bash
VITE_API_TARGET=http://localhost:8001 npm run dev
```

Rules for this app:
- **Offline only:** no CDNs, remote fonts or remote images. Bundle every asset.
- **For children aged 6–9:** big touch targets (at least 48px, 56px on touch screens), high contrast, light and dark mode, and short text.
- **Never show the answer before the child gives it.** A number line's `blank` box stays empty, and `misconception` ids are for teachers, not children.
- **Accessible:** real `<button>`s and labelled inputs, one polite live region for feedback, and visible focus outlines.
- **Read-aloud uses on-device English voices only.** Windows, Android, macOS, iOS and Chromebooks include them. On Linux, install speech packages (for example `speech-dispatcher` and `espeak-ng`), or the 🔊 buttons stay hidden. The on/off choice is saved on the device.

Run the tests with `npm test`. They use [Vitest](https://vitest.dev) with [Vue Test Utils](https://test-utils.vuejs.org) on a small browser-like DOM ([happy-dom](https://github.com/capricorn86/happy-dom)), so no browser is needed:

- `src/lib/*.test.js`: read-aloud text, focus handling, when to show the placement check, emoji picking
- `src/components/*.test.js`: the number pad, pictures (tapping to count, take-away), the lesson, placement and learner screens, with the backend API mocked
- `src/App.test.js`: which screen each learner sees
