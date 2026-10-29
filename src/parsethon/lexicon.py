"""Lexical categories, subelements, and token structures for Parsethon."""

from __future__ import annotations

import builtins
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, Optional, Set, Tuple


class TokenCategory(str, Enum):
    """High-level lexical categories for Python tokens."""

    KEYWORD = "keyword"
    OPERATOR = "operator"
    DELIMITER = "delimiter"
    LITERAL = "literal"
    IDENTIFIER = "identifier"
    COMMENT = "comment"
    WHITESPACE = "whitespace"
    INDENTATION = "indentation"
    NEWLINE = "newline"
    STRING = "string"
    FSTRING = "fstring"
    SPECIAL = "special"


class TokenSubelement(str, Enum):
    """Fine-grained subelement classification of lexical tokens."""

    # Keywords
    KW_CONTROL_FLOW = "kw_control_flow"
    KW_DEFINITION = "kw_definition"
    KW_SCOPE = "kw_scope"
    KW_EXCEPTION = "kw_exception"
    KW_CONTEXT = "kw_context"
    KW_IMPORT = "kw_import"
    KW_TYPE = "kw_type"

    # Operators
    OP_ARITHMETIC = "op_arithmetic"
    OP_BITWISE = "op_bitwise"
    OP_COMPARISON = "op_comparison"
    OP_ASSIGNMENT = "op_assignment"
    OP_LOGICAL = "op_logical"

    # Delimiters
    DELIM_PAREN_OPEN = "delim_paren_open"
    DELIM_PAREN_CLOSE = "delim_paren_close"
    DELIM_BRACKET_OPEN = "delim_bracket_open"
    DELIM_BRACKET_CLOSE = "delim_bracket_close"
    DELIM_BRACE_OPEN = "delim_brace_open"
    DELIM_BRACE_CLOSE = "delim_brace_close"
    DELIM_COMMA = "delim_comma"
    DELIM_COLON = "delim_colon"
    DELIM_DOT = "delim_dot"
    DELIM_SEMICOLON = "delim_semicolon"
    DELIM_ARROW = "delim_arrow"
    DELIM_ELLIPSIS = "delim_ellipsis"

    # Literals
    LIT_BOOLEAN = "lit_boolean"
    LIT_NONE = "lit_none"
    LIT_INT = "lit_int"
    LIT_FLOAT = "lit_float"
    LIT_COMPLEX = "lit_complex"
    LIT_STRING_SINGLE = "lit_string_single"
    LIT_STRING_DOUBLE = "lit_string_double"
    LIT_STRING_TRIPLE = "lit_string_triple"
    LIT_BYTES = "lit_bytes"

    # Identifiers
    ID_STANDARD = "id_standard"
    ID_BUILTIN = "id_builtin"
    ID_MAGIC = "id_magic"

    # Trivia / Structural
    TRIVIA_WHITESPACE = "trivia_whitespace"
    TRIVIA_COMMENT = "trivia_comment"
    TRIVIA_NEWLINE = "trivia_newline"
    TRIVIA_INDENT = "trivia_indent"
    TRIVIA_DEDENT = "trivia_dedent"

    # Special / Uncategorized
    UNKNOWN = "unknown"


# Mapping Python keywords to their subelements
PYTHON_KEYWORDS: Dict[str, TokenSubelement] = {
    # Control flow
    "if": TokenSubelement.KW_CONTROL_FLOW,
    "elif": TokenSubelement.KW_CONTROL_FLOW,
    "else": TokenSubelement.KW_CONTROL_FLOW,
    "while": TokenSubelement.KW_CONTROL_FLOW,
    "for": TokenSubelement.KW_CONTROL_FLOW,
    "break": TokenSubelement.KW_CONTROL_FLOW,
    "continue": TokenSubelement.KW_CONTROL_FLOW,
    "return": TokenSubelement.KW_CONTROL_FLOW,
    "yield": TokenSubelement.KW_CONTROL_FLOW,
    "pass": TokenSubelement.KW_CONTROL_FLOW,
    "match": TokenSubelement.KW_CONTROL_FLOW,
    "case": TokenSubelement.KW_CONTROL_FLOW,
    # Definitions
    "def": TokenSubelement.KW_DEFINITION,
    "class": TokenSubelement.KW_DEFINITION,
    "lambda": TokenSubelement.KW_DEFINITION,
    "async": TokenSubelement.KW_DEFINITION,
    "await": TokenSubelement.KW_DEFINITION,
    # Scope & variable management
    "global": TokenSubelement.KW_SCOPE,
    "nonlocal": TokenSubelement.KW_SCOPE,
    "del": TokenSubelement.KW_SCOPE,
    # Exceptions
    "try": TokenSubelement.KW_EXCEPTION,
    "except": TokenSubelement.KW_EXCEPTION,
    "finally": TokenSubelement.KW_EXCEPTION,
    "raise": TokenSubelement.KW_EXCEPTION,
    "assert": TokenSubelement.KW_EXCEPTION,
    # Context
    "with": TokenSubelement.KW_CONTEXT,
    "as": TokenSubelement.KW_CONTEXT,
    # Imports
    "import": TokenSubelement.KW_IMPORT,
    "from": TokenSubelement.KW_IMPORT,
    # Type statement (Python 3.12+)
    "type": TokenSubelement.KW_TYPE,
}

