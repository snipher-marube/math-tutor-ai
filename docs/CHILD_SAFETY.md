# Child safety and privacy guidelines

Our users are about **7–8 years old**. Every contributor must follow these rules. Reviewers will check them on every PR that touches prompts, content, UI or data handling.

## Content

- ✅ Age-appropriate, kind, encouraging language. Never shame a wrong answer.
- ✅ Inclusive examples that reflect Kenya's diversity of names, regions, genders and abilities.
- ❌ No violence, scary themes, romance, brands or adverts, gambling (including betting examples), alcohol, religion or politics.
- ❌ No links to external websites, and no instructions to go online.
- ❌ No stereotypes (for example, "girls are bad at maths").

## Model behaviour

- The system prompt must keep the tutor **on maths topics**, and it should redirect off-topic questions gently.
- The tutor must never ask for personal information (full name, school, location, phone number).
- Treat model output as untrusted. Before shipping, check new prompts against tricky inputs: off-topic questions, rude messages, and attempts to make the tutor ignore its instructions.
- Correctness matters. A confidently wrong answer teaches the wrong thing. Prefer verifying arithmetic in code.

## Data and privacy

- **Everything stays on the device.** No telemetry, analytics, crash reporting, or remote logging.
- Don't store learner questions unless a feature clearly needs it. If it does, store them locally, make deletion easy, and document it.
- No accounts or logins for learners.
- Never commit real learner data, photos or voice recordings to this repository.

## Reporting a concern

If you see the tutor produce unsafe content, open an issue with the **Curriculum / learning content** template (leave out any personal data). For sensitive concerns, follow [SECURITY.md](../SECURITY.md).
