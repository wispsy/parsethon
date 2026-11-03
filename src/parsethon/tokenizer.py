"""Lossless lexical tokenizer for Python and Tongue syntax."""

from __future__ import annotations

import re
from typing import Iterator, List, Optional, Tuple

from parsethon.lexicon import (
    PYTHON_DELIMITERS,
    PYTHON_KEYWORDS,
    PYTHON_LITERAL_CONSTANTS,
    PYTHON_SYMBOL_OPERATORS,
    PYTHON_WORD_OPERATORS,
    LexicalToken,
    SourcePosition,
    SourceSpan,
    TokenCategory,
    TokenSubelement,
    classify_identifier_or_keyword,
    classify_symbol,
)

def get_multi_char_symbols() -> List[str]:
    """Return all standard Python and registered Tongue multi-char symbols, sorted descending by length."""
    syms = set(PYTHON_SYMBOL_OPERATORS.keys()) | set(PYTHON_DELIMITERS.keys())
    try:
        from parsethon.tongue import registry
        for t_name in registry.list_tongues():
            tongue = registry.get(t_name)
            for d in (tongue.operators, tongue.delimiters):
                for val in d.values():
                    if val and not val.isidentifier():
                        syms.add(val)
    except Exception:
        pass
    return sorted(syms, key=lambda s: len(s), reverse=True)


# Multi-character symbols ordered by length descending to match greedily
MULTI_CHAR_SYMBOLS = get_multi_char_symbols()

# Regular expressions for lexical elements
RE_WHITESPACE = re.compile(r"[ \t\f]+")
RE_NEWLINE = re.compile(r"\r\n|\r|\n")
RE_COMMENT = re.compile(r"#[^\r\n]*")

# String literal prefixes
RE_STRING_PREFIX = re.compile(r"^(r[bf]|b[r]|f[r]|r|u|b|f)?", re.IGNORECASE)


def scan_string_literal(source: str, start_index: int = 0) -> Optional[Tuple[str, bool, bool]]:
    """Scan a string literal statefully, handling escape sequences and Python 3.12+ nested f-strings.

    Returns (string_token, is_fstring, is_triple) or None if no string literal starts at start_index.
    """
    m = RE_STRING_PREFIX.match(source[start_index:])
    if not m:
        return None
    prefix = m.group(0)
    p = start_index + len(prefix)
    if p >= len(source):
        return None

    if source[p : p + 3] in ('"""', "'''"):
        quote_delim = source[p : p + 3]
        p += 3
        is_triple = True
    elif source[p] in ('"', "'"):
        quote_delim = source[p]
        p += 1
        is_triple = False
    else:
        return None

    is_fstring = "f" in prefix.lower()

    if not is_fstring:
        while p < len(source):
            if source[p] == "\\":
                p += 2
                continue
            if is_triple:
                if source[p : p + 3] == quote_delim:
                    return source[start_index : p + 3], is_fstring, is_triple
                p += 1
            else:
                if source[p] in ("\r", "\n"):
                    break
                if source[p] == quote_delim:
                    return source[start_index : p + 1], is_fstring, is_triple
                p += 1
        return None

    # Stateful f-string scanning (Python 3.12+ PEP 701 support)
    brace_depth = 0
    while p < len(source):
        if brace_depth == 0:
            if source[p : p + 2] in ("{{", "}}"):
                p += 2
                continue
            if source[p] == "{":
                brace_depth += 1
                p += 1
                continue
            if is_triple:
                if source[p : p + 3] == quote_delim:
                    return source[start_index : p + 3], is_fstring, is_triple
                if source[p] == "\\":
                    p += 2
                    continue
                p += 1
            else:
                if source[p] in ("\r", "\n"):
                    break
                if source[p] == quote_delim:
                    return source[start_index : p + 1], is_fstring, is_triple
                if source[p] == "\\":
                    p += 2
                    continue
                p += 1
        else:
            # Inside expression within f-string
            inner_str = scan_string_literal(source, p)
            if inner_str is not None:
                p += len(inner_str[0])
                continue
            if source[p] == "{":
                brace_depth += 1
                p += 1
            elif source[p] == "}":
                brace_depth -= 1
                p += 1
            elif source[p] == "#":
                while p < len(source) and source[p] not in ("\r", "\n"):
                    p += 1
            elif source[p] == "\\":
                p += 2
            else:
                p += 1

    return None

