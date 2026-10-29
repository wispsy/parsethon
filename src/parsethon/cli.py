"""Command-line interface for Parsethon powered by expose-interface."""

from __future__ import annotations

import ast
import os
import sys
from pathlib import Path
from typing import List, Optional

import expose_interface as ei
from parsethon.lexicon import TokenCategory
from parsethon.runtime import execute_file
from parsethon.tokenizer import ParsethonTokenizer
from parsethon.tongue import registry
from parsethon.translator import translate_from_python, translate_to_python

app = ei.Interface("parsethon", description="Parsethon: Extensible Python Lexical Parser and Tongue System")


@app.command
def run(path: str, tongue: str = "") -> None:
    """Execute a Tongue source file under CPython."""
    try:
        execute_file(path, tongue=tongue if tongue else None)
    except Exception as e:
        sys.stderr.write(f"{e}\n")
        sys.exit(1)


@app.command
def translate(
    path: str,
    tongue: str = "",
    to_python: bool = True,
    output: str = "",
) -> None:
    """Translate source code between Tongue and canonical Python syntax."""
    file_path = Path(path)
    if not file_path.exists():
        sys.stderr.write(f"File not found: {path}\n")
        sys.exit(1)

    source = file_path.read_text(encoding="utf-8")
    t_name = tongue if tongue else None

    # Infer tongue if to_python
    if not t_name:
        from parsethon.runtime import detect_tongue_from_filename, detect_tongue_from_source
        t_name = detect_tongue_from_source(source) or detect_tongue_from_filename(path) or "es"

    if to_python:
        result = translate_to_python(source, t_name)
    else:
        result = translate_from_python(source, t_name)

    if output:
        Path(output).write_text(result, encoding="utf-8")
        print(f"Wrote translated code to {output}")
    else:
        sys.stdout.write(result)


@app.command
def tokenize(path: str, verbose: bool = False) -> None:
    """Tokenize a source file and display lexical classification and subelements."""
    file_path = Path(path)
    if not file_path.exists():
        sys.stderr.write(f"File not found: {path}\n")
        sys.exit(1)

    source = file_path.read_text(encoding="utf-8")
    tokenizer = ParsethonTokenizer(source)
    tokens = tokenizer.tokenize()

    print(f"Total tokens emitted: {len(tokens)}")
    print(f"{'SPAN':<16} {'CATEGORY':<14} {'SUBELEMENT':<20} {'VALUE'}")
    print("-" * 65)

    for tok in tokens:
        if not verbose and tok.category in (TokenCategory.WHITESPACE, TokenCategory.NEWLINE):
            continue
        span_str = f"{tok.span.start.line}:{tok.span.start.column}-{tok.span.end.line}:{tok.span.end.column}"
        repr_val = repr(tok.value)
        if len(repr_val) > 25:
            repr_val = repr_val[:22] + "..."
        print(f"{span_str:<16} {tok.category.value:<14} {tok.subelement.value:<20} {repr_val}")


@app.command
def list_tongues() -> None:
    """Enumerate all available registered Tongues."""
    print("Available Tongues:")
    for name in registry.list_tongues():
        t = registry.get(name)
        desc = t.description or "No description"
        sample_kw = list(t.keywords.items())[:3]
        samples = ", ".join(f"{k}->{v}" for k, v in sample_kw)
        print(f"  * {name:<10} (v{t.version}): {desc} [{samples}...]")


@app.command
def check(path: str, tongue: str = "") -> None:
    """Validate syntax of a Tongue file without executing."""
    file_path = Path(path)
    if not file_path.exists():
        sys.stderr.write(f"File not found: {path}\n")
        sys.exit(1)

    source = file_path.read_text(encoding="utf-8")
    t_name = tongue if tongue else None
    if not t_name:
        from parsethon.runtime import detect_tongue_from_filename, detect_tongue_from_source
        t_name = detect_tongue_from_source(source) or detect_tongue_from_filename(path) or "es"

    try:
        py_source = translate_to_python(source, t_name)
        ast.parse(py_source, filename=path)
        print(f"Syntax valid: {path} (Tongue: {t_name})")
    except SyntaxError as se:
        sys.stderr.write(f"Syntax error at line {se.lineno}: {se.msg}\n")
        sys.exit(1)


def main(argv: Optional[List[str]] = None) -> None:
    """Main CLI entry point."""
    app.main(argv, prog_name="parsethon")


if __name__ == "__main__":
    main()
