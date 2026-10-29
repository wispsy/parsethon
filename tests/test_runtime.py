"""Unit tests for Parsethon CPython runtime and traceback mapping."""

import tempfile
import unittest
from pathlib import Path

from parsethon.runtime import (
    ParsethonRuntime,
    TongueExecutionError,
    detect_tongue_from_filename,
    detect_tongue_from_source,
    execute,
    execute_file,
)


class TestRuntime(unittest.TestCase):
    def test_execute_spanish(self):
        code = """
definir multiplicar(a, b):
    retornar a * b

resultado = multiplicar(6, 7)
"""
        scope = execute(code, tongue="es")
        self.assertEqual(scope["resultado"], 42)

    def test_execute_emoji(self):
        code = """
🔨 contar(limite):
    total = 0
    🔁 num 📥 [1, 2, 3]:
        total += num
    📦 total

final = contar(10)
"""
        scope = execute(code, tongue="emoji")
        self.assertEqual(scope["final"], 6)

    def test_tongue_header_detection(self):
        src1 = "# tongue: es\ndefinir f(): retornar 99\nx = f()\n"
        self.assertEqual(detect_tongue_from_source(src1), "es")
        scope1 = execute(src1)
        self.assertEqual(scope1["x"], 99)

        src2 = "# coding: parsethon-emoji\n🔨 f(): 📦 100\nx = f()\n"
        self.assertEqual(detect_tongue_from_source(src2), "emoji")
        scope2 = execute(src2)
        self.assertEqual(scope2["x"], 100)

    def test_tongue_filename_detection(self):
        self.assertEqual(detect_tongue_from_filename("app.es.py"), "es")
        self.assertEqual(detect_tongue_from_filename("service.emoji.py"), "emoji")
        self.assertEqual(detect_tongue_from_filename("simple.py"), None)

    def test_execute_file(self):
        with tempfile.NamedTemporaryFile("w", suffix=".es.py", delete=False) as tmp:
            tmp.write("definir calc(): retornar 123\nres = calc()\n")
            tmp_path = Path(tmp.name)
        try:
            scope = execute_file(tmp_path)
            self.assertEqual(scope["res"], 123)
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    def test_runtime_error_mapping(self):
        code = """# Line 1
definir dividir(a, b):
    retornar a / b

dividir(10, 0)
"""
        with self.assertRaises(TongueExecutionError) as ctx:
            execute(code, tongue="es")

        err = ctx.exception
        self.assertIn("ZeroDivisionError", err.message)
        self.assertEqual(err.lineno, 3)
        self.assertIn("retornar a / b", err.tongue_line)

    def test_syntax_error_mapping(self):
        code = """
definir foo()
    retornar 1
"""
        with self.assertRaises(TongueExecutionError) as ctx:
            execute(code, tongue="es")

        err = ctx.exception
        self.assertIn("SyntaxError", err.message)
        self.assertEqual(err.lineno, 2)
        self.assertIn("definir foo()", err.tongue_line)


if __name__ == "__main__":
    unittest.main()
