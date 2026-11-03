"""Unit tests for SourceMap bidirectional coordinate remapping."""

import unittest
from parsethon.sourcemap import SourceMap, SourceMapEntry
from parsethon.lexicon import SourcePosition, SourceSpan
from parsethon.translator import ParsethonTranslator


class TestSourceMap(unittest.TestCase):
    def test_sourcemap_creation_and_serialization(self):
        sm = SourceMap()
        sm.add_entry(
            original_span=SourceSpan(SourcePosition(1, 0), SourcePosition(1, 7)),
            translated_span=SourceSpan(SourcePosition(1, 0), SourcePosition(1, 3)),
            original_text="definir",
            translated_text="def",
        )
        self.assertEqual(len(sm.entries), 1)

        d = sm.to_dict()
        sm2 = SourceMap.from_dict(d)
        self.assertEqual(len(sm2.entries), 1)
        self.assertEqual(sm2.entries[0].original_text, "definir")
        self.assertEqual(sm2.entries[0].translated_text, "def")

    def test_sourcemap_coordinate_lookups(self):
        translator = ParsethonTranslator("es")
        code = "definir saludar(nombre):\n    imprimir(nombre)\n"
        py_code, sm = translator.translate_with_sourcemap(code, is_to_python=True)

        self.assertIn("def saludar(nombre):", py_code)
        self.assertIn("print(nombre)", py_code)

        # Lookup translated "def" (1, 0) -> original "definir" (1, 0)
        orig_pos = sm.lookup_original(line=1, column=0)
        self.assertIsNotNone(orig_pos)
        self.assertEqual(orig_pos.line, 1)
        self.assertEqual(orig_pos.column, 0)

        # Lookup translated "print" on line 2
        orig_print = sm.lookup_original(line=2, column=4)
        self.assertIsNotNone(orig_print)
        self.assertEqual(orig_print.line, 2)
        # In original, 'imprimir' was at column 4
        self.assertEqual(orig_print.column, 4)

        # Reverse lookup: original (2, 4) -> translated (2, 4)
        trans_pos = sm.lookup_translated(line=2, column=4)
        self.assertIsNotNone(trans_pos)
        self.assertEqual(trans_pos.line, 2)
        self.assertEqual(trans_pos.column, 4)


if __name__ == "__main__":
    unittest.main()
