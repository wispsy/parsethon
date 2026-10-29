"""Unit tests for ParsethonTokenizer."""

import unittest
from parsethon.tokenizer import ParsethonTokenizer
from parsethon.lexicon import TokenCategory, TokenSubelement


class TestTokenizer(unittest.TestCase):
    def test_lossless_reconstruction_simple(self):
        code = "x = 42\ny = 3.14\nprint(x + y)\n"
        tokenizer = ParsethonTokenizer(code)
        tokens = tokenizer.tokenize()
        reconstructed = ParsethonTokenizer.reconstruct(tokens)
        self.assertEqual(code, reconstructed)

    def test_lossless_reconstruction_complex(self):
        code = '''# A complex python snippet
def compute(a: int, b: int = 10) -> float:
    """Docstring with 'quotes' and "double quotes"."""
    result = (a ** 2) + (b // 3)
    if result >= 100:
        return float(result)
    elif result := a * 2:
        return float(result)
    else:
        return 0.0

@decorator
class SampleClass:
    async def run(self):
        val = 0x1A + 0b1010 + 1_000_000
        msg = f"Value is: {val}"
        return msg
'''
        tokenizer = ParsethonTokenizer(code)
        tokens = tokenizer.tokenize()
        reconstructed = ParsethonTokenizer.reconstruct(tokens)
        self.assertEqual(code, reconstructed)

    def test_tokens_categories(self):
        code = "def add(x, y):\n    return x + y\n"
        tokenizer = ParsethonTokenizer(code)
        tokens = tokenizer.tokenize()

        # Filter out trivia whitespace/newline for semantic check
        significant = [
            t for t in tokens if t.category not in (TokenCategory.WHITESPACE, TokenCategory.NEWLINE)
        ]

        self.assertEqual(significant[0].value, "def")
        self.assertEqual(significant[0].category, TokenCategory.KEYWORD)
        self.assertEqual(significant[0].subelement, TokenSubelement.KW_DEFINITION)

        self.assertEqual(significant[1].value, "add")
        self.assertEqual(significant[1].category, TokenCategory.IDENTIFIER)

        self.assertEqual(significant[2].value, "(")
        self.assertEqual(significant[2].category, TokenCategory.DELIMITER)

        self.assertEqual(significant[5].value, "y")
        self.assertEqual(significant[6].value, ")")
        self.assertEqual(significant[7].value, ":")
        self.assertEqual(significant[7].category, TokenCategory.DELIMITER)

        self.assertEqual(significant[8].value, "return")
        self.assertEqual(significant[8].category, TokenCategory.KEYWORD)
        self.assertEqual(significant[8].subelement, TokenSubelement.KW_CONTROL_FLOW)

        self.assertEqual(significant[10].value, "+")
        self.assertEqual(significant[10].category, TokenCategory.OPERATOR)
        self.assertEqual(significant[10].subelement, TokenSubelement.OP_ARITHMETIC)

    def test_walrus_and_multi_char_operators(self):
        code = "if (n := len(items)) > 10:\n    pass\n"
        tokenizer = ParsethonTokenizer(code)
        tokens = tokenizer.tokenize()

        op_tokens = [t for t in tokens if t.value == ":="]
        self.assertEqual(len(op_tokens), 1)
        self.assertEqual(op_tokens[0].category, TokenCategory.OPERATOR)
        self.assertEqual(op_tokens[0].subelement, TokenSubelement.OP_ASSIGNMENT)

    def test_unicode_and_emoji_tokens(self):
        code = "definir saludar(nombre):\n    📦 f'Hola {nombre}'\n"
        tokenizer = ParsethonTokenizer(code)
        tokens = tokenizer.tokenize()
        self.assertEqual(code, ParsethonTokenizer.reconstruct(tokens))

        emoji_token = [t for t in tokens if t.value == "📦"][0]
        self.assertIsNotNone(emoji_token)

    def test_spans_accuracy(self):
        code = "a = 1\nb = 2"
        tokenizer = ParsethonTokenizer(code)
        tokens = tokenizer.tokenize()

        first_token = tokens[0]  # 'a'
        self.assertEqual(first_token.value, "a")
        self.assertEqual(first_token.span.start.line, 1)
        self.assertEqual(first_token.span.start.column, 0)
        self.assertEqual(first_token.span.end.line, 1)
        self.assertEqual(first_token.span.end.column, 1)


if __name__ == "__main__":
    unittest.main()
