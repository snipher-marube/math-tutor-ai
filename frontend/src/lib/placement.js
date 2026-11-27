// Deciding when a learner should take the placement check.
// See the placement check in docs/PEDAGOGY.md.

// A brand-new learner (no placement check yet, and nothing practised) takes the
// check first, so they start at the right level. Everyone else goes straight to
// the lesson. Teachers can re-run the check from the learner screen.
export async function needsPlacement(api, learnerId) {
  try {
    await api.latestPlacement(learnerId)
    return false // already placed
  } catch (e) {
    if (e?.status !== 404) throw e
  }
  const progress = await api.progress(learnerId)
  return progress.length === 0
}
