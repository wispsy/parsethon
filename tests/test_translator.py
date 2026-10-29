"""Unit tests for Parsethon bidirectional translation engine."""

import ast
import unittest

from parsethon.translator import (
    ParsethonTranslator,
    translate_from_python,
    translate_to_python,
)


class TestTranslator(unittest.TestCase):
    def test_translate_spanish_to_python(self):
        spanish_code = """
# Un programa en español
definir calcular(total, factor):
    si total > 100 y factor es no Nada:
        retornar total * factor
    sino:
        retornar 0

imprimir(calcular(200, 1.5))
"""
        py_code = translate_to_python(spanish_code, "es")
        self.assertIn("def calcular(total, factor):", py_code)
        self.assertIn("if total > 100 and factor is not None:", py_code)
        self.assertIn("return total * factor", py_code)
        self.assertIn("else:", py_code)
        self.assertIn("print(calcular(200, 1.5))", py_code)

        # Verify translated code is valid standard Python AST
        parsed = ast.parse(py_code)
        self.assertIsNotNone(parsed)

    def test_translate_emoji_to_python(self):
        emoji_code = """
🔨 sumar(a, b):
    📦 a + b

🔨 verificar(estado):
    ❓ estado == ✅:
        📦 "activo"
    ❗:
        📦 "inactivo"
"""
        py_code = translate_to_python(emoji_code, "emoji")
        self.assertIn("def sumar(a, b):", py_code)
        self.assertIn("return a + b", py_code)
        self.assertIn("def verificar(estado):", py_code)
        self.assertIn("if estado == True:", py_code)
        self.assertIn("else:", py_code)

        parsed = ast.parse(py_code)
        self.assertIsNotNone(parsed)

    def test_translate_pirate_to_python(self):
        pirate_code = """
chart plunder_loot(chest):
    perchance chest == aye:
        booty 1000
    otherwise_avast:
        booty 0
"""
        py_code = translate_to_python(pirate_code, "pirate")
        self.assertIn("def plunder_loot(chest):", py_code)
        self.assertIn("if chest == True:", py_code)
        self.assertIn("return 1000", py_code)
        self.assertIn("else:", py_code)
        self.assertIn("return 0", py_code)

        parsed = ast.parse(py_code)
        self.assertIsNotNone(parsed)

    def test_literal_and_comment_protection(self):
        code = """
# definir is a comment here, should not change
msg = "definir si sino retornar"
other = 'Verdadero o Falso'
"""
        py_code = translate_to_python(code, "es")
        # Strings and comments remain untouched
        self.assertIn('# definir is a comment here, should not change', py_code)
        self.assertIn('msg = "definir si sino retornar"', py_code)
        self.assertIn("other = 'Verdadero o Falso'", py_code)

    def test_identifier_substring_protection(self):
        code = """
si_condition = 10
silla = "chair"
es_val = 5
definir probar(silla, si_condition):
    retornar silla
"""
        py_code = translate_to_python(code, "es")
        self.assertIn("si_condition = 10", py_code)
        self.assertIn('silla = "chair"', py_code)
        self.assertIn("es_val = 5", py_code)
        self.assertIn("def probar(silla, si_condition):", py_code)
        self.assertIn("return silla", py_code)

    def test_fstring_translation(self):
        code = '''
definir saludo(nombre, activo):
    retornar f"Hola {nombre}, estado: {Verdadero si activo sino Falso:.2s} y normal"
'''
        py_code = translate_to_python(code, "es")
        self.assertIn("def saludo(nombre, activo):", py_code)
        self.assertIn('return f"Hola {nombre}, estado: {True if activo else False:.2s} y normal"', py_code)
        parsed = ast.parse(py_code)
        self.assertIsNotNone(parsed)

    def test_roundtrip_translation(self):
        py_source = """def factorial(n: int) -> int:
    if n <= 1:
        return 1
    return n * factorial(n - 1)
"""
        spanish_source = translate_from_python(py_source, "es")
        self.assertIn("definir factorial(n: int) -> int:", spanish_source)
        self.assertIn("si n <= 1:", spanish_source)
        self.assertIn("retornar 1", spanish_source)

        restored_py = translate_to_python(spanish_source, "es")
        self.assertEqual(py_source, restored_py)


if __name__ == "__main__":
    unittest.main()
