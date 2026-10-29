"""Parsethon: Extensible Python lexical parser, tokenizer, and Tongue translation system."""

from parsethon.cli import app as cli_app, main
from parsethon.importer import (
    disable,
    enable,
    install_codec,
    install_importer,
    uninstall_codec,
    uninstall_importer,
)
from parsethon.lexicon import (
    LexicalToken,
    SourcePosition,
    SourceSpan,
    TokenCategory,
    TokenSubelement,
    classify_identifier_or_keyword,
    classify_symbol,
)
from parsethon.runtime import (
    ParsethonRuntime,
    TongueExecutionError,
    execute,
    execute_file,
    runtime,
)
from parsethon.tokenizer import ParsethonTokenizer
from parsethon.tongue import (
    Tongue,
    TongueRegistry,
    TongueValidationError,
    registry,
)
from parsethon.translator import (
    ParsethonTranslator,
    translate_from_python,
    translate_to_python,
)

__version__ = "0.1.0"
__all__ = [
    "LexicalToken",
    "SourcePosition",
    "SourceSpan",
    "TokenCategory",
    "TokenSubelement",
    "classify_identifier_or_keyword",
    "classify_symbol",
    "ParsethonTokenizer",
    "Tongue",
    "TongueRegistry",
    "TongueValidationError",
    "registry",
    "ParsethonTranslator",
    "translate_to_python",
    "translate_from_python",
    "ParsethonRuntime",
    "TongueExecutionError",
    "execute",
    "execute_file",
    "runtime",
    "install_importer",
    "uninstall_importer",
    "install_codec",
    "uninstall_codec",
    "enable",
    "disable",
    "cli_app",
    "main",
]