# Word-based operators
PYTHON_WORD_OPERATORS: Dict[str, TokenSubelement] = {
    "and": TokenSubelement.OP_LOGICAL,
    "or": TokenSubelement.OP_LOGICAL,
    "not": TokenSubelement.OP_LOGICAL,
    "is": TokenSubelement.OP_LOGICAL,
    "in": TokenSubelement.OP_LOGICAL,
}

# Boolean and None literal constants
PYTHON_LITERAL_CONSTANTS: Dict[str, TokenSubelement] = {
    "True": TokenSubelement.LIT_BOOLEAN,
    "False": TokenSubelement.LIT_BOOLEAN,
    "None": TokenSubelement.LIT_NONE,
}

# Symbol-based operators
PYTHON_SYMBOL_OPERATORS: Dict[str, TokenSubelement] = {
    # Arithmetic
    "+": TokenSubelement.OP_ARITHMETIC,
    "-": TokenSubelement.OP_ARITHMETIC,
    "*": TokenSubelement.OP_ARITHMETIC,
    "/": TokenSubelement.OP_ARITHMETIC,
    "//": TokenSubelement.OP_ARITHMETIC,
    "%": TokenSubelement.OP_ARITHMETIC,
    "**": TokenSubelement.OP_ARITHMETIC,
    "@": TokenSubelement.OP_ARITHMETIC,
    # Bitwise
    "&": TokenSubelement.OP_BITWISE,
    "|": TokenSubelement.OP_BITWISE,
    "^": TokenSubelement.OP_BITWISE,
    "~": TokenSubelement.OP_BITWISE,
    "<<": TokenSubelement.OP_BITWISE,
    ">>": TokenSubelement.OP_BITWISE,
    # Comparison
    "==": TokenSubelement.OP_COMPARISON,
    "!=": TokenSubelement.OP_COMPARISON,
    "<": TokenSubelement.OP_COMPARISON,
    "<=": TokenSubelement.OP_COMPARISON,
    ">": TokenSubelement.OP_COMPARISON,
    ">=": TokenSubelement.OP_COMPARISON,
    # Assignment
    "=": TokenSubelement.OP_ASSIGNMENT,
    "+=": TokenSubelement.OP_ASSIGNMENT,
    "-=": TokenSubelement.OP_ASSIGNMENT,
    "*=": TokenSubelement.OP_ASSIGNMENT,
    "/=": TokenSubelement.OP_ASSIGNMENT,
    "//=": TokenSubelement.OP_ASSIGNMENT,
    "%=": TokenSubelement.OP_ASSIGNMENT,
    "@=": TokenSubelement.OP_ASSIGNMENT,
    "&=": TokenSubelement.OP_ASSIGNMENT,
    "|=": TokenSubelement.OP_ASSIGNMENT,
    "^=": TokenSubelement.OP_ASSIGNMENT,
    "<<=": TokenSubelement.OP_ASSIGNMENT,
    ">>=": TokenSubelement.OP_ASSIGNMENT,
    "**=": TokenSubelement.OP_ASSIGNMENT,
    ":=": TokenSubelement.OP_ASSIGNMENT,
}

# Delimiters and punctuation
PYTHON_DELIMITERS: Dict[str, TokenSubelement] = {
    "(": TokenSubelement.DELIM_PAREN_OPEN,
    ")": TokenSubelement.DELIM_PAREN_CLOSE,
    "[": TokenSubelement.DELIM_BRACKET_OPEN,
    "]": TokenSubelement.DELIM_BRACKET_CLOSE,
    "{": TokenSubelement.DELIM_BRACE_OPEN,
    "}": TokenSubelement.DELIM_BRACE_CLOSE,
    ",": TokenSubelement.DELIM_COMMA,
    ":": TokenSubelement.DELIM_COLON,
    ".": TokenSubelement.DELIM_DOT,
    ";": TokenSubelement.DELIM_SEMICOLON,
    "->": TokenSubelement.DELIM_ARROW,
    "...": TokenSubelement.DELIM_ELLIPSIS,
}