# Number patterns
RE_HEX_INT = re.compile(r"^0[xX][0-9a-fA-F_]+[jJ]?")
RE_BIN_INT = re.compile(r"^0[bB][01_]+[jJ]?")
RE_OCT_INT = re.compile(r"^0[oO][0-7_]+[jJ]?")
RE_FLOAT_SCI = re.compile(r"^\d[0-9_]*(\.[0-9_]*)?[eE][+-]?[0-9_]+[jJ]?")
RE_FLOAT_DOT = re.compile(r"^(\d[0-9_]*\.[0-9_]*|\.[0-9_]+)([eE][+-]?[0-9_]+)?[jJ]?")
RE_DECIMAL_INT = re.compile(r"^\d[0-9_]*[jJ]?")

# Identifiers (standard ASCII identifier or Unicode word)
RE_IDENTIFIER = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*")
# Non-ASCII word / unicode identifier
RE_UNICODE_WORD = re.compile(r"^\w+", re.UNICODE)

# Unicode emoji or multi-codepoint symbol with variation selectors / ZWJ
RE_EMOJI_OR_SYMBOL = re.compile(
    r"^[^\s\w\(\)\[\]\{\}\,\:\;\.\+\-\*\/\%\&\|\^\~\<\>\=\@](?:[\ufe00-\ufe0f]|[\U0001f3fb-\U0001f3ff]|(?:\u200d[^\s\w\(\)\[\]\{\}\,\:\;\.\+\-\*\/\%\&\|\^\~\<\>\=\@](?:[\ufe00-\ufe0f]|[\U0001f3fb-\U0001f3ff])?))*"
)


