"""Unit tests for Parsethon import hooks and codec registration."""

import codecs
import importlib
import sys
import tempfile
import unittest
from pathlib import Path

from parsethon.importer import (
    disable,
    enable,
    install_codec,
    install_importer,
    search_tongue_codec,
    uninstall_codec,
    uninstall_importer,
)


class TestImporter(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.dir_path = Path(self.temp_dir.name)
        sys.path.insert(0, str(self.dir_path))
        enable()

    def tearDown(self):
        disable()
        if str(self.dir_path) in sys.path:
            sys.path.remove(str(self.dir_path))
        self.temp_dir.cleanup()

    def test_import_spanish_module(self):
        mod_file = self.dir_path / "operaciones.es.py"
        mod_file.write_text(
            """
definir sumar(a, b):
    retornar a + b

definir es_positivo(n):
    si n > 0:
        retornar Verdadero
    sino:
        retornar Falso
""",
            encoding="utf-8",
        )

        # Import dynamically as 'operaciones'
        mod = importlib.import_module("operaciones")
        self.assertIsNotNone(mod)
        self.assertEqual(mod.sumar(15, 27), 42)
        self.assertTrue(mod.es_positivo(10))
        self.assertFalse(mod.es_positivo(-5))

        # Cleanup sys.modules
        if "operaciones" in sys.modules:
            del sys.modules["operaciones"]

    def test_import_emoji_module(self):
        mod_file = self.dir_path / "emojimod.emoji.py"
        mod_file.write_text(
            """
🔨 multiplicar(x, y):
    📦 x * y
""",
            encoding="utf-8",
        )

        mod = importlib.import_module("emojimod")
        self.assertIsNotNone(mod)
        self.assertEqual(mod.multiplicar(6, 9), 54)

        if "emojimod" in sys.modules:
            del sys.modules["emojimod"]

    def test_import_js_module(self):
        mod_file = self.dir_path / "mathops.js"
        mod_file.write_text(
            """
function square(n) {
    return n * n;
}

function isEven(n) {
    if (n % 2 === 0) {
        return true;
    } else {
        return false;
    }
}
""",
            encoding="utf-8",
        )

        mod = importlib.import_module("mathops")
        self.assertIsNotNone(mod)
        self.assertEqual(mod.square(8), 64)
        self.assertTrue(mod.isEven(4))
        self.assertFalse(mod.isEven(5))

        if "mathops" in sys.modules:
            del sys.modules["mathops"]

    def test_import_js_py_module(self):
        mod_file = self.dir_path / "helper.js.py"
        mod_file.write_text(
            """
function greet(name) {
    return "Hello, " + name;
}
""",
            encoding="utf-8",
        )

        mod = importlib.import_module("helper")
        self.assertIsNotNone(mod)
        self.assertEqual(mod.greet("Parsethon"), "Hello, Parsethon")

        if "helper" in sys.modules:
            del sys.modules["helper"]

    def test_codec_lookup(self):
        install_codec()
        info = codecs.lookup("parsethon-es")
        self.assertIsNotNone(info)

        raw_es = b"definir foo(): retornar 123"
        decoded, length = info.decode(raw_es)
        self.assertIn("def foo():", decoded)
        self.assertIn("return 123", decoded)

    def test_codec_uninstall(self):
        install_codec()
        info = codecs.lookup("parsethon-es")
        self.assertIsNotNone(info)

        uninstall_codec()
        with self.assertRaises(LookupError):
            codecs.lookup("parsethon-es")


if __name__ == "__main__":
    unittest.main()
