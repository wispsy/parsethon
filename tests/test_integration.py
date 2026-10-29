"""End-to-end integration tests and complex Python constructs across Tongues."""

import ast
import asyncio
import tempfile
import unittest
from pathlib import Path

from parsethon.runtime import execute, execute_file
from parsethon.translator import translate_from_python, translate_to_python


class TestIntegration(unittest.TestCase):
    def test_examples_run(self):
        examples_dir = Path(__file__).parent.parent / "examples"

        # 1. Fibonacci in Spanish
        fib_path = examples_dir / "fibonacci.es.py"
        self.assertTrue(fib_path.exists())
        scope_fib = execute_file(fib_path)
        self.assertEqual(scope_fib["estado"], "Completado")

        # 2. Counter in Emoji
        emoji_path = examples_dir / "counter.emoji.py"
        self.assertTrue(emoji_path.exists())
        scope_emoji = execute_file(emoji_path)
        self.assertEqual(scope_emoji["nuevo_valor"], 14)
        self.assertEqual(scope_emoji["par"], True)

        # 3. Treasure in Pirate
        pirate_path = examples_dir / "treasure.pirate.py"
        self.assertTrue(pirate_path.exists())
        scope_pirate = execute_file(pirate_path)
        self.assertEqual(scope_pirate["success"], True)
        self.assertEqual(scope_pirate["chest"].gold, 350)

    def test_oop_inheritance_and_polymorphism(self):
        code = """
clase Animal:
    definir __init__(este, nombre):
        este.nombre = nombre
    definir hablar(este):
        retornar "..."

clase Perro(Animal):
    definir hablar(este):
        retornar f"{este.nombre} dice guau"

p = Perro("Firulais")
res = p.hablar()
"""
        scope = execute(code, tongue="es")
        self.assertEqual(scope["res"], "Firulais dice guau")

    def test_list_and_dict_comprehensions(self):
        code = """
numeros = [1, 2, 3, 4, 5, 6]
pares_cuadrados = [x ** 2 para x en numeros si x % 2 == 0]
mapa = {f"k_{x}": x para x en pares_cuadrados}
"""
        scope = execute(code, tongue="es")
        self.assertEqual(scope["pares_cuadrados"], [4, 16, 36])
        self.assertEqual(scope["mapa"]["k_4"], 4)
        self.assertEqual(scope["mapa"]["k_16"], 16)

    def test_exception_handling_flow(self):
        code = """
estado = "inicio"
intentar:
    lanzar ValueError("error de prueba")
excepto ValueError como err:
    estado = f"capturado: {err}"
finalmente:
    limpieza = Verdadero
"""
        scope = execute(code, tongue="es")
        self.assertEqual(scope["estado"], "capturado: error de prueba")
        self.assertTrue(scope["limpieza"])

    def test_pattern_matching(self):
        code = """
definir describir(val):
    coincidir val:
        caso 1:
            retornar "uno"
        caso [a, b]:
            retornar f"par: {a}, {b}"
        caso _:
            retornar "otro"

r1 = describir(1)
r2 = describir([10, 20])
r3 = describir("prueba")
"""
        scope = execute(code, tongue="es")
        self.assertEqual(scope["r1"], "uno")
        self.assertEqual(scope["r2"], "par: 10, 20")
        self.assertEqual(scope["r3"], "otro")

    def test_ast_equivalence_roundtrip(self):
        py_code = """
def sample_pipeline(data: list[int]) -> dict[str, int]:
    result = {}
    for item in data:
        if item > 10 and item % 2 == 0:
            result[str(item)] = item * 2
        else:
            continue
    return result
"""
        tongue_code = translate_from_python(py_code, "es")
        restored_py = translate_to_python(tongue_code, "es")

        # Ast parse both and compare AST dump
        ast_orig = ast.dump(ast.parse(py_code))
        ast_restored = ast.dump(ast.parse(restored_py))
        self.assertEqual(ast_orig, ast_restored)


if __name__ == "__main__":
    unittest.main()
