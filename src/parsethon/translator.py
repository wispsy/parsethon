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
from parsethon.tokenizer import ParsethonTokenizer, scan_string_literal
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

        # Collect non-trivia token indices and paren depths for context analysis
        sig_indices: List[int] = []
        paren_depths: Dict[int, int] = {}
        depth = 0
        for idx, tok in enumerate(tokens):
            if tok.category in (TokenCategory.WHITESPACE, TokenCategory.NEWLINE, TokenCategory.COMMENT):
                continue
            sig_indices.append(idx)
            if tok.value in ("(", "[", "{"):
                depth += 1
            elif tok.value in (")", "]", "}"):
                depth = max(0, depth - 1)
            paren_depths[idx] = depth

        def_keywords = {"def", "class"}
        import_stmt_keywords = {"import", "from", "as"}
        if is_to_python:
            for k in ("def", "class"):
                if k in self.tongue.keywords:
                    def_keywords.add(self.tongue.keywords[k])
            for k in ("import", "from", "as"):
                if k in self.tongue.keywords:
                    import_stmt_keywords.add(self.tongue.keywords[k])
        else:
            for k in ("def", "class", "import", "from", "as"):
                if k in self.tongue.keywords:
                    def_keywords.add(k)
                    import_stmt_keywords.add(k)

        # Soft keywords to watch
        if is_to_python:
            match_word = self.tongue.keywords.get("match")
            case_word = self.tongue.keywords.get("case")
        else:
            match_word = "match"
            case_word = "case"

        # Check which lines contain an import statement
        import_lines: set[int] = set()
        for idx in sig_indices:
            tok = tokens[idx]
            if tok.value in (
                "import", "from",
                self.tongue.keywords.get("import", ""),
                self.tongue.keywords.get("from", ""),
            ):
                import_lines.add(tok.span.start.line)

        # Helper to test if a token is in statement start position
        def is_statement_start(sig_pos: int) -> bool:
            if sig_pos == 0:
                return True
            prev_t = tokens[sig_indices[sig_pos - 1]]
            curr_t = tokens[sig_indices[sig_pos]]
            if prev_t.span.end.line < curr_t.span.start.line:
                return True
            if prev_t.value in (":", ";"):
                return True
            return False

        # Helper to check if statement line has a colon
        def statement_has_colon(sig_pos: int) -> bool:
            curr_line = tokens[sig_indices[sig_pos]].span.start.line
            for p in range(sig_pos + 1, len(sig_indices)):
                t = tokens[sig_indices[p]]
                if t.span.start.line > curr_line and paren_depths.get(sig_indices[p], 0) == 0:
                    break
                if t.value == ":" and paren_depths.get(sig_indices[p], 0) == 0:
                    return True
            return False

        for sig_pos, idx in enumerate(sig_indices):
            token = tokens[idx]
            prev_tok = tokens[sig_indices[sig_pos - 1]] if sig_pos > 0 else None
            next_tok = tokens[sig_indices[sig_pos + 1]] if sig_pos + 1 < len(sig_indices) else None

            # Process f-strings
            if token.category == TokenCategory.FSTRING:
                token.value = self._translate_fstring(
                    token.value,
                    mapping=mapping,
                    is_to_python=is_to_python,
                )
                continue

            # Skip comments and regular string literals
            if token.category in (TokenCategory.STRING, TokenCategory.COMMENT):
                continue

            # 1. Attribute access guard (e.g. obj.attr, obj.case, sys.stdout.write)
            is_dot_access = prev_tok is not None and prev_tok.value == "."
            if is_dot_access:
                continue

            # 2. Definition name guard (def func, class MyClass)
            is_def_name = prev_tok is not None and prev_tok.value in def_keywords
            if is_def_name:
                continue

            # 3. Import statements guard (only translate keywords import/from/as, never module/symbol names)
            if token.span.start.line in import_lines:
                if token.value not in import_stmt_keywords:
                    continue

            # 4. Keyword argument guard in function call (e.g. func(match=1, print=True))
            cur_depth = paren_depths.get(idx, 0)
            is_kwarg = cur_depth > 0 and next_tok is not None and next_tok.value == "="
            if is_kwarg:
                continue

            # 5. Soft keywords (match and case) contextual resolution
            if match_word and token.value == match_word:
                in_match_context = (
                    is_statement_start(sig_pos)
                    and next_tok is not None
                    and next_tok.value not in ("=", "+=", "-=", "*=", "/=", "==", "!=", "<", ">", "<=", ">=", ".", ")", "]", "}")
                    and statement_has_colon(sig_pos)
                )
                if in_match_context and token.value in mapping:
                    token.value = mapping[token.value]
                continue

            if case_word and token.value == case_word:
                in_case_context = (
                    is_statement_start(sig_pos)
                    and next_tok is not None
                    and next_tok.value not in ("=", "+=", "-=", "*=", "/=", "==", "!=", "<", ">", "<=", ">=", ".", ")", "]", "}")
                    and statement_has_colon(sig_pos)
                )
                if in_case_context and token.value in mapping:
                    token.value = mapping[token.value]
                continue

            # 6. Standard translation
            val = token.value
            if val in mapping:
                replacement = mapping[val]

                # If translating from python, only translate identifiers if they are known builtins or constants
                if not is_to_python and token.category == TokenCategory.IDENTIFIER:
                    if val not in self.tongue.builtins and val not in self.tongue.constants:
                        continue
                    # Don't translate assigned variable matching builtin name: print = 1
                    if val in self.tongue.builtins and next_tok is not None and next_tok.value == "=":
                        continue

                token.value = replacement

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
                while j < n and brace_depth > 0:
                    str_info = scan_string_literal(inner, j)
                    if str_info is not None:
                        j += len(str_info[0])
                        continue
                    ch = inner[j]
                    if ch == "{":
                        brace_depth += 1
                    elif ch == "}":
                        brace_depth -= 1
                    elif ch == "#":
                        while j < n and inner[j] not in ("\r", "\n"):
                            j += 1
                        continue
                    elif ch == "\\":
                        j += 2
                        continue
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
        """Translate an expression inside an f-string, preserving conversions and nested format specs."""
        paren_depth = 0
        bracket_depth = 0
        brace_depth = 0
        split_idx = -1
        k = 0
        n = len(expr_raw)

        while k < n:
            str_info = scan_string_literal(expr_raw, k)
            if str_info is not None:
                k += len(str_info[0])
                continue

            c = expr_raw[k]
            if c == "(":
                paren_depth += 1
            elif c == ")":
                paren_depth -= 1
            elif c == "[":
                bracket_depth += 1
            elif c == "]":
                bracket_depth -= 1
            elif c == "{":
                brace_depth += 1
            elif c == "}":
                brace_depth -= 1
            elif paren_depth == 0 and bracket_depth == 0 and brace_depth == 0 and c in ("!", ":"):
                split_idx = k
                break
            k += 1

        if split_idx != -1:
            code_part = expr_raw[:split_idx]
            spec_part = expr_raw[split_idx:]
            translated_code = self._translate(code_part, mapping, is_to_python)

            # If spec_part has format_spec with nested expressions (e.g. `:{width}` or `!r:{width}`)
            if ":" in spec_part:
                colon_idx = spec_part.index(":")
                conv_prefix = spec_part[: colon_idx + 1]
                fmt_body = spec_part[colon_idx + 1 :]
                if "{" in fmt_body:
                    fmt_translated = self._translate_fstring(
                        f'f"{{{fmt_body}}}"',
                        mapping=mapping,
                        is_to_python=is_to_python,
                    )
                    if fmt_translated.startswith(('f"{', "f'{")):
                        fmt_body = fmt_translated[3:-2]
                translated_spec = f"{conv_prefix}{fmt_body}"
            else:
                translated_spec = spec_part

            return f"{translated_code}{translated_spec}"
        else:
            return self._translate(expr_raw, mapping, is_to_python)


def translate_to_python(tongue_source: str, tongue: Union[Tongue, str]) -> str:
    """Convenience helper to translate Tongue code to standard Python."""
    return ParsethonTranslator(tongue).to_python(tongue_source)


def translate_from_python(python_source: str, tongue: Union[Tongue, str]) -> str:
    """Convenience helper to translate Python code to Tongue."""
    return ParsethonTranslator(tongue).from_python(python_source)
