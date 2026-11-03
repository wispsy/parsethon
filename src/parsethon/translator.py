"""Bidirectional Tongue <-> Python translation engine."""

from __future__ import annotations

import re
from typing import Callable, List, Optional, Tuple, Union

from parsethon.lexicon import (
    PYTHON_KEYWORDS,
    LexicalToken,
    SourcePosition,
    SourceSpan,
    TokenCategory,
)
from parsethon.sourcemap import SourceMap
from parsethon.tokenizer import ParsethonTokenizer
from parsethon.tongue import Tongue, registry


class ParsethonTranslator:
    """Translates source code between custom Tongues and canonical Python syntax."""

    def __init__(self, tongue: Union[Tongue, str]) -> None:
        if isinstance(tongue, str):
            self.tongue = registry.get(tongue)
        else:
            self.tongue = tongue
        self.last_source_map: Optional[SourceMap] = None

    def to_python(self, tongue_source: str) -> str:
        """Translate source code written in Tongue syntax to standard Python syntax."""
        return self._translate(
            source=tongue_source,
            mapping=self.tongue.reverse_map,
            is_to_python=True,
        )

    def from_python(self, python_source: str) -> str:
        """Translate standard Python source code into Tongue syntax."""
        return self._translate(
            source=python_source,
            mapping=self.tongue.forward_map,
            is_to_python=False,
        )

    def translate_with_sourcemap(
        self,
        source: str,
        is_to_python: bool = True,
    ) -> Tuple[str, SourceMap]:
        """Translate source and return both translated code and the explicit SourceMap."""
        mapping = self.tongue.reverse_map if is_to_python else self.tongue.forward_map
        result = self._translate(source=source, mapping=mapping, is_to_python=is_to_python)
        return result, self.last_source_map or SourceMap()

    def _translate(
        self,
        source: str,
        mapping: dict[str, str],
        is_to_python: bool,
    ) -> str:
        tokenizer = ParsethonTokenizer(source)
        tokens = tokenizer.tokenize()

        orig_records: List[Tuple[SourceSpan, str]] = [
            (t.span, t.value) for t in tokens
        ]

        prev_significant_token: Optional[LexicalToken] = None

        for token in tokens:
            if token.category in (TokenCategory.WHITESPACE, TokenCategory.NEWLINE):
                continue

            # Process f-strings
            if token.category == TokenCategory.FSTRING:
                token.value = self._translate_fstring(
                    token.value,
                    mapping=mapping,
                    is_to_python=is_to_python,
                )
                prev_significant_token = token
                continue

            # Skip comments and regular string literals
            if token.category in (TokenCategory.STRING, TokenCategory.COMMENT):
                prev_significant_token = token
                continue

            # Guard attribute access: don't translate if preceded by '.' and target is Python keyword
            is_dot_access = (
                prev_significant_token is not None
                and prev_significant_token.value == "."
            )

            val = token.value
            if val in mapping:
                replacement = mapping[val]

                # If translating to python and preceded by '.', avoid generating invalid keyword attribute
                if is_to_python and is_dot_access and replacement in PYTHON_KEYWORDS:
                    prev_significant_token = token
                    continue

                # If translating from python, only translate identifiers if they are known builtins or constants
                if not is_to_python and token.category == TokenCategory.IDENTIFIER:
                    if val not in self.tongue.builtins and val not in self.tongue.constants:
                        prev_significant_token = token
                        continue

                token.value = replacement

            prev_significant_token = token

        # Build SourceMap tracking remapped token lengths and line/column positions
        source_map = SourceMap()
        curr_line = 1
        curr_col = 0

        for (orig_span, orig_text), tok in zip(orig_records, tokens):
            t_text = tok.value
            start_pos = SourcePosition(curr_line, curr_col)
            lines = t_text.splitlines(keepends=True)
            if not lines:
                end_pos = start_pos
            elif len(lines) == 1 and not (lines[0].endswith("\n") or lines[0].endswith("\r")):
                curr_col += len(t_text)
                end_pos = SourcePosition(curr_line, curr_col)
            else:
                for l in lines:
                    if l.endswith("\n") or l.endswith("\r"):
                        curr_line += 1
                        curr_col = 0
                    else:
                        curr_col += len(l)
                end_pos = SourcePosition(curr_line, curr_col)

            translated_span = SourceSpan(start_pos, end_pos)
            source_map.add_entry(
                original_span=orig_span,
                translated_span=translated_span,
                original_text=orig_text,
                translated_text=t_text,
            )

        self.last_source_map = source_map

        return ParsethonTokenizer.reconstruct(tokens)

    def _translate_fstring(
        self,
        fstring_literal: str,
        mapping: dict[str, str],
        is_to_python: bool,
    ) -> str:
        """Translate expressions within f-strings while leaving string text intact."""
        # Find prefix, e.g. f, rf, F, fr
        quote_start = -1
        for i, ch in enumerate(fstring_literal):
            if ch in ('"', "'"):
                quote_start = i
                break

        if quote_start == -1:
            return fstring_literal

        prefix = fstring_literal[:quote_start]
        body_with_quotes = fstring_literal[quote_start:]

        # Determine quote delimiter (triple or single)
        if body_with_quotes.startswith(('"""', "'''")):
            quote_delim = body_with_quotes[:3]
            inner = body_with_quotes[3:-3]
        else:
            quote_delim = body_with_quotes[0]
            inner = body_with_quotes[1:-1]

        # Scan inner string and translate {expression} blocks
        translated_inner = []
        i = 0
        n = len(inner)

        while i < n:
            # Handle escaped braces {{ or }}
            if inner[i : i + 2] == "{{" or inner[i : i + 2] == "}}":
                translated_inner.append(inner[i : i + 2])
                i += 2
                continue

            if inner[i] == "{":
                # Find matching unescaped }
                brace_depth = 1
                j = i + 1
                in_quote: Optional[str] = None
                while j < n and brace_depth > 0:
                    ch = inner[j]
                    if in_quote:
                        if ch == "\\" and j + 1 < n:
                            j += 2
                            continue
                        if ch == in_quote:
                            in_quote = None
                    else:
                        if ch in ('"', "'"):
                            in_quote = ch
                        elif ch == "{":
                            brace_depth += 1
                        elif ch == "}":
                            brace_depth -= 1
                    j += 1

                if brace_depth == 0:
                    expr_raw = inner[i + 1 : j - 1]
                    # Parse format specifier or conversion if present
                    # Format: expr[!conversion][:format_spec]
                    translated_expr = self._translate_fstring_expr(
                        expr_raw,
                        mapping=mapping,
                        is_to_python=is_to_python,
                    )
                    translated_inner.append(f"{{{translated_expr}}}")
                    i = j
                    continue

            translated_inner.append(inner[i])
            i += 1

        return f"{prefix}{quote_delim}{''.join(translated_inner)}{quote_delim}"

    def _translate_fstring_expr(
        self,
        expr_raw: str,
        mapping: dict[str, str],
        is_to_python: bool,
    ) -> str:
        """Translate an expression inside an f-string, preserving conversions and formats."""
        # Split on conversion or format spec if outside quotes and parentheses
        paren_depth = 0
        in_quote: Optional[str] = None
        split_idx = -1
        k = 0
        while k < len(expr_raw):
            c = expr_raw[k]
            if in_quote:
                if c == "\\" and k + 1 < len(expr_raw):
                    k += 2
                    continue
                if c == in_quote:
                    in_quote = None
            else:
                if c in ('"', "'"):
                    in_quote = c
                elif c in "([{":
                    paren_depth += 1
                elif c in ")]}":
                    paren_depth -= 1
                elif paren_depth == 0 and c in ("!", ":"):
                    split_idx = k
                    break
            k += 1

        if split_idx != -1:
            code_part = expr_raw[:split_idx]
            spec_part = expr_raw[split_idx:]
            translated_code = self._translate(code_part, mapping, is_to_python)
            return f"{translated_code}{spec_part}"
        else:
            return self._translate(expr_raw, mapping, is_to_python)


def translate_to_python(tongue_source: str, tongue: Union[Tongue, str]) -> str:
    """Convenience helper to translate Tongue code to standard Python."""
    return ParsethonTranslator(tongue).to_python(tongue_source)


def translate_from_python(python_source: str, tongue: Union[Tongue, str]) -> str:
    """Convenience helper to translate Python code to Tongue."""
    return ParsethonTranslator(tongue).from_python(python_source)
