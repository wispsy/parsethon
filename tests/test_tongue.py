"""Unit tests for Tongue specification and TongueRegistry."""

import json
import tempfile
import unittest
from pathlib import Path

from parsethon.tongue import (
    Tongue,
    TongueRegistry,
    TongueValidationError,
    registry,
)


class TestTongue(unittest.TestCase):
    def test_tongue_creation_and_maps(self):
        t = Tongue(
            name="test_lang",
            keywords={"def": "crear", "return": "devolver"},
            constants={"True": "Si", "False": "No"},
        )
        self.assertEqual(t.forward_map["def"], "crear")
        self.assertEqual(t.reverse_map["crear"], "def")
        self.assertEqual(t.forward_map["True"], "Si")
        self.assertEqual(t.reverse_map["Si"], "True")

    def test_tongue_validation_collision(self):
        # Two Python tokens mapping to the same Tongue token
        with self.assertRaises(TongueValidationError):
            Tongue(
                name="collision_lang",
                keywords={"def": "same", "class": "same"},
            )

    def test_tongue_empty_name(self):
        with self.assertRaises(TongueValidationError):
            Tongue(name="", keywords={"def": "make"})

    def test_tongue_serialization(self):
        t = Tongue(
            name="json_lang",
            description="A test language for serialization",
            keywords={"if": "quando", "else": "outro"},
        )
        json_str = t.to_json()
        restored = Tongue.from_json(json_str)
        self.assertEqual(restored.name, t.name)
        self.assertEqual(restored.description, t.description)
        self.assertEqual(restored.keywords, t.keywords)

        with tempfile.NamedTemporaryFile("w", delete=False) as tmp:
            tmp_path = Path(tmp.name)
        try:
            t.save(tmp_path)
            loaded = Tongue.load(tmp_path)
            self.assertEqual(loaded.name, t.name)
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    def test_tongue_registry_builtins(self):
        names = registry.list_tongues()
        self.assertIn("es", names)
        self.assertIn("emoji", names)
        self.assertIn("pirate", names)

        es = registry.get("es")
        self.assertEqual(es.reverse_map["definir"], "def")
        self.assertEqual(es.reverse_map["retornar"], "return")
        self.assertEqual(es.reverse_map["si"], "if")

        emoji = registry.get("emoji")
        self.assertEqual(emoji.reverse_map["🔨"], "def")
        self.assertEqual(emoji.reverse_map["📦"], "return")

        pirate = registry.get("pirate")
        self.assertEqual(pirate.reverse_map["chart"], "def")
        self.assertEqual(pirate.reverse_map["booty"], "return")

        self.assertIn("js", names)
        js = registry.get("js")
        self.assertTrue(js.braces)
        self.assertEqual(js.syntax_style, "braces")
        self.assertEqual(js.reverse_map["function"], "def")
        self.assertEqual(js.reverse_map["true"], "True")
        self.assertEqual(js.reverse_map["false"], "False")
        self.assertEqual(js.reverse_map["null"], "None")
        self.assertEqual(js.reverse_map["&&"], "and")
        self.assertEqual(js.reverse_map["||"], "or")
        self.assertEqual(js.reverse_map["!"], "not")
        self.assertEqual(js.reverse_map["==="], "is")

    def test_tongue_braces_configuration(self):
        t1 = Tongue(name="braced", braces=True)
        self.assertTrue(t1.braces)
        self.assertEqual(t1.syntax_style, "braces")

        t2 = Tongue(name="braced_style", syntax_style="braces")
        self.assertTrue(t2.braces)
        self.assertEqual(t2.syntax_style, "braces")

        d = t1.to_dict()
        self.assertTrue(d["braces"])
        self.assertEqual(d["syntax_style"], "braces")

        restored = Tongue.from_dict(d)
        self.assertTrue(restored.braces)

    def test_custom_registry(self):
        reg = TongueRegistry()
        custom = Tongue(name="custom", keywords={"for": "each"})
        reg.register(custom)
        self.assertIn("custom", reg.list_tongues())
        self.assertEqual(reg.get("custom").keywords["for"], "each")

        # Duplicate without overwrite
        with self.assertRaises(ValueError):
            reg.register(custom)

        # Missing tongue
        with self.assertRaises(KeyError):
            reg.get("non_existent")


if __name__ == "__main__":
    unittest.main()
