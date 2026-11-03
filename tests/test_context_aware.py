"""Tests for context-aware identifier translation and soft keywords (match, case)."""

import unittest
from parsethon.translator import translate_to_python, translate_from_python
from parsethon.runtime import execute


class TestContextAwareTranslation(unittest.TestCase):
    def test_soft_keywords_match_case_statements(self):
        py_code = """match x:
    case 1:
        print("one")
    case _:
        print("other")
"""
        es_code = translate_from_python(py_code, "es")
        self.assertIn("coincidir x:", es_code)
        self.assertIn("caso 1:", es_code)
        self.assertIn("caso _:", es_code)
        self.assertIn("imprimir(", es_code)

        # Round trip to python
        roundtrip_py = translate_to_python(es_code, "es")
        self.assertEqual(roundtrip_py, py_code)

    def test_soft_keywords_as_user_variables_not_renamed(self):
        py_code = """match = 5
case = 10
total = match + case
"""
        es_code = translate_from_python(py_code, "es")
        # match and case as variable names should NOT be translated to coincidir and caso
        self.assertIn("match = 5", es_code)
        self.assertIn("case = 10", es_code)
        self.assertIn("match + case", es_code)

        roundtrip = translate_to_python(es_code, "es")
        self.assertEqual(roundtrip, py_code)

    def test_attributes_not_transformed(self):
        py_code = """obj.match = 1
obj.case = 2
obj.print = 3
obj.len = 4
result = obj.print()
"""
        es_code = translate_from_python(py_code, "es")
        # Attributes following '.' must never be translated
        self.assertIn("obj.match = 1", es_code)
        self.assertIn("obj.case = 2", es_code)
        self.assertIn("obj.print = 3", es_code)
        self.assertIn("obj.len = 4", es_code)
        self.assertIn("result = obj.print()", es_code)

        roundtrip = translate_to_python(es_code, "es")
        self.assertEqual(roundtrip, py_code)

    def test_function_and_arg_definitions_not_transformed(self):
        py_code = """def match(case):
    return case
"""
        es_code = translate_from_python(py_code, "es")
        self.assertIn("definir match(case):", es_code)
        self.assertIn("retornar case", es_code)

        roundtrip = translate_to_python(es_code, "es")
        self.assertEqual(roundtrip, py_code)

    def test_keyword_arguments_in_calls(self):
        py_code = "result = func(match=True, case=123, print=False)\n"
        es_code = translate_from_python(py_code, "es")
        self.assertIn("match=Verdadero", es_code)
        self.assertIn("case=123", es_code)
        self.assertIn("print=Falso", es_code)

        roundtrip = translate_to_python(es_code, "es")
        self.assertEqual(roundtrip, py_code)

    def test_import_symbols_preserved(self):
        py_code = "from my_module import match, case, print\n"
        es_code = translate_from_python(py_code, "es")
        self.assertIn("desde my_module importar match, case, print", es_code)

        roundtrip = translate_to_python(es_code, "es")
        self.assertEqual(roundtrip, py_code)

    def test_runtime_execution_with_soft_keywords_and_variables(self):
        tongue_code = """
definir evaluar(valor):
    match = valor
    coincidir match:
        caso 1:
            retornar "uno"
        caso 2:
            retornar "dos"
        caso _:
            retornar "otro"

res1 = evaluar(1)
res2 = evaluar(2)
res3 = evaluar(99)
"""
        scope = execute(tongue_code, tongue="es")
        self.assertEqual(scope["res1"], "uno")
        self.assertEqual(scope["res2"], "dos")
        self.assertEqual(scope["res3"], "otro")


if __name__ == "__main__":
    unittest.main()
