"""JavaScript-style syntax desugaring and formatting for Parsethon.

Enables:
1. Braces `{ ... }` for compound statement code blocks.
2. Semicolons `;` as statement terminators.
3. Whitespace indifference (flat, compact, single-line, or arbitrarily indented code).
4. JavaScript idioms: `function`, `let`/`const`/`var`, `else if`, `catch (e)`,
   `throw`, `===`, `!==`, `&&`, `||`, `!`, `true`, `false`, `null`, `console.log`.
5. Empty block `{}` handling via `pass`.
6. Disambiguation between code blocks and dictionary/set literals `{ ... }`.
7. Reversible translation from standard Python to JS-style syntax.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Set, Tuple

from parsethon.lexicon import TokenCategory
from parsethon.tokenizer import ParsethonTokenizer

BLOCK_START_KEYWORDS: Set[str] = {
    # Python & JS keywords
    "def", "function", "class", "if", "elif", "else", "while", "for",
    "try", "except", "catch", "finally", "with", "match", "case", "switch",
    # Spanish keywords
    "definir", "clase", "si", "siosi", "sino", "mientras", "para",
    "intentar", "excepto", "finalmente", "con", "coincidir", "caso",
    # Pirate keywords
    "chart", "galleon", "perchance", "or_perchance", "otherwise_avast",
    "tide", "reckon", "brave", "scurvy", "anchors_aweigh",
    # Emoji keywords
    "🔨", "🏛️", "❓", "❔", "❗", "🔄", "🔁", "🛡️", "⚠️", "🏁", "🤝",
}

EXPR_PREV_TOKENS: Set[str] = {
    "=", "+=", "-=", "*=", "/=", "//=", "%=", "@=", "&=", "|=", "^=",
    "<<=", ">>=", "**=", ":=", ":", ",", "(", "[", "{",
    "return", "yield", "retornar", "booty", "📦",
    "+", "-", "*", "/", "//", "%", "**", "@", "&", "|", "^", "~",
    "==", "!=", "<", "<=", ">", ">=", "in", "is", "and", "or", "not",
    "&&", "||", "!", "===", "!==",
}


def has_js_style_syntax(source: str) -> bool:
    """Detect if the source text contains JS-style syntax elements."""
    # Check for keywords or syntax markers
    patterns = [
        r"\bfunction\b",
        r"\blet\b",
        r"\bconst\b",
        r"\bvar\b",
        r"\bconsole\.log\b",
        r"\bcatch\b",
        r"\bthrow\b",
        r"===|!==|&&|\|\|",
        r"\b(if|else|while|for|def|function|class|try|catch|finally)\b[^{};]*\{",
        r"\}[ \t]*(else|catch|finally)\b",
    ]
    for pat in patterns:
        if re.search(pat, source):
            return True

    # Check for block-style braces
    if "{" in source and "}" in source:
        # Check if any { appears at end of line or after )
        if re.search(r"(\)|\belse|\btry|\bfinally|\bclass\s+\w+)[ \t]*\{", source):
            return True
        if re.search(r"^[ \t]*\{", source, re.MULTILINE):
            return True

    return False


def desugar_js_syntax(source: str) -> str:
    """Convert JavaScript-style syntax into standard, properly indented Python syntax."""
    tokenizer = ParsethonTokenizer(source)
    tokens = tokenizer.tokenize()

    if not tokens:
        return source

    # Phase 1: Filter significant tokens and classify brace roles (block vs expr)
    sig_tokens: List[Tuple[int, any]] = [
        (i, t) for i, t in enumerate(tokens)
        if t.category not in (TokenCategory.WHITESPACE, TokenCategory.NEWLINE, TokenCategory.COMMENT)
    ]

    brace_types: Dict[int, str] = {}
    brace_stack: List[Tuple[str, int]] = []

    for sig_idx, (orig_idx, tok) in enumerate(sig_tokens):
        if tok.value == "{":
            prev_tok = sig_tokens[sig_idx - 1][1] if sig_idx > 0 else None
            is_block = False

            if prev_tok is None or prev_tok.value in (";", "{", "}"):
                is_block = True
            elif prev_tok.value in ("=", "+=", "-=", "*=", "/=", ",", "(", "[", "in", "return", "yield"):
                is_block = False
            elif prev_tok.value == ")":
                is_block = True
            elif prev_tok.value in BLOCK_START_KEYWORDS:
                is_block = True
            elif prev_tok.value == ":":
                is_block = True
            else:
                # Trace backwards to find start of statement
                k = sig_idx - 1
                stmt_first = None
                has_assign = False
                while k >= 0 and sig_tokens[k][1].value not in (";", "{", "}"):
                    val = sig_tokens[k][1].value
                    if val in ("=", "return", "yield"):
                        has_assign = True
                    stmt_first = val
                    k -= 1
                is_block = (stmt_first is None or (stmt_first in BLOCK_START_KEYWORDS and not has_assign))

            b_type = "block" if is_block else "expr"
            brace_types[orig_idx] = b_type
            brace_stack.append((b_type, orig_idx))

        elif tok.value == "}":
            if brace_stack:
                b_type, _ = brace_stack.pop()
                brace_types[orig_idx] = b_type
            else:
                brace_types[orig_idx] = "block"

    # Identify empty blocks `{ }`
    skip_indices: Set[int] = set()
    for i, tok in enumerate(tokens):
        if tok.value == "{" and brace_types.get(i) == "block":
            j = i + 1
            while j < len(tokens) and tokens[j].category in (TokenCategory.WHITESPACE, TokenCategory.NEWLINE, TokenCategory.COMMENT):
                j += 1
            if j < len(tokens) and tokens[j].value == "}" and brace_types.get(j) == "block":
                brace_types[i] = "empty_block"
                skip_indices.add(j)

    # Phase 2: Token conversion and block indentation emission
    output_lines: List[str] = []
    curr_line_parts: List[str] = []
    indent_level = 0
    paren_depth = 0

    def format_tokens(parts: List[str]) -> str:
        """Format accumulated tokens with proper spacing."""
        res: List[str] = []
        for p in parts:
            if not res:
                res.append(p)
                continue
            prev = res[-1]
            # Space between words/identifiers/literals
            if (prev[-1].isalnum() or prev[-1] in "_$'\"") and (p[0].isalnum() or p[0] in "_$'\""):
                res.append(" ")
            elif p in ("=", "+=", "-=", "*=", "/=", "==", "!=", "<", ">", "<=", ">=", "+", "-", "*", "/", "//", "%", "and", "or", "not", "in", "is", "as"):
                res.append(" ")
            elif prev in ("=", "+=", "-=", "*=", "/=", "==", "!=", "<", ">", "<=", ">=", "+", "-", "*", "/", "//", "%", "and", "or", "not", "in", "is", "as", ",", ":"):
                res.append(" ")
            res.append(p)
        return "".join(res)

    def flush_line() -> None:
        nonlocal curr_line_parts
        if curr_line_parts:
            text = format_tokens(curr_line_parts).strip()
            if text:
                output_lines.append(("    " * indent_level) + text)
            curr_line_parts = []

    i = 0
    n = len(tokens)

    while i < n:
        if i in skip_indices:
            i += 1
            continue

        tok = tokens[i]

        # Preserve comments
        if tok.category == TokenCategory.COMMENT:
            flush_line()
            output_lines.append(("    " * indent_level) + tok.value)
            i += 1
            continue

        if tok.category in (TokenCategory.WHITESPACE, TokenCategory.NEWLINE):
            i += 1
            continue

        # Track paren/bracket depth
        if tok.value in ("(", "["):
            paren_depth += 1
        elif tok.value in (")", "]"):
            paren_depth = max(0, paren_depth - 1)

        b_type = brace_types.get(i)

        # 1. Empty block `{}` -> emit header + `:` and `pass`
        if b_type == "empty_block":
            header = format_tokens(curr_line_parts).strip()
            if not header.endswith(":"):
                header += ":"
            output_lines.append(("    " * indent_level) + header)
            output_lines.append(("    " * (indent_level + 1)) + "pass")
            curr_line_parts = []
            i += 1
            continue

        # 2. Block opening `{` -> emit header + `:` and increase indent
        if b_type == "block" and tok.value == "{":
            header = format_tokens(curr_line_parts).strip()
            if not header.endswith(":"):
                header += ":"
            output_lines.append(("    " * indent_level) + header)
            curr_line_parts = []
            indent_level += 1
            i += 1
            continue

        # 3. Block closing `}` -> flush current line and decrease indent
        if b_type == "block" and tok.value == "}":
            flush_line()
            indent_level = max(0, indent_level - 1)
            i += 1
            continue

        # 4. Semicolon `;` at statement level
        if tok.value == ";" and paren_depth == 0:
            flush_line()
            i += 1
            continue

        # 5. Variable declaration keywords: `let`, `const`, `var` at statement start
        if tok.value in ("let", "const", "var") and not curr_line_parts and paren_depth == 0:
            i += 1
            continue

        # 6. `function` -> `def`
        if tok.value == "function":
            curr_line_parts.append("def")
            i += 1
            continue

        # 7. `else if` -> `elif`
        if tok.value == "else":
            # Peek ahead to next non-trivia token
            j = i + 1
            while j < n and tokens[j].category in (TokenCategory.WHITESPACE, TokenCategory.NEWLINE):
                j += 1
            if j < n and tokens[j].value == "if":
                curr_line_parts.append("elif")
                i = j + 1
                continue
            curr_line_parts.append("else")
            i += 1
            continue

        # 8. `catch (e)` -> `except Exception as e`
        if tok.value == "catch":
            j = i + 1
            while j < n and tokens[j].category in (TokenCategory.WHITESPACE, TokenCategory.NEWLINE):
                j += 1
            if j < n and tokens[j].value == "(":
                # extract variable name
                k = j + 1
                while k < n and tokens[k].category in (TokenCategory.WHITESPACE, TokenCategory.NEWLINE):
                    k += 1
                err_var = tokens[k].value if k < n else "e"
                # skip until closing )
                m = k + 1
                while m < n and tokens[m].value != ")":
                    m += 1
                curr_line_parts.append(f"except Exception as {err_var}")
                i = m + 1
                continue
            curr_line_parts.append("except Exception")
            i += 1
            continue

        # 9. `throw` -> `raise`
        if tok.value == "throw":
            curr_line_parts.append("raise")
            i += 1
            continue

        # 10. `for (let x of items)` or `for (let x in items)`
        if tok.value == "for":
            j = i + 1
            while j < n and tokens[j].category in (TokenCategory.WHITESPACE, TokenCategory.NEWLINE):
                j += 1
            if j < n and tokens[j].value == "(":
                # scan tokens inside `(...)`
                depth = 1
                k = j + 1
                for_inner: List[any] = []
                while k < n and depth > 0:
                    if tokens[k].value == "(":
                        depth += 1
                    elif tokens[k].value == ")":
                        depth -= 1
                    if depth > 0:
                        for_inner.append(tokens[k])
                    k += 1
                # Parse `[let|const|var] x (in|of) iterable`
                inner_sig = [t for t in for_inner if t.category not in (TokenCategory.WHITESPACE, TokenCategory.NEWLINE)]
                if inner_sig and inner_sig[0].value in ("let", "const", "var"):
                    inner_sig = inner_sig[1:]
                # Check for `of` or `in`
                op_idx = -1
                for idx_s, st_tok in enumerate(inner_sig):
                    if st_tok.value in ("of", "in"):
                        op_idx = idx_s
                        break
                if op_idx != -1:
                    var_tokens = [t.value for t in inner_sig[:op_idx]]
                    iter_tokens = [t.value for t in inner_sig[op_idx + 1:]]
                    var_str = format_tokens(var_tokens)
                    iter_str = format_tokens(iter_tokens)
                    curr_line_parts.append(f"for {var_str} in {iter_str}")
                    i = k
                    continue

        # 11. `class Foo extends Bar` -> `class Foo(Bar)`
        if tok.value == "extends":
            # Replace previous class name or wrap base class
            j = i + 1
            while j < n and tokens[j].category in (TokenCategory.WHITESPACE, TokenCategory.NEWLINE):
                j += 1
            if j < n:
                base_class = tokens[j].value
                # Wrap previous name with (base_class)
                curr_line_parts.append(f"({base_class})")
                i = j + 1
                continue

        # 12. Operator and constant replacements
        val = tok.value
        if val == "===":
            curr_line_parts.append("==")
        elif val == "!==":
            curr_line_parts.append("!=")
        elif val == "&&":
            curr_line_parts.append("and")
        elif val == "||":
            curr_line_parts.append("or")
        elif val == "!":
            curr_line_parts.append("not")
        elif val == "true":
            curr_line_parts.append("True")
        elif val == "false":
            curr_line_parts.append("False")
        elif val in ("null", "undefined"):
            curr_line_parts.append("None")
        elif val == "console" and i + 2 < n and tokens[i + 1].value == "." and tokens[i + 2].value == "log":
            curr_line_parts.append("print")
            i += 3
            continue
        else:
            curr_line_parts.append(val)

        i += 1

    flush_line()
    return "\n".join(output_lines) + "\n"


def to_js_syntax(source: str) -> str:
    """Format Python syntax into JavaScript-style syntax with braces and semicolons."""
    lines = source.splitlines()
    output_lines: List[str] = []
    indent_stack: List[int] = [0]

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        indent = len(line) - len(line.lstrip(" "))

        # Close blocks if indent decreased
        while indent < indent_stack[-1]:
            indent_stack.pop()
            closing_indent = " " * indent_stack[-1]
            output_lines.append(f"{closing_indent}}}")

        current_indent = " " * indent

        # Check if line opens a block (ends with :)
        if stripped.endswith(":") and not (stripped.startswith("{") or stripped.startswith("'") or stripped.startswith('"')):
            header = stripped[:-1].strip()

            # Convert keywords
            if header.startswith("def "):
                header = "function " + header[4:]
            elif header.startswith("if "):
                cond = header[3:].strip()
                if not (cond.startswith("(") and cond.endswith(")")):
                    header = f"if ({cond})"
            elif header.startswith("elif "):
                cond = header[5:].strip()
                if not (cond.startswith("(") and cond.endswith(")")):
                    header = f"else if ({cond})"
                else:
                    header = f"else if {cond}"
            elif header.startswith("while "):
                cond = header[6:].strip()
                if not (cond.startswith("(") and cond.endswith(")")):
                    header = f"while ({cond})"
            elif header.startswith("for "):
                for_part = header[4:].strip()
                if not (for_part.startswith("(") and for_part.endswith(")")):
                    header = f"for ({for_part})"

            output_lines.append(f"{current_indent}{header} {{")
            # Anticipate next indent level
            indent_stack.append(indent + 4)
        else:
            stmt = stripped
            # Convert keywords/constants
            stmt = re.sub(r"\bTrue\b", "true", stmt)
            stmt = re.sub(r"\bFalse\b", "false", stmt)
            stmt = re.sub(r"\bNone\b", "null", stmt)
            stmt = re.sub(r"\band\b", "&&", stmt)
            stmt = re.sub(r"\bor\b", "||", stmt)
            stmt = re.sub(r"\bnot\b", "!", stmt)
            stmt = re.sub(r"\bprint\(", "console.log(", stmt)

            if not stmt.endswith(";") and not stmt.endswith("{") and not stmt.endswith("}"):
                stmt += ";"
            output_lines.append(f"{current_indent}{stmt}")

    # Close remaining blocks at EOF
    while len(indent_stack) > 1:
        indent_stack.pop()
        closing_indent = " " * indent_stack[-1]
        output_lines.append(f"{closing_indent}}}")

    return "\n".join(output_lines) + "\n"
