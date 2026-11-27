# Child safety and privacy guidelines

Our users are Lower Primary learners (Grades 1–3), about **6–9 years old**. Many are still learning to read. Every contributor must follow these rules. Reviewers will check them on every PR that touches prompts, content, UI or data handling.

## Content

- ✅ Age-appropriate, kind, encouraging language. Never shame a wrong answer. Praise effort and strategy, not ability.
- ✅ Don't rely on reading alone. Pair text with pictures and read-aloud audio where possible.
- ✅ Inclusive examples that reflect Kenya's diversity of names, regions, genders and abilities.
- ❌ No violence, scary themes, romance, brands or adverts, gambling (including betting examples), alcohol, religion or politics.
- ❌ No links to external websites, and no instructions to go online.
- ❌ No stereotypes (for example, "girls are bad at maths").

## Model behaviour

- The system prompt (`backend/prompts/tutor_system.txt`) must keep the tutor **on maths topics**, and it should redirect off-topic questions gently.
- The tutor must never ask for personal information (full name, school, location, phone number).
- Treat model output as untrusted. Before shipping, check new prompts against tricky inputs: off-topic questions, rude messages, and attempts to make the tutor ignore its instructions.
- Correctness matters. A confidently wrong answer teaches the wrong thing. Correct answers must be computed in code, and the model never decides whether a child's answer is right (see [PEDAGOGY.md](PEDAGOGY.md)).

## Data and privacy

- **Everything stays on the device.** No telemetry, analytics, crash reporting, or remote logging.
- **Read-aloud uses on-device voices only.** Online voices (such as Chrome's "Google" voices) send the text to a server, so they are never used.
- Don't store learner questions unless a feature clearly needs it. If it does, store them locally, make deletion easy, and document it.
- No accounts or logins for learners. On shared devices, a learner picks a nickname or picture, never a real full name. The API enforces this as far as it can: nicknames are letters only (1–20), so phone numbers and email addresses are rejected.
- **Learner progress** (skills practised, mastery, answers) is stored only on the device, in a local SQLite file (`backend/data/math_tutor.db` by default). It must never be sent anywhere. Teachers and parents can view it (`GET /api/learners/{id}/progress`), reset it (`DELETE /api/learners/{id}/progress`), or delete the learner and everything about them (`DELETE /api/learners/{id}`). Deleting the file removes all learner data on the device.
- There are no passwords, so anyone using the device can view or reset progress. That suits a shared family or classroom device, and keeps children's details out of the system entirely.
- Never commit real learner data, photos or voice recordings to this repository.

## Reporting a concern

If you see the tutor produce unsafe content, open an issue with the **Curriculum / learning content** template (leave out any personal data). For sensitive concerns, follow [SECURITY.md](../SECURITY.md).
