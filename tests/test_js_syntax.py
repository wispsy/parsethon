"""Unit and integration tests for JavaScript-style syntax (braces, semicolons, whitespace indifference)."""

import ast
import unittest

from parsethon import execute, translate_from_python, translate_to_python
from parsethon.js_syntax import desugar_js_syntax, has_js_style_syntax, to_js_syntax


class TestJavaScriptSyntax(unittest.TestCase):
    def test_detection(self):
        self.assertTrue(has_js_style_syntax("function add(a, b) { return a + b; }"))
        self.assertTrue(has_js_style_syntax("let x = 10;"))
        self.assertTrue(has_js_style_syntax("if (x > 0) { console.log(x); }"))
        self.assertTrue(has_js_style_syntax("x === y && a || b"))
        self.assertFalse(has_js_style_syntax("def add(a, b):\n    return a + b\n"))

    def test_braces_and_semicolons_translation(self):
        js_code = """
function add(a, b) {
    if (a > 0) {
        return a + b;
    } else {
        return b;
    }
}
"""
        py_code = translate_to_python(js_code, "js")
        ast.parse(py_code)
        self.assertIn("def add(a, b):", py_code)
        self.assertIn("if(a > 0):", py_code)
        self.assertIn("return a + b", py_code)
        self.assertIn("else:", py_code)
        self.assertIn("return b", py_code)

    def test_whitespace_indifference_flat_code(self):
        flat_js = """
function factorial(n) {
if (n <= 1) {
return 1;
} else {
return n * factorial(n - 1);
}
}
"""
        py_code = translate_to_python(flat_js, "js")
        ast.parse(py_code)
        # Verify proper 4-space indentation was created
        self.assertIn("def factorial(n):", py_code)
        self.assertIn("    if(n <= 1):", py_code)
        self.assertIn("        return 1", py_code)
        self.assertIn("    else:", py_code)
        self.assertIn("        return n * factorial(n - 1)", py_code)

    def test_whitespace_indifference_single_line(self):
        single_line = "function min(a, b) { if (a < b) { return a; } return b; }"
        py_code = translate_to_python(single_line, "js")
        ast.parse(py_code)
        self.assertIn("def min(a, b):", py_code)
        self.assertIn("    if(a < b):", py_code)
        self.assertIn("        return a", py_code)
        self.assertIn("    return b", py_code)

    def test_empty_blocks(self):
        empty_code = """
function noop() {}
class MyClass {}
if (True) {}
"""
        py_code = translate_to_python(empty_code, "js")
        ast.parse(py_code)
        self.assertIn("def noop():\n    pass", py_code)
        self.assertIn("class MyClass:\n    pass", py_code)
        self.assertTrue("if(True):\n    pass" in py_code or "if True:\n    pass" in py_code)

    def test_dict_and_set_literals_distinguished_from_blocks(self):
        js_code = """
function build_config() {
    let d = { 'host': 'localhost', 'port': 8080 };
    let s = { 1, 2, 3 };
    return d;
}
"""
        py_code = translate_to_python(js_code, "js")
        ast.parse(py_code)
        self.assertIn("{'host': 'localhost', 'port': 8080}", py_code)
        self.assertIn("{1, 2, 3}", py_code)

    def test_else_if_translation(self):
        js_code = """
function grade(score) {
    if (score >= 90) {
        return 'A';
    } else if (score >= 80) {
        return 'B';
    } else {
        return 'C';
    }
}
"""
        py_code = translate_to_python(js_code, "js")
        ast.parse(py_code)
        self.assertIn("elif(score >= 80):", py_code)

    def test_loops_for_and_while(self):
        js_code = """
function sum_values(items) {
    let total = 0;
    for (let x of items) {
        total += x;
    }
    let i = 0;
    while (i < 5) {
        i += 1;
    }
    return total + i;
}
"""
        py_code = translate_to_python(js_code, "js")
        ast.parse(py_code)
        self.assertIn("for x in items:", py_code)
        self.assertIn("while(i < 5):", py_code)

    def test_try_catch_finally(self):
        js_code = """
function risky(a, b) {
    try {
        return a / b;
    } catch (err) {
        return null;
    } finally {
        let x = 1;
    }
}
"""
        py_code = translate_to_python(js_code, "js")
        ast.parse(py_code)
        self.assertIn("try:", py_code)
        self.assertIn("except Exception as err:", py_code)
        self.assertIn("finally:", py_code)

    def test_python_keywords_with_braces(self):
        mixed_code = """
def calculate(val) {
    if val > 10 {
        return val * 2;
    } else {
        return val;
    }
}
"""
        py_code = desugar_js_syntax(mixed_code)
        ast.parse(py_code)
        self.assertIn("def calculate(val):", py_code)
        self.assertIn("    if val > 10:", py_code)
        self.assertIn("        return val * 2", py_code)

    def test_operators_and_constants(self):
        js_code = """
let cond = (10 === 10 && 5 !== 3) || !false;
let val = null;
"""
        py_code = translate_to_python(js_code, "js")
        ast.parse(py_code)
        self.assertIn("==", py_code)
        self.assertIn("!=", py_code)
        self.assertIn("and", py_code)
        self.assertIn("or", py_code)
        self.assertIn("None", py_code)

    def test_runtime_execution_of_javascript_program(self):
        js_code = """
function fibonacci(n) {
    if (n <= 1) {
        return n;
    }
    return fibonacci(n - 1) + fibonacci(n - 2);
}

let result = fibonacci(8);
let is_valid = true && (result === 21);
console.log("Fib 8:", result);
"""
        scope = execute(js_code, tongue="js")
        self.assertEqual(scope["result"], 21)
        self.assertTrue(scope["is_valid"])

    def test_roundtrip_python_to_js_and_back(self):
        py_code = """def multiply(a, b):
    if a == 0:
        return 0
    elif b == 0:
        return 0
    else:
        return a * b
"""
        js_code = translate_from_python(py_code, "js")
        self.assertIn("function multiply(a, b) {", js_code)
        self.assertIn("return 0;", js_code)
        self.assertIn("}", js_code)

        roundtrip_py = translate_to_python(js_code, "js")
        tree1 = ast.parse(py_code)
        tree2 = ast.parse(roundtrip_py)
        self.assertEqual(len(tree1.body), len(tree2.body))


if __name__ == "__main__":
    unittest.main()
