import ast
import operator
import re

# Safe operators for evaluating simple arithmetic expressions
_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}


def _safe_eval(node):
    """Recursively evaluate an AST node using only safe arithmetic ops."""
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            return node.value
        raise ValueError("Non-numeric constant")
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    raise ValueError(f"Unsupported expression: {ast.dump(node)}")


def extract_final_answer(text: str):
    """Pull the last number after '=' or 'answer is' from model output."""
    matches = re.findall(r"(?:=|answer is)\s*(-?\d+(?:\.\d+)?)", text, re.IGNORECASE)
    if not matches:
        return None
    return float(matches[-1])


def extract_expression(question: str):
    """Strip words, keep only a simple arithmetic expression from the question."""
    # Keep digits, operators, dots, and spaces
    cleaned = re.sub(r"[^0-9+\-*/().\s]", " ", question)
    # Collapse whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    # Keep only the longest contiguous expression-like chunk
    chunks = re.findall(r"[\d\s+\-*/().]+", cleaned)
    if not chunks:
        return None
    candidate = max(chunks, key=len).strip()
    # Must contain at least one operator and two numbers to be worth evaluating
    if not re.search(r"\d", candidate) or not re.search(r"[+\-*/]", candidate):
        return None
    return candidate


def verify(question: str, model_output: str) -> dict:
    """Compare model's final answer against an independent calculation."""
    model_answer = extract_final_answer(model_output)
    expression = extract_expression(question)

    if expression is None:
        return {
            "model_answer": model_answer,
            "correct_answer": None,
            "is_correct": None,
            "reason": "Could not extract an arithmetic expression from the question",
        }

    try:
        tree = ast.parse(expression, mode="eval")
        correct_answer = float(_safe_eval(tree.body))
    except Exception as e:
        return {
            "model_answer": model_answer,
            "correct_answer": None,
            "is_correct": None,
            "reason": f"Could not evaluate expression: {e}",
        }

    if model_answer is None:
        return {
            "model_answer": None,
            "correct_answer": correct_answer,
            "is_correct": False,
            "reason": "Model did not produce a final answer",
        }

    is_correct = abs(correct_answer - model_answer) < 1e-6
    return {
        "model_answer": model_answer,
        "correct_answer": correct_answer,
        "is_correct": is_correct,
        "reason": "ok",
    }
