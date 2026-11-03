"""Tests for stateful string scanner and Python 3.12+ f-string grammar support."""

import unittest
from parsethon.tokenizer import ParsethonTokenizer, scan_string_literal
from parsethon.lexicon import TokenCategory
from parsethon.translator import translate_to_python, translate_from_python


class TestStatefulStringsAndFstrings(unittest.TestCase):
    def test_string_escape_sequences(self):
        # Single quote with escaped quote
        s1 = r"'hello \' world'"
        res1 = scan_string_literal(s1)
        self.assertIsNotNone(res1)
        self.assertEqual(res1[0], s1)

        # Double quote with escaped quote
        s2 = r'"hello \" world"'
        res2 = scan_string_literal(s2)
        self.assertIsNotNone(res2)
        self.assertEqual(res2[0], s2)

        # Triple quote with internal escaped quote
        s3 = r'"""hello \""" world"""'
        res3 = scan_string_literal(s3)
        self.assertIsNotNone(res3)
        self.assertEqual(res3[0], s3)

        # Even backslashes before closing quote: \\ means backslash is escaped, quote closes string
        s4 = r'"hello \\"'
        res4 = scan_string_literal(s4)
        self.assertIsNotNone(res4)
        self.assertEqual(res4[0], s4)

    def test_tokenizer_handles_escaped_strings_cleanly(self):
        source = r'''
x = "escaped \" double"
y = 'escaped \' single'
z = """multiline \""" with quote"""
w = r"raw \" string"
'''
        tokens = ParsethonTokenizer(source).tokenize()
        str_tokens = [t for t in tokens if t.category == TokenCategory.STRING]
        self.assertEqual(len(str_tokens), 4)
        # Lossless round-trip
        self.assertEqual(ParsethonTokenizer.reconstruct(tokens), source)

    def test_python312_fstring_with_matching_inner_quotes(self):
        # Python 3.12+ allows quotes matching outer delimiter inside expressions
        source = 'f"{d[\"key\"]}"'
        tokens = ParsethonTokenizer(source).tokenize()
        fstrings = [t for t in tokens if t.category == TokenCategory.FSTRING]
        self.assertEqual(len(fstrings), 1)
        self.assertEqual(fstrings[0].value, source)

    def test_python312_nested_fstrings(self):
        source = 'f"outer {f"inner {x}"} end"'
        tokens = ParsethonTokenizer(source).tokenize()
        fstrings = [t for t in tokens if t.category == TokenCategory.FSTRING]
        self.assertEqual(len(fstrings), 1)
        self.assertEqual(fstrings[0].value, source)

    def test_fstring_translation_with_nested_expressions(self):
        # Translate Spanish tongue expressions inside complex f-strings
        tongue_code = 'f"Total: {longitud(items):{ancho}}"'
        py_code = translate_to_python(tongue_code, "es")
        self.assertEqual(py_code, 'f"Total: {len(items):{ancho}}"')

        # Translate with nested f-string
        nested_tongue = 'f"A {f"B {imprimir(1)}"} C"'
        nested_py = translate_to_python(nested_tongue, "es")
        self.assertEqual(nested_py, 'f"A {f"B {print(1)}"} C"')

    def test_fstring_conversions_and_formats(self):
        tongue_code = 'f"{imprimir(x)!r:10}"'
        py_code = translate_to_python(tongue_code, "es")
        self.assertEqual(py_code, 'f"{print(x)!r:10}"')


if __name__ == "__main__":
    unittest.main()
