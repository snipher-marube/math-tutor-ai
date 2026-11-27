// Small wrapper around the backend API. All requests go to /api, which the Vite
// dev server proxies to FastAPI (see vite.config.js).

export class ApiError extends Error {
  constructor(status, detail) {
    super(typeof detail === 'string' ? detail : 'Something went wrong')
    this.status = status
    this.detail = detail
  }
}

async function request(method, path, body) {
  let res
  try {
    res = await fetch(`/api${path}`, {
      method,
      headers: body === undefined ? {} : { 'Content-Type': 'application/json' },
      body: body === undefined ? undefined : JSON.stringify(body),
    })
  } catch {
    throw new ApiError(0, "Can't reach the tutor. Is the backend running?")
  }
  if (res.status === 204) return null
  const data = await res.json().catch(() => null)
  if (!res.ok) throw new ApiError(res.status, data?.detail)
  return data
}

export const api = {
  listLearners: () => request('GET', '/learners'),
  createLearner: (nickname, avatar) => request('POST', '/learners', { nickname, avatar }),
  nextSkill: (learnerId) => request('GET', `/learners/${learnerId}/next-skill`),
  newProblem: (skillId, learnerId) =>
    request('POST', '/lesson/problems', { skill_id: skillId, learner_id: learnerId }),
  answer: (problemId, answer) =>
    request('POST', `/lesson/problems/${problemId}/answer`, { answer }),
  progress: (learnerId) => request('GET', `/learners/${learnerId}/progress`),
  startPlacement: (learnerId) => request('POST', `/learners/${learnerId}/placement`),
  answerPlacement: (placementId, problemId, answer) =>
    request('POST', `/placement/${placementId}/answer`, { problem_id: problemId, answer }),
  latestPlacement: (learnerId) => request('GET', `/learners/${learnerId}/placement`),
  hints: (problemId, start) =>
    request('GET', `/lesson/problems/${problemId}/hints?start=${encodeURIComponent(start)}`),
}

// The animal pictures a learner can choose. Keys match the backend's AVATARS.
export const AVATARS = {
  lion: '🦁',
  elephant: '🐘',
  giraffe: '🦒',
  zebra: '🦓',
  cheetah: '🐆',
  rhino: '🦏',
  hippo: '🦛',
  monkey: '🐒',
}
