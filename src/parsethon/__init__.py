"""Parsethon: Extensible Python lexical parser, tokenizer, and Tongue translation system."""

from parsethon.lexicon import (
    LexicalToken,
    SourcePosition,
    SourceSpan,
    TokenCategory,
    TokenSubelement,
    classify_identifier_or_keyword,
    classify_symbol,
)
from parsethon.tokenizer import ParsethonTokenizer
from parsethon.tongue import (
    Tongue,
    TongueRegistry,
    TongueValidationError,
    registry,
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
]