class ParsethonTokenizer:
    """Tokenizer capable of lossless parsing of Python and custom Tongue source code."""

    def __init__(self, source: str) -> None:
        self.source = source
        self.length = len(source)
        self.index = 0
        self.line = 1
        self.column = 0
        self.symbols = get_multi_char_symbols()

    def _advance(self, text: str) -> SourceSpan:
        """Advance cursor by text length and line breaks, returning source span."""
        start = SourcePosition(self.line, self.column)
        lines = text.splitlines(keepends=True)
        if len(lines) == 1 and not (lines[0].endswith("\n") or lines[0].endswith("\r")):
            self.column += len(text)
        else:
            for l in lines:
                if l.endswith("\n") or l.endswith("\r"):
                    self.line += 1
                    self.column = 0
                else:
                    self.column += len(l)
        end = SourcePosition(self.line, self.column)
        self.index += len(text)
        return SourceSpan(start, end)

    def tokenize(self) -> List[LexicalToken]:
        """Tokenize entire source text into a list of LexicalTokens."""
        tokens: List[LexicalToken] = []
        while self.index < self.length:
            token = self._next_token()
            tokens.append(token)
        return tokens

    def _next_token(self) -> LexicalToken:
        current_slice = self.source[self.index :]

        # 1. Whitespace (spaces and tabs)
        m_ws = RE_WHITESPACE.match(current_slice)
        if m_ws:
            text = m_ws.group(0)
            span = self._advance(text)
            return LexicalToken(
                category=TokenCategory.WHITESPACE,
                subelement=TokenSubelement.TRIVIA_WHITESPACE,
                value=text,
                canonical_value=text,
                span=span,
            )

        # 2. Newline
        m_nl = RE_NEWLINE.match(current_slice)
        if m_nl:
            text = m_nl.group(0)
            span = self._advance(text)
            return LexicalToken(
                category=TokenCategory.NEWLINE,
                subelement=TokenSubelement.TRIVIA_NEWLINE,
                value=text,
                canonical_value=text,
                span=span,
            )

        # 3. Comment
        m_comment = RE_COMMENT.match(current_slice)
        if m_comment:
            text = m_comment.group(0)
            span = self._advance(text)
            return LexicalToken(
                category=TokenCategory.COMMENT,
                subelement=TokenSubelement.TRIVIA_COMMENT,
                value=text,
                canonical_value=text,
                span=span,
            )

        # 4. Strings and F-Strings (stateful scanner)
        str_res = scan_string_literal(self.source, self.index)
        if str_res is not None:
            text, is_fstring, is_triple = str_res
            span = self._advance(text)
            category = TokenCategory.FSTRING if is_fstring else TokenCategory.STRING
            if is_triple:
                sub_kind = TokenSubelement.LIT_STRING_TRIPLE
            elif '"' in text[:4]:
                sub_kind = TokenSubelement.LIT_STRING_DOUBLE
            else:
                sub_kind = TokenSubelement.LIT_STRING_SINGLE
            return LexicalToken(
                category=category,
                subelement=sub_kind,
                value=text,
                canonical_value=text,
                span=span,
            )

        # 5. Numbers
        for pattern, sub_kind in (
            (RE_HEX_INT, TokenSubelement.LIT_INT),
            (RE_BIN_INT, TokenSubelement.LIT_INT),
            (RE_OCT_INT, TokenSubelement.LIT_INT),
            (RE_FLOAT_SCI, TokenSubelement.LIT_FLOAT),
            (RE_FLOAT_DOT, TokenSubelement.LIT_FLOAT),
            (RE_DECIMAL_INT, TokenSubelement.LIT_INT),
        ):
            m_num = pattern.match(current_slice)
            if m_num:
                text = m_num.group(0)
                span = self._advance(text)
                if text.endswith(("j", "J")):
                    sub_kind = TokenSubelement.LIT_COMPLEX
                return LexicalToken(
                    category=TokenCategory.LITERAL,
                    subelement=sub_kind,
                    value=text,
                    canonical_value=text,
                    span=span,
                )

        # 6. Multi-character and known symbol operators/delimiters
        for sym in self.symbols:
            if current_slice.startswith(sym):
                span = self._advance(sym)
                cat, sub = classify_symbol(sym)
                return LexicalToken(
                    category=cat,
                    subelement=sub,
                    value=sym,
                    canonical_value=sym,
                    span=span,
                )

        # 7. Identifiers, keywords, or Unicode words
        m_ident = RE_IDENTIFIER.match(current_slice)
        if m_ident:
            text = m_ident.group(0)
            span = self._advance(text)
            cat, sub = classify_identifier_or_keyword(text)
            return LexicalToken(
                category=cat,
                subelement=sub,
                value=text,
                canonical_value=text,
                span=span,
            )

        m_uword = RE_UNICODE_WORD.match(current_slice)
        if m_uword:
            text = m_uword.group(0)
            span = self._advance(text)
            cat, sub = classify_identifier_or_keyword(text)
            return LexicalToken(
                category=cat,
                subelement=sub,
                value=text,
                canonical_value=text,
                span=span,
            )

        # 8. Unicode emoji or multi-codepoint symbol
        m_emoji = RE_EMOJI_OR_SYMBOL.match(current_slice)
        if m_emoji:
            text = m_emoji.group(0)
            span = self._advance(text)
            cat, sub = classify_symbol(text)
            return LexicalToken(
                category=cat,
                subelement=sub,
                value=text,
                canonical_value=text,
                span=span,
            )

        # 9. Single fallback character (special character, single punctuation)
        char = current_slice[0]
        span = self._advance(char)
        cat, sub = classify_symbol(char)
        return LexicalToken(
            category=cat,
            subelement=sub,
            value=char,
            canonical_value=char,
            span=span,
        )

    @classmethod
    def reconstruct(cls, tokens: List[LexicalToken]) -> str:
        """Reconstruct exact source text from token stream."""
        return "".join(t.value for t in tokens)