# Standard built-in identifiers
PYTHON_BUILTINS: Set[str] = {
    name for name in dir(builtins) if not name.startswith("_")
}


@dataclass(frozen=True)
class SourcePosition:
    """Zero-indexed or 1-indexed source code position."""

    line: int
    column: int

    def __str__(self) -> str:
        return f"{self.line}:{self.column}"


@dataclass(frozen=True)
class SourceSpan:
    """Range span in source code covering start and end positions."""

    start: SourcePosition
    end: SourcePosition

    def __str__(self) -> str:
        return f"[{self.start} - {self.end}]"


@dataclass
class LexicalToken:
    """Represents a token with fine-grained lexical classification and trivia."""

    category: TokenCategory
    subelement: TokenSubelement
    value: str
    canonical_value: str
    span: SourceSpan
    leading_trivia: str = ""
    trailing_trivia: str = ""

    @property
    def is_keyword(self) -> bool:
        return self.category == TokenCategory.KEYWORD

    @property
    def is_operator(self) -> bool:
        return self.category == TokenCategory.OPERATOR

    @property
    def is_delimiter(self) -> bool:
        return self.category == TokenCategory.DELIMITER

    @property
    def is_literal(self) -> bool:
        return self.category == TokenCategory.LITERAL

    @property
    def is_identifier(self) -> bool:
        return self.category == TokenCategory.IDENTIFIER

    @property
    def full_text(self) -> str:
        """Original text including surrounding trivia."""
        return f"{self.leading_trivia}{self.value}{self.trailing_trivia}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category.value,
            "subelement": self.subelement.value,
            "value": self.value,
            "canonical_value": self.canonical_value,
            "span": {
                "start": {"line": self.span.start.line, "column": self.span.start.column},
                "end": {"line": self.span.end.line, "column": self.span.end.column},
            },
            "leading_trivia": self.leading_trivia,
            "trailing_trivia": self.trailing_trivia,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> LexicalToken:
        span_data = data["span"]
        span = SourceSpan(
            start=SourcePosition(
                line=span_data["start"]["line"],
                column=span_data["start"]["column"],
            ),
            end=SourcePosition(
                line=span_data["end"]["line"],
                column=span_data["end"]["column"],
            ),
        )
        return cls(
            category=TokenCategory(data["category"]),
            subelement=TokenSubelement(data["subelement"]),
            value=data["value"],
            canonical_value=data["canonical_value"],
            span=span,
            leading_trivia=data.get("leading_trivia", ""),
            trailing_trivia=data.get("trailing_trivia", ""),
        )


def classify_identifier_or_keyword(text: str) -> Tuple[TokenCategory, TokenSubelement]:
    """Classifies an alphanumeric word token into its category and subelement."""
    if text in PYTHON_KEYWORDS:
        return TokenCategory.KEYWORD, PYTHON_KEYWORDS[text]
    if text in PYTHON_WORD_OPERATORS:
        return TokenCategory.OPERATOR, PYTHON_WORD_OPERATORS[text]
    if text in PYTHON_LITERAL_CONSTANTS:
        return TokenCategory.LITERAL, PYTHON_LITERAL_CONSTANTS[text]
    if text.startswith("__") and text.endswith("__") and len(text) > 4:
        return TokenCategory.IDENTIFIER, TokenSubelement.ID_MAGIC
    if text in PYTHON_BUILTINS:
        return TokenCategory.IDENTIFIER, TokenSubelement.ID_BUILTIN
    return TokenCategory.IDENTIFIER, TokenSubelement.ID_STANDARD


def classify_symbol(symbol: str) -> Tuple[TokenCategory, TokenSubelement]:
    """Classifies a symbolic token into its category and subelement."""
    if symbol in PYTHON_SYMBOL_OPERATORS:
        return TokenCategory.OPERATOR, PYTHON_SYMBOL_OPERATORS[symbol]
    if symbol in PYTHON_DELIMITERS:
        return TokenCategory.DELIMITER, PYTHON_DELIMITERS[symbol]
    return TokenCategory.SPECIAL, TokenSubelement.UNKNOWN
