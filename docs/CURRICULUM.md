# Curriculum scope: CBE Lower Primary Mathematics (Grades 1–3)

Kenya's Competency Based Education (CBE, formerly CBC) organises Lower Primary Mathematics Activities into **strands** and **sub-strands**. This file defines what the tutor covers. It is the starting point for the **skill map** described in [PEDAGOGY.md](PEDAGOGY.md).

> ⚠️ **Verify before relying on this.** This is a working summary written for contributors. It is not an official document, and the number ranges below are approximate. The source of truth is the **KICD Mathematics Activities Curriculum Designs for Grades 1, 2 and 3**. If you have the official documents, please help us check this page, add learning-outcome references, and fix any gaps (use the *Curriculum / learning content* issue template).

## Strands and progression

The same three strands run through all three grades. Each grade goes further.

### 1. Numbers

| Sub-strand | Grade 1 | Grade 2 | Grade 3 |
| --- | --- | --- | --- |
| Number concept | Sort, group, match and order objects. Simple patterns | Number patterns | Number patterns with larger numbers |
| Whole numbers | Count, read and write small numbers (around 1–100). Number words | Numbers up to about 100. Place value (tens and ones). Compare and order | Numbers up to about 1,000. Place value (hundreds, tens, ones) |
| Addition | Add small numbers, within about 20, using objects | Add within 100, with and without regrouping | Add larger numbers, with regrouping |
| Subtraction | Take away within about 20, using objects | Subtract within 100, with and without regrouping. Link to addition | Subtract larger numbers, with regrouping |
| Multiplication | — | Repeated addition with small numbers | Multiplication facts for small tables (for example 2, 3, 4, 5, 10) |
| Division | — | Sharing and grouping equally, small numbers | Division as sharing and grouping. Link to multiplication |
| Fractions | Halves of objects (introductory) | ½ and ¼ of a whole and of a group | ½, ¼ and ⅛. Compare simple fractions |

### 2. Measurement

| Sub-strand | Grade 1 | Grade 2 | Grade 3 |
| --- | --- | --- | --- |
| Length | Compare (longer, shorter). Non-standard units (hand spans, strides) | Non-standard units, then the metre | Metres and centimetres |
| Mass | Compare (heavier, lighter) | Non-standard units, then the kilogram | Kilograms. Compare and estimate |
| Capacity | Compare (holds more, holds less) | Non-standard units, then the litre | Litres. Compare and estimate |
| Time | Daily activities, days of the week | Days, months, telling time by the hour and half hour | Telling time, including quarter hours. Simple durations |
| Money | Recognise Kenyan coins | Coins and notes. Add and subtract small amounts | Larger amounts. Buying, selling and giving change |

### 3. Geometry

| Sub-strand | Grade 1 | Grade 2 | Grade 3 |
| --- | --- | --- | --- |
| Lines | Straight and curved lines | Drawing straight and curved lines | Lines in shapes and patterns |
| Shapes | Recognise everyday 2D and 3D shapes | Rectangles, squares, triangles, circles. Patterns with shapes | Sort and describe shapes. Patterns |
| Position | Positional words (in, on, under, next to) | — | — |

## From curriculum to skill map

Each sub-strand gets broken into small, ordered skills with prerequisites, so the lesson engine can teach at the right level (see [PEDAGOGY.md](PEDAGOGY.md#1-skill-map-and-mastery)). For example, addition from Grade 1 to Grade 3:

| Skill | Typical grade | Needs first |
| --- | --- | --- |
| Count objects to 20 | 1 | — |
| Add within 10 using objects | 1 | Count objects to 20 |
| Make 10 (number bonds to 10) | 1 | Add within 10 |
| Add within 20 | 1–2 | Make 10 |
| Add tens (20 + 30) | 2 | Place value: tens and ones |
| Add within 100, no regrouping | 2 | Add within 20, add tens |
| Add within 100, with regrouping | 2 | Add within 100, no regrouping |
| Add within 1,000 | 3 | Add within 100, with regrouping; place value: hundreds |

The skill map lives in `backend/skills/` as data files that teachers can review without writing code. See [SKILLS.md](SKILLS.md).

## How the tutor should teach

The full approach is in [PEDAGOGY.md](PEDAGOGY.md). In short:

- **Concrete → pictorial → abstract.** Objects first, then pictures, then numbers.
- **Hints, not answers.** Climb the hint ladder instead of revealing the answer.
- **Kenyan context.** Shillings, mandazi, sukuma wiki, matatus, local names, and market scenes.
- **Language.** Simple English, read aloud for children who can't read well yet. Kiswahili is planned.
- **Encourage.** Praise effort and strategy.

## Out of scope

- Content above Grade 3 (long multiplication, decimals, negative numbers, and so on). The tutor should gently say it's a topic for later grades.
- Non-maths subjects. The tutor should steer back to maths.

## Contributing content

Good content contributions include:
- Checking this page against the official KICD curriculum designs
- Breaking a sub-strand into ordered skills with prerequisites
- Common mistakes children make for a skill, and how a teacher responds (the misconception list in [PEDAGOGY.md](PEDAGOGY.md#5-learn-from-wrong-answers-misconceptions))
- Sample problems per skill with correct answers, for the evaluation set
- Reports of wrong or confusing tutor answers
