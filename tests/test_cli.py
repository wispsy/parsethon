"""Unit tests for Parsethon CLI commands powered by expose-interface."""

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from parsethon.cli import app


class TestCLI(unittest.TestCase):
    def test_help_formatting(self):
        help_text = app.format_help()
        self.assertIn("run", help_text)
        self.assertIn("translate", help_text)
        self.assertIn("tokenize", help_text)
        self.assertIn("list-tongues", help_text)
        self.assertIn("check", help_text)

    def test_cli_list_tongues(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            app.invoke(["list-tongues"])
        out = buf.getvalue()
        self.assertIn("Available Tongues:", out)
        self.assertIn("es", out)
        self.assertIn("emoji", out)
        self.assertIn("pirate", out)

    def test_cli_tokenize(self):
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tmp:
            tmp.write("def foo():\n    return 42\n")
            tmp_path = Path(tmp.name)
        try:
            buf = io.StringIO()
            with redirect_stdout(buf):
                app.invoke(["tokenize", str(tmp_path)])
            out = buf.getvalue()
            self.assertIn("Total tokens emitted:", out)
            self.assertIn("keyword", out)
            self.assertIn("kw_definition", out)
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    def test_cli_check_syntax(self):
        with tempfile.NamedTemporaryFile("w", suffix=".es.py", delete=False) as tmp:
            tmp.write("definir saludar():\n    retornar 'hola'\n")
            tmp_path = Path(tmp.name)
        try:
            buf = io.StringIO()
            with redirect_stdout(buf):
                app.invoke(["check", str(tmp_path)])
            out = buf.getvalue()
            self.assertIn("Syntax valid:", out)
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    def test_cli_translate(self):
        with tempfile.NamedTemporaryFile("w", suffix=".es.py", delete=False) as tmp:
            tmp.write("definir test(): retornar 99\n")
            tmp_path = Path(tmp.name)
        out_file = tmp_path.with_suffix(".translated.py")
        try:
            app.invoke(["translate", str(tmp_path), "--output", str(out_file)])
            self.assertTrue(out_file.exists())
            content = out_file.read_text(encoding="utf-8")
            self.assertIn("def test():", content)
            self.assertIn("return 99", content)
        finally:
            if tmp_path.exists():
                tmp_path.unlink()
            if out_file.exists():
                out_file.unlink()

    def test_cli_run(self):
        with tempfile.NamedTemporaryFile("w", suffix=".es.py", delete=False) as tmp:
            tmp.write("imprimir('CLI runner working!')\n")
            tmp_path = Path(tmp.name)
        try:
            buf = io.StringIO()
            with redirect_stdout(buf):
                app.invoke(["run", str(tmp_path)])
            out = buf.getvalue()
            self.assertIn("CLI runner working!", out)
        finally:
            if tmp_path.exists():
                tmp_path.unlink()


if __name__ == "__main__":
    unittest.main()
