"""CPython execution engine and traceback mapping for Parsethon."""

from __future__ import annotations

import builtins
import os
import re
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, Optional, Union

from parsethon.tongue import Tongue, registry
from parsethon.translator import ParsethonTranslator, translate_to_python

RE_TONGUE_HEADER = re.compile(
    r"^[ \t]*#[ \t]*(?:coding[:=]\s*parsethon-([a-zA-Z0-9_-]+)|tongue[:=]\s*([a-zA-Z0-9_-]+))",
    re.MULTILINE,
)


class TongueExecutionError(Exception):
    """Encapsulates an execution failure with mapped Tongue source details."""

    def __init__(
        self,
        message: str,
        filename: str,
        lineno: Optional[int] = None,
        tongue_line: Optional[str] = None,
        original_exc: Optional[BaseException] = None,
        translated_code: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.filename = filename
        self.lineno = lineno
        self.tongue_line = tongue_line
        self.original_exc = original_exc
        self.translated_code = translated_code

    def __str__(self) -> str:
        loc = f" line {self.lineno}" if self.lineno else ""
        header = f"Error in '{self.filename}'{loc}: {self.message}"
        if self.tongue_line:
            header += f"\n  --> {self.tongue_line.strip()}"
        return header


def detect_tongue_from_source(source: str) -> Optional[str]:
    """Detect Tongue from header comments such as `# tongue: es` or `# coding: parsethon-es`."""
    lines = source.splitlines()[:5]  # Check first 5 lines
    for line in lines:
        m = RE_TONGUE_HEADER.match(line)
        if m:
            return m.group(1) or m.group(2)
    return None


def detect_tongue_from_filename(filename: Union[str, Path]) -> Optional[str]:
    """Detect Tongue from filename conventions (e.g. `script.es.py`, `script.emoji.py`)."""
    path = Path(filename)
    parts = path.name.split(".")
    # Example: foo.es.py -> parts = ['foo', 'es', 'py']
    if len(parts) >= 3 and parts[-1] in ("py", "pyt"):
        candidate = parts[-2]
        if candidate in registry.list_tongues():
            return candidate
    return None


class ParsethonRuntime:
    """Executes Tongue code under the standard CPython interpreter."""

    def __init__(self, default_tongue: Optional[Union[Tongue, str]] = None) -> None:
        if isinstance(default_tongue, str):
            self.default_tongue: Optional[Tongue] = registry.get(default_tongue)
        else:
            self.default_tongue = default_tongue

    def resolve_tongue(
        self,
        source: str,
        tongue: Optional[Union[Tongue, str]] = None,
        filename: Optional[str] = None,
    ) -> Tongue:
        """Resolve Tongue by explicit argument, source header, filename, or default."""
        if tongue is not None:
            return registry.get(tongue) if isinstance(tongue, str) else tongue

        header_tongue = detect_tongue_from_source(source)
        if header_tongue:
            return registry.get(header_tongue)

        if filename:
            file_tongue = detect_tongue_from_filename(filename)
            if file_tongue:
                return registry.get(file_tongue)

        if self.default_tongue:
            return self.default_tongue

        raise ValueError(
            "Could not determine Tongue for source code. Please specify explicitly, "
            "add a header comment like '# tongue: es', or use filename convention '*.es.py'."
        )

    def execute(
        self,
        source: str,
        tongue: Optional[Union[Tongue, str]] = None,
        filename: str = "<tongue>",
        custom_globals: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Translate Tongue source and execute under CPython."""
        resolved_tongue = self.resolve_tongue(source, tongue=tongue, filename=filename)
        translator = ParsethonTranslator(resolved_tongue)
        py_source = translator.to_python(source)

        source_lines = source.splitlines()

        # Prepare execution globals
        exec_globals: Dict[str, Any] = {
            "__name__": "__main__",
            "__file__": os.path.abspath(filename) if filename != "<tongue>" else filename,
            "__builtins__": __builtins__,
        }
        if custom_globals:
            exec_globals.update(custom_globals)

        # Inject tongue builtins aliases into globals
        for builtin_orig, builtin_alias in resolved_tongue.builtins.items():
            if hasattr(builtins, builtin_orig):
                exec_globals[builtin_alias] = getattr(builtins, builtin_orig)

        try:
            code_obj = compile(py_source, filename, "exec")
        except SyntaxError as se:
            lineno = se.lineno
            col_offset = se.offset
            orig_pos = (
                translator.last_source_map.lookup_original(lineno, col_offset)
                if translator.last_source_map and lineno is not None
                else None
            )
            mapped_lineno = orig_pos.line if orig_pos else lineno
            tongue_line = (
                source_lines[mapped_lineno - 1]
                if mapped_lineno and 0 < mapped_lineno <= len(source_lines)
                else None
            )
            raise TongueExecutionError(
                message=f"SyntaxError: {se.msg}",
                filename=filename,
                lineno=mapped_lineno,
                tongue_line=tongue_line,
                original_exc=se,
                translated_code=py_source,
            ) from se

        try:
            exec(code_obj, exec_globals)
        except Exception as e:
            # Map exception traceback to original line
            exc_tb = sys.exc_info()[2]
            lineno = None
            if exc_tb:
                tb_frames = traceback.extract_tb(exc_tb)
                for f in reversed(tb_frames):
                    if f.filename == filename:
                        lineno = f.lineno
                        break
            if lineno and translator.last_source_map:
                orig_pos = translator.last_source_map.lookup_original(lineno)
                if orig_pos:
                    lineno = orig_pos.line
            tongue_line = source_lines[lineno - 1] if lineno and 0 < lineno <= len(source_lines) else None
            raise TongueExecutionError(
                message=f"{type(e).__name__}: {e}",
                filename=filename,
                lineno=lineno,
                tongue_line=tongue_line,
                original_exc=e,
                translated_code=py_source,
            ) from e

        return exec_globals

    def execute_file(
        self,
        path: Union[str, Path],
        tongue: Optional[Union[Tongue, str]] = None,
        custom_globals: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute a Tongue source file from disk."""
        filepath = Path(path)
        source = filepath.read_text(encoding="utf-8")
        return self.execute(
            source=source,
            tongue=tongue,
            filename=str(filepath),
            custom_globals=custom_globals,
        )


# Default runtime instance
runtime = ParsethonRuntime()


def execute(
    source: str,
    tongue: Optional[Union[Tongue, str]] = None,
    filename: str = "<tongue>",
    custom_globals: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Convenience helper to execute Tongue code."""
    return runtime.execute(source, tongue=tongue, filename=filename, custom_globals=custom_globals)


def execute_file(
    path: Union[str, Path],
    tongue: Optional[Union[Tongue, str]] = None,
    custom_globals: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Convenience helper to execute a Tongue file from disk."""
    return runtime.execute_file(path, tongue=tongue, custom_globals=custom_globals)
