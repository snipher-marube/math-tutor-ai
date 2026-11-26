"""Load and validate the skill map from the YAML files in `backend/skills/`.

The skill map is the list of small, ordered skills the lesson engine teaches.
Teachers edit the YAML files. This module checks them and gives the rest of the
backend a simple way to look skills up. See docs/SKILLS.md for the file format.

Check the shipped skill map from the command line:

    uv run python -m services.skill_map
"""

from __future__ import annotations

import sys
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

SKILLS_DIR = Path(__file__).resolve().parent.parent / "skills"

SkillId = Annotated[str, Field(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$")]
Strand = Literal["numbers", "measurement", "geometry"]


class NumberRange(BaseModel):
    """The smallest and largest numbers a learner sees in this skill (problems and answers)."""

    model_config = ConfigDict(extra="forbid")

    min: int = Field(ge=0)
    max: int = Field(ge=0)

    @model_validator(mode="after")
    def _min_not_above_max(self) -> NumberRange:
        if self.min > self.max:
            raise ValueError(f"min ({self.min}) is bigger than max ({self.max})")
        return self


class _SkillEntry(BaseModel):
    """One skill as written in a YAML file."""

    model_config = ConfigDict(extra="forbid")

    id: SkillId
    name: str = Field(min_length=1)
    grade: int = Field(ge=1, le=3)
    requires: list[SkillId] = []
    numbers: NumberRange
    description: str = Field(min_length=1)
    examples: list[str] = Field(min_length=1)


class _SkillFile(BaseModel):
    """A whole YAML file: one CBE sub-strand."""

    model_config = ConfigDict(extra="forbid")

    strand: Strand
    substrand: SkillId
    skills: list[_SkillEntry] = Field(min_length=1)


@dataclass(frozen=True)
class Skill:
    id: str
    name: str
    grade: int
    strand: str
    substrand: str
    requires: tuple[str, ...]
    numbers: NumberRange
    description: str
    examples: tuple[str, ...]
    source: str  # file name, used in error messages


class SkillMapError(Exception):
    """Raised when the skill files have problems. Lists every problem found."""

    def __init__(self, problems: list[str]):
        self.problems = problems
        super().__init__("Skill map has problems:\n" + "\n".join(f"  - {p}" for p in problems))


class SkillMap:
    """All skills, checked and ready to use. Iterates in teaching order."""

    def __init__(self, skills: list[Skill]):
        self._skills = {s.id: s for s in skills}
        self._ordered = _teaching_order(skills)

    def __len__(self) -> int:
        return len(self._skills)

    def __iter__(self) -> Iterator[Skill]:
        return iter(self._ordered)

    def __contains__(self, skill_id: object) -> bool:
        return skill_id in self._skills

    def get(self, skill_id: str) -> Skill:
        try:
            return self._skills[skill_id]
        except KeyError:
            raise KeyError(f"Unknown skill: {skill_id!r}") from None

    def prerequisites(self, skill_id: str) -> list[Skill]:
        """The skills a learner needs directly before this one."""
        return [self._skills[r] for r in self.get(skill_id).requires]


def load_skill_map(directory: Path = SKILLS_DIR) -> SkillMap:
    """Read every `*.yaml` file in `directory` and check the skills as a whole.

    Raises SkillMapError listing every problem, so a teacher can fix them all at once.
    """
    problems: list[str] = []
    skills: list[Skill] = []

    files = sorted(directory.glob("*.yaml"))
    if not files:
        raise SkillMapError([f"No .yaml skill files found in {directory}"])

    for path in files:
        skills.extend(_read_file(path, problems))

    problems.extend(_check_map(skills))
    if problems:
        raise SkillMapError(problems)
    return SkillMap(skills)


def _read_file(path: Path, problems: list[str]) -> list[Skill]:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        problems.append(f"{path.name}: not valid YAML ({e})")
        return []

    try:
        parsed = _SkillFile.model_validate(raw)
    except ValidationError as e:
        for err in e.errors():
            where = ".".join(str(part) for part in err["loc"])
            problems.append(f"{path.name}: {where}: {err['msg']}")
        return []

    return [
        Skill(
            id=entry.id,
            name=entry.name,
            grade=entry.grade,
            strand=parsed.strand,
            substrand=parsed.substrand,
            requires=tuple(entry.requires),
            numbers=entry.numbers,
            description=entry.description.strip(),
            examples=tuple(entry.examples),
            source=path.name,
        )
        for entry in parsed.skills
    ]


def _check_map(skills: list[Skill]) -> list[str]:
    """Checks that need all skills at once: duplicates, prerequisites, loops."""
    problems: list[str] = []
    by_id: dict[str, Skill] = {}

    for skill in skills:
        if skill.id in by_id:
            other = by_id[skill.id]
            problems.append(
                f"{skill.source}: skill '{skill.id}' is defined twice (also in {other.source})"
            )
        else:
            by_id[skill.id] = skill

    for skill in by_id.values():
        for req in skill.requires:
            if req == skill.id:
                problems.append(f"{skill.source}: '{skill.id}' requires itself")
            elif req not in by_id:
                problems.append(f"{skill.source}: '{skill.id}' requires unknown skill '{req}'")
            elif by_id[req].grade > skill.grade:
                problems.append(
                    f"{skill.source}: '{skill.id}' (grade {skill.grade}) requires "
                    f"'{req}', which is a later grade ({by_id[req].grade})"
                )

    cycle = _find_cycle(by_id)
    if cycle:
        problems.append("prerequisites form a loop: " + " -> ".join(cycle))

    return problems


def _find_cycle(by_id: dict[str, Skill]) -> list[str] | None:
    """Return one prerequisite loop (e.g. [a, b, a]) if any exists."""
    visiting: list[str] = []
    done: set[str] = set()

    def visit(skill_id: str) -> list[str] | None:
        if skill_id in visiting:
            return visiting[visiting.index(skill_id) :] + [skill_id]
        if skill_id in done or skill_id not in by_id:
            return None
        visiting.append(skill_id)
        for req in by_id[skill_id].requires:
            if req != skill_id and (loop := visit(req)):
                return loop
        visiting.pop()
        done.add(skill_id)
        return None

    for skill_id in by_id:
        if loop := visit(skill_id):
            return loop
    return None


def _teaching_order(skills: list[Skill]) -> list[Skill]:
    """Prerequisites first. Ties keep the order the skills appear in the files."""
    by_id = {s.id: s for s in skills}
    placed: set[str] = set()
    ordered: list[Skill] = []

    def place(skill: Skill) -> None:
        if skill.id in placed:
            return
        for req in skill.requires:
            place(by_id[req])
        placed.add(skill.id)
        ordered.append(skill)

    for skill in sorted(skills, key=lambda s: s.grade):  # stable: file order within a grade
        place(skill)
    return ordered


def main() -> int:
    try:
        skill_map = load_skill_map()
    except SkillMapError as e:
        print(e, file=sys.stderr)
        return 1

    print(f"Skill map OK: {len(skill_map)} skills, in teaching order:\n")
    for skill in skill_map:
        needs = ", ".join(skill.requires) or "-"
        print(f"  Grade {skill.grade}  {skill.id:<32} needs: {needs}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
