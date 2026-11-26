"""Tests for the skill map loader. Bad files are written to a temp folder."""

import textwrap

import pytest

from services.skill_map import SkillMapError, load_skill_map


def _skill(skill_id, grade=1, requires=(), lo=0, hi=10):
    reqs = ", ".join(requires)
    return f"""
  - id: {skill_id}
    name: Skill {skill_id}
    grade: {grade}
    requires: [{reqs}]
    numbers: {{ min: {lo}, max: {hi} }}
    description: Test skill.
    examples: ["1 + 1 = ?"]
"""


def _write(folder, name, *skills, strand="numbers", substrand="addition"):
    body = f"strand: {strand}\nsubstrand: {substrand}\nskills:" + "".join(skills)
    (folder / name).write_text(body)


def _problems(folder) -> str:
    with pytest.raises(SkillMapError) as exc:
        load_skill_map(folder)
    return "\n".join(exc.value.problems)


# --- The skill map we ship ---------------------------------------------------


def test_shipped_skill_map_is_valid():
    skill_map = load_skill_map()
    assert len(skill_map) >= 9
    assert "add-within-10" in skill_map


def test_shipped_teaching_order_puts_prerequisites_first():
    seen: set[str] = set()
    for skill in load_skill_map():
        assert set(skill.requires) <= seen, f"{skill.id} comes before its prerequisites"
        seen.add(skill.id)


def test_prerequisites_lookup():
    skill_map = load_skill_map()
    names = [s.id for s in skill_map.prerequisites("add-within-100-no-regrouping")]
    assert names == ["add-within-20", "add-tens"]


def test_unknown_skill_lookup_raises():
    with pytest.raises(KeyError, match="no-such-skill"):
        load_skill_map().get("no-such-skill")


# --- Valid custom files ------------------------------------------------------


def test_prerequisites_can_live_in_another_file(tmp_path):
    _write(tmp_path, "a.yaml", _skill("add-small", requires=["count"]))
    _write(tmp_path, "b.yaml", _skill("count"), substrand="whole-numbers")
    skill_map = load_skill_map(tmp_path)
    assert [s.id for s in skill_map] == ["count", "add-small"]
    assert skill_map.get("add-small").substrand == "addition"
    assert skill_map.get("count").source == "b.yaml"


# --- Mistakes a teacher could make -------------------------------------------


def test_no_files(tmp_path):
    assert "No .yaml skill files" in _problems(tmp_path)


def test_invalid_yaml(tmp_path):
    (tmp_path / "bad.yaml").write_text("skills: [unclosed")
    assert "bad.yaml: not valid YAML" in _problems(tmp_path)


def test_duplicate_id_across_files(tmp_path):
    _write(tmp_path, "a.yaml", _skill("count"))
    _write(tmp_path, "b.yaml", _skill("count"))
    assert "'count' is defined twice (also in a.yaml)" in _problems(tmp_path)


def test_unknown_prerequisite(tmp_path):
    _write(tmp_path, "a.yaml", _skill("add", requires=["cuont"]))
    assert "'add' requires unknown skill 'cuont'" in _problems(tmp_path)


def test_requires_itself(tmp_path):
    _write(tmp_path, "a.yaml", _skill("add", requires=["add"]))
    assert "'add' requires itself" in _problems(tmp_path)


def test_prerequisite_loop(tmp_path):
    _write(
        tmp_path,
        "a.yaml",
        _skill("a", requires=["c"]),
        _skill("b", requires=["a"]),
        _skill("c", requires=["b"]),
    )
    assert "prerequisites form a loop: a -> c -> b -> a" in _problems(tmp_path)


def test_prerequisite_from_a_later_grade(tmp_path):
    _write(tmp_path, "a.yaml", _skill("easy", grade=1, requires=["hard"]), _skill("hard", grade=2))
    assert "'easy' (grade 1) requires 'hard', which is a later grade (2)" in _problems(tmp_path)


@pytest.mark.parametrize(
    ("skill", "expected"),
    [
        (_skill("Add_Within_10"), "skills.0.id"),
        (_skill("add", grade=4), "skills.0.grade"),
        (_skill("add", lo=20, hi=10), "min (20) is bigger than max (10)"),
        (_skill("add", lo=-1), "skills.0.numbers.min"),
    ],
)
def test_invalid_skill_fields(tmp_path, skill, expected):
    _write(tmp_path, "a.yaml", skill)
    assert expected in _problems(tmp_path)


def test_unknown_field_is_rejected(tmp_path):
    """Catches typos like 'require:' instead of 'requires:'."""
    _write(tmp_path, "a.yaml", _skill("add") + "    require: [count]\n")
    assert "skills.0.require: Extra inputs are not permitted" in _problems(tmp_path)


def test_invalid_strand(tmp_path):
    _write(tmp_path, "a.yaml", _skill("add"), strand="algebra")
    assert "a.yaml: strand" in _problems(tmp_path)


def test_all_problems_reported_together(tmp_path):
    _write(tmp_path, "a.yaml", _skill("add", requires=["missing"]))
    _write(tmp_path, "b.yaml", _skill("add"))
    problems = _problems(tmp_path)
    assert "defined twice" in problems
    assert "unknown skill 'missing'" in problems


def test_cli_reports_problems(tmp_path, monkeypatch, capsys):
    import services.skill_map as skill_map_module

    _write(tmp_path, "a.yaml", _skill("add", requires=["missing"]))
    monkeypatch.setattr(skill_map_module, "load_skill_map", lambda: load_skill_map(tmp_path))
    assert skill_map_module.main() == 1
    assert "unknown skill 'missing'" in capsys.readouterr().err


def test_docs_example_is_valid(tmp_path):
    """The example in docs/SKILLS.md must stay valid."""
    example = textwrap.dedent(
        """
        strand: numbers
        substrand: subtraction
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
        """
    )
    (tmp_path / "subtraction.yaml").write_text(example)
    assert "subtract-within-10" in load_skill_map(tmp_path)
