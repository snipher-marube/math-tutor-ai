import pytest

from services.math_verifier import extract_expression, extract_final_answer, verify


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Count on: 15, 16, 17. = 17", 17.0),
        ("So the answer is 42", 42.0),
        ("3 + 2 = 5, then 5 + 1 = 6", 6.0),
        ("I am not sure", None),
    ],
)
def test_extract_final_answer(text, expected):
    assert extract_final_answer(text) == expected


def test_extract_expression_from_question():
    assert extract_expression("What is 14 + 5?") == "14 + 5"


def test_extract_expression_word_problem_without_operator():
    assert extract_expression("Wanjiru has 5 mangoes and buys 3 more") is None


def test_verify_correct():
    result = verify("What is 7 - 4?", "Take away 4 from 7. = 3")
    assert result["is_correct"] is True
    assert result["correct_answer"] == 3.0


def test_verify_wrong_answer():
    result = verify("What is 6 * 2?", "6 groups of 2 = 10")
    assert result["is_correct"] is False
    assert result["correct_answer"] == 12.0


def test_verify_missing_model_answer():
    result = verify("What is 2 + 2?", "Let's count together!")
    assert result["is_correct"] is False
    assert result["reason"] == "Model did not produce a final answer"


def test_verify_division_by_zero_is_handled():
    result = verify("What is 4 / 0?", "= 0")
    assert result["is_correct"] is None
