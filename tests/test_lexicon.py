"""Unit tests for Parsethon lexical definitions and token classification."""

import unittest
from parsethon.lexicon import (
    LexicalToken,
    SourcePosition,
    SourceSpan,
    TokenCategory,
    TokenSubelement,
    classify_identifier_or_keyword,
    classify_symbol,
)


class TestLexicon(unittest.TestCase):
    def test_keywords_classification(self):
        cat, sub = classify_identifier_or_keyword("def")
        self.assertEqual(cat, TokenCategory.KEYWORD)
        self.assertEqual(sub, TokenSubelement.KW_DEFINITION)

        cat, sub = classify_identifier_or_keyword("if")
        self.assertEqual(cat, TokenCategory.KEYWORD)
        self.assertEqual(sub, TokenSubelement.KW_CONTROL_FLOW)

        cat, sub = classify_identifier_or_keyword("try")
        self.assertEqual(cat, TokenCategory.KEYWORD)
        self.assertEqual(sub, TokenSubelement.KW_EXCEPTION)

        cat, sub = classify_identifier_or_keyword("global")
        self.assertEqual(cat, TokenCategory.KEYWORD)
        self.assertEqual(sub, TokenSubelement.KW_SCOPE)

    def test_word_operators_classification(self):
        cat, sub = classify_identifier_or_keyword("and")
        self.assertEqual(cat, TokenCategory.OPERATOR)
        self.assertEqual(sub, TokenSubelement.OP_LOGICAL)

        cat, sub = classify_identifier_or_keyword("is")
        self.assertEqual(cat, TokenCategory.OPERATOR)
        self.assertEqual(sub, TokenSubelement.OP_LOGICAL)

    def test_literals_constants_classification(self):
        cat, sub = classify_identifier_or_keyword("True")
        self.assertEqual(cat, TokenCategory.LITERAL)
        self.assertEqual(sub, TokenSubelement.LIT_BOOLEAN)

        cat, sub = classify_identifier_or_keyword("None")
        self.assertEqual(cat, TokenCategory.LITERAL)
        self.assertEqual(sub, TokenSubelement.LIT_NONE)

    def test_identifiers_classification(self):
        cat, sub = classify_identifier_or_keyword("print")
        self.assertEqual(cat, TokenCategory.IDENTIFIER)
        self.assertEqual(sub, TokenSubelement.ID_BUILTIN)

        cat, sub = classify_identifier_or_keyword("__init__")
        self.assertEqual(cat, TokenCategory.IDENTIFIER)
        self.assertEqual(sub, TokenSubelement.ID_MAGIC)

        cat, sub = classify_identifier_or_keyword("my_var")
        self.assertEqual(cat, TokenCategory.IDENTIFIER)
        self.assertEqual(sub, TokenSubelement.ID_STANDARD)

    def test_symbols_classification(self):
        cat, sub = classify_symbol("+")
        self.assertEqual(cat, TokenCategory.OPERATOR)
        self.assertEqual(sub, TokenSubelement.OP_ARITHMETIC)

        cat, sub = classify_symbol("==")
        self.assertEqual(cat, TokenCategory.OPERATOR)
        self.assertEqual(sub, TokenSubelement.OP_COMPARISON)

        cat, sub = classify_symbol(":=")
        self.assertEqual(cat, TokenCategory.OPERATOR)
        self.assertEqual(sub, TokenSubelement.OP_ASSIGNMENT)

        cat, sub = classify_symbol("(")
        self.assertEqual(cat, TokenCategory.DELIMITER)
        self.assertEqual(sub, TokenSubelement.DELIM_PAREN_OPEN)

        cat, sub = classify_symbol("->")
        self.assertEqual(cat, TokenCategory.DELIMITER)
        self.assertEqual(sub, TokenSubelement.DELIM_ARROW)

    def test_lexical_token_serialization(self):
        span = SourceSpan(SourcePosition(1, 0), SourcePosition(1, 3))
        tok = LexicalToken(
            category=TokenCategory.KEYWORD,
            subelement=TokenSubelement.KW_DEFINITION,
            value="def",
            canonical_value="def",
            span=span,
            leading_trivia="    ",
            trailing_trivia=" ",
        )
        self.assertTrue(tok.is_keyword)
        self.assertEqual(tok.full_text, "    def ")

        d = tok.to_dict()
        restored = LexicalToken.from_dict(d)
        self.assertEqual(tok.category, restored.category)
        self.assertEqual(tok.subelement, restored.subelement)
        self.assertEqual(tok.value, restored.value)
        self.assertEqual(tok.span.start.line, restored.span.start.line)
        self.assertEqual(tok.leading_trivia, restored.leading_trivia)


if __name__ == "__main__":
    unittest.main()
