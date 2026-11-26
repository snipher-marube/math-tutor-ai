# The skill map: a guide for teachers

The **skill map** is the list of small maths skills the tutor teaches, in order. Each skill says which skills a child needs first. The lesson engine uses it to decide what each child learns next (see [PEDAGOGY.md](PEDAGOGY.md#1-skill-map-and-mastery)).

You don't need to know how to program to review or add skills. They're plain text files.

## Where the skills live

```
backend/skills/
├── whole_numbers.yaml   counting, tens and ones
└── addition.yaml        add within 10, make 10, add within 20, ...
```

There is **one file per CBE sub-strand**. The files are in [YAML](https://yaml.org), a simple text format where indentation (spaces at the start of a line) matters.

## What a skill looks like

```yaml
strand: numbers          # numbers, measurement or geometry
substrand: subtraction   # the CBE sub-strand this file covers

skills:
  - id: subtract-within-10
    name: Subtract within 10
    grade: 1
    requires: []
    numbers: { min: 0, max: 10 }
    description: >
      Take away a small group and find how many are left.
    examples:
      - Amina has 7 oranges and eats 2. How many are left?
```

| Field | What to write | Rules |
| --- | --- | --- |
| `id` | A short, unique name for the skill | Lowercase letters, numbers and dashes only, like `add-within-20`. Must be unique across **all** files |
| `name` | The skill's name, as a teacher would say it | Any text |
| `grade` | The grade where this skill is usually taught | `1`, `2` or `3` |
| `requires` | The `id`s of skills a child needs **directly** before this one | Use `[]` if none. Each one must exist (in any file), and can't be from a later grade |
| `numbers` | The smallest and largest numbers the child sees, in problems and answers | Whole numbers, `min` no bigger than `max` |
| `description` | What the child can do once they've mastered it | A sentence or two, for teachers and contributors |
| `examples` | One or more example problems | At least one. Use Kenyan names, shillings and everyday objects |

**Only list direct prerequisites.** If `add-within-20` needs `make-10`, and `make-10` needs `add-within-10`, then `add-within-20` only lists `make-10`. The chain takes care of the rest.

## Adding or changing a skill

1. Open the right file in `backend/skills/`, or create a new one for a new sub-strand, such as `subtraction.yaml`.
2. Add or edit a skill, copying the layout above. Keep the same indentation.
3. Check your work:
   ```bash
   make skills
   ```
   If everything is fine, you'll see the skills listed in teaching order:
   ```
   Skill map OK: 9 skills, in teaching order:

     Grade 1  count-to-20                      needs: -
     Grade 1  add-within-10                    needs: count-to-20
     ...
   ```
   If something is wrong, you'll get a list of problems, with the file name:
   ```
   Skill map has problems:
     - addition.yaml: 'add-within-20' requires unknown skill 'make-ten'
     - addition.yaml: 'add-within-100-with-regrouping' requires unknown skill 'add-within-100-no-regroupin'
   ```
   Problems are checked in two rounds. First, each file's **format** (indentation, field names, grade, numbers). If a file has a format problem, fix it and run `make skills` again. The checks **between** skills (prerequisites, duplicates, loops) then run. A format problem looks like this, where `skills.0` means the first skill in the file:
   ```
   Skill map has problems:
     - addition.yaml: skills.0.grade: Input should be less than or equal to 3
   ```
4. Open a pull request (see [CONTRIBUTING.md](../CONTRIBUTING.md)). CI runs the same checks.

Not comfortable with Git? Open an issue with the **Curriculum / learning content** template and describe the skill in your own words. A contributor will turn it into YAML.

## What the checks catch

- A file that isn't valid YAML, for example broken indentation
- A missing or misspelt field, for example `require:` instead of `requires:`
- An `id` with capitals, spaces or underscores
- A grade outside 1–3, or a `numbers` range where `min` is bigger than `max`
- The same `id` used twice
- A prerequisite that doesn't exist, often a typo
- A skill that requires itself, or a loop (A needs B, B needs C, C needs A)
- A skill that requires a skill from a **later** grade

## Tips for good skills

- **Small steps.** A skill should be something a child can master in a few short sessions. If it feels big, split it.
- **One idea per skill.** "Add within 100 without regrouping" and "with regrouping" are separate skills, because regrouping is a new idea.
- **Follow the CBE curriculum.** Check against [CURRICULUM.md](CURRICULUM.md) and the KICD curriculum designs.
- **Think about common mistakes.** If you know a mistake children often make with a skill, note it in your pull request or issue. Misconception rules are coming next on the [roadmap](ROADMAP.md).

## Every skill needs a problem generator

The tutor makes practice problems for each skill with a small piece of code called a **problem generator**. It picks new numbers each time, inside the skill's `numbers` range, and calculates the answer, so answers are always correct.

To see sample problems for every skill:

```bash
make problems
```

```
add-within-20  (Grade 1, Add within 20)
  8 + 3 = ?                                     answer: 11
  8 + 9 = ?                                     answer: 17
  ...
```

**Adding a new skill?** It also needs a generator, which is written in Python. If you're not a developer, open your pull request anyway, describe what the problems should look like (with examples), and a developer will add the generator before it's merged. The test `test_every_shipped_skill_has_a_generator` will list the skills that still need one.

## For developers

The loader is `backend/services/skill_map.py`:

```python
from services.skill_map import load_skill_map

skill_map = load_skill_map()            # raises SkillMapError listing every problem
skill = skill_map.get("add-within-20")
skill_map.prerequisites("add-within-20")  # direct prerequisites, as Skill objects
for skill in skill_map:                 # teaching order: prerequisites first
    ...
```

Tests are in `backend/tests/test_skill_map.py`. One of them loads the shipped skill files, so a broken skill file fails CI.

### Writing a problem generator

Generators live in `backend/services/problems.py`. Register one per skill id:

```python
@generator("add-within-10")
def _add_within_10(skill: Skill, rng: random.Random) -> Problem:
    total = rng.randint(2, skill.numbers.max)
    a = rng.randint(1, total - 1)
    return _add(skill, a, total - a)
```

Rules:
- **Build the problem from the skill's rules**, rather than picking random numbers and retrying until they fit. That way the answer is correct by construction and generation is always fast.
- **Stay inside `skill.numbers`.** All operands and the answer must be within the range in the YAML.
- **Practise this skill, not a neighbouring one.** For example, `add-within-20` only uses totals above 10, because bridging through 10 is the new idea; smaller totals belong to `add-within-10`.
- **Always use the `rng` passed in**, never the global `random`, so tests can repeat problems with a seed.
- Add the problem's `kind` to `_expected_answer` in `tests/test_problems.py`, plus a test for the skill's own rule. The shared tests already generate 2,000 problems per skill and check every answer and range.
