"""Property-based testing for Parsethon v0.2.0 safety and reversibility.

Validates:
1. Lossless source reconstruction across arbitrary token streams.
2. Bidirectional round-trip translation reversibility.
3. AST equivalence between original and round-tripped code.
4. Execution equivalence across Python constructs under CPython runtime.
"""

import ast
from hypothesis import given, settings, strategies as st
import pytest

from parsethon.runtime import execute
from parsethon.tokenizer import ParsethonTokenizer
from parsethon.translator import translate_from_python, translate_to_python


def _strip_locations(node: ast.AST) -> ast.AST:
    """Strip location and context attributes for structural AST comparison."""
    for n in ast.walk(node):
        for attr in ("lineno", "col_offset", "end_lineno", "end_col_offset", "ctx"):
            if hasattr(n, attr):
                delattr(n, attr)
    return node


def assert_ast_equivalent(code1: str, code2: str) -> None:
    """Assert that two Python code strings produce identical AST structures."""
    t1 = _strip_locations(ast.parse(code1))
    t2 = _strip_locations(ast.parse(code2))
    assert ast.dump(t1) == ast.dump(t2)


# --- Hypothesis Strategies for Construct Generation ---

safe_identifier = st.from_regex(r"[a-z][a-z0-9_]{0,8}", fullmatch=True).filter(
    lambda s: s not in (
        "def", "class", "if", "elif", "else", "while", "for", "in", "break",
        "continue", "return", "yield", "pass", "try", "except", "finally",
        "raise", "assert", "import", "from", "as", "with", "lambda", "global",
        "nonlocal", "del", "match", "case", "type", "and", "or", "not", "is",
        "True", "False", "None", "print", "len", "range",
    )
)

simple_expr = st.one_of(
    st.integers(min_value=-1000, max_value=1000).map(str),
    st.booleans().map(str),
    st.sampled_from(["None", "'hello'", '"world"']),
    safe_identifier,
)

operators = st.sampled_from(["+", "-", "*", "//", "%", "==", "!=", "<", ">", "<=", ">="])
word_operators = st.sampled_from(["and", "or"])


# --- Property Tests ---

class TestPropertySafetyAndReversibility:
    """Property tests demonstrating translation safety and reversibility."""

    @settings(max_examples=50)
    @given(
        id1=safe_identifier,
        op=operators,
        num=st.integers(min_value=1, max_value=100),
        comment=st.text(alphabet="abcdefghijklmnopqrstuvwxyz ", max_size=20),
    )
    def test_property_source_reconstruction(self, id1, op, num, comment):
        """Property 1: Source reconstruction is completely lossless."""
        snippet = f"# {comment}\n{id1} = {num} {op} 2\n"
        tokens = ParsethonTokenizer(snippet).tokenize()
        reconstructed = ParsethonTokenizer.reconstruct(tokens)
        assert reconstructed == snippet

    @settings(max_examples=40)
    @given(
        a=st.integers(min_value=1, max_value=50),
        b=st.integers(min_value=1, max_value=50),
        bool_val=st.booleans(),
    )
    def test_property_arithmetic_and_bool_roundtrip_ast(self, a, b, bool_val):
        """Property 2: Arithmetic and boolean expressions maintain round-trip AST equivalence."""
        py_code = f"x = {a} + {b} * 2\nflag = {bool_val} and not False\n"
        for tongue in ("es", "emoji", "pirate"):
            tongue_code = translate_from_python(py_code, tongue)
            roundtrip_py = translate_to_python(tongue_code, tongue)
            assert_ast_equivalent(py_code, roundtrip_py)

    @settings(max_examples=30)
    @given(
        val=st.integers(min_value=-20, max_value=20),
        threshold=st.integers(min_value=0, max_value=10),
    )
    def test_property_control_flow_execution_equivalence(self, val, threshold):
        """Property 3: Control flow (if/else) maintains execution equivalence."""
        py_code = f"""
val = {val}
threshold = {threshold}
if val > threshold:
    res = val * 2
else:
    res = val - 1
"""
        # Execute original Python
        py_globals = {}
        exec(py_code, py_globals)

        # Translate to Spanish Tongue, execute, and verify result matches exactly
        es_code = translate_from_python(py_code, "es")
        es_globals = execute(es_code, tongue="es")

        assert es_globals["res"] == py_globals["res"]

    @settings(max_examples=30)
    @given(
        items=st.lists(st.integers(min_value=1, max_value=10), min_size=1, max_size=5),
    )
    def test_property_loops_and_builtins_execution_equivalence(self, items):
        """Property 4: Loops and built-in functions maintain execution equivalence."""
        py_code = f"""
items = {items}
total = 0
for x in items:
    total += x
count = len(items)
"""
        py_globals = {}
        exec(py_code, py_globals)

        es_code = translate_from_python(py_code, "es")
        es_globals = execute(es_code, tongue="es")

        assert es_globals["total"] == py_globals["total"]
        assert es_globals["count"] == py_globals["count"]

    @settings(max_examples=25)
    @given(
        target=st.integers(min_value=0, max_value=3),
    )
    def test_property_pattern_matching_execution_equivalence(self, target):
        """Property 5: Pattern matching (match / case) maintains execution equivalence."""
        py_code = f"""
val = {target}
match val:
    case 0:
        label = "zero"
    case 1:
        label = "one"
    case 2:
        label = "two"
    case _:
        label = "many"
"""
        py_globals = {}
        exec(py_code, py_globals)

        es_code = translate_from_python(py_code, "es")
        es_globals = execute(es_code, tongue="es")

        assert es_globals["label"] == py_globals["label"]

        # Also check AST equivalence of round trip
        roundtrip_py = translate_to_python(es_code, "es")
        assert_ast_equivalent(py_code, roundtrip_py)

    @settings(max_examples=25)
    @given(
        num=st.integers(min_value=1, max_value=100),
        name=st.sampled_from(["alpha", "beta", "gamma"]),
    )
    def test_property_fstrings_and_scopes_equivalence(self, num, name):
        """Property 6: F-strings and function scopes maintain execution equivalence."""
        py_code = f"""
def compute(n, tag):
    return f"TAG: {{tag}}={{n * 2}}"

out = compute({num}, "{name}")
"""
        py_globals = {}
        exec(py_code, py_globals)

        es_code = translate_from_python(py_code, "es")
        es_globals = execute(es_code, tongue="es")

        assert es_globals["out"] == py_globals["out"]

        # AST equivalence
        roundtrip_py = translate_to_python(es_code, "es")
        assert_ast_equivalent(py_code, roundtrip_py)
