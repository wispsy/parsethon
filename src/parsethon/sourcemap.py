"""Explicit bidirectional source mapping between original and translated code spans."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from parsethon.lexicon import SourcePosition, SourceSpan


@dataclass(frozen=True)
class SourceMapEntry:
    """Represents a mapped span between original source and translated source."""

    original_span: SourceSpan
    translated_span: SourceSpan
    original_text: str
    translated_text: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_span": {
                "start": {"line": self.original_span.start.line, "column": self.original_span.start.column},
                "end": {"line": self.original_span.end.line, "column": self.original_span.end.column},
            },
            "translated_span": {
                "start": {"line": self.translated_span.start.line, "column": self.translated_span.start.column},
                "end": {"line": self.translated_span.end.line, "column": self.translated_span.end.column},
            },
            "original_text": self.original_text,
            "translated_text": self.translated_text,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SourceMapEntry:
        orig = data["original_span"]
        trans = data["translated_span"]
        return cls(
            original_span=SourceSpan(
                start=SourcePosition(orig["start"]["line"], orig["start"]["column"]),
                end=SourcePosition(orig["end"]["line"], orig["end"]["column"]),
            ),
            translated_span=SourceSpan(
                start=SourcePosition(trans["start"]["line"], trans["start"]["column"]),
                end=SourcePosition(trans["end"]["line"], trans["end"]["column"]),
            ),
            original_text=data["original_text"],
            translated_text=data["translated_text"],
        )


@dataclass
class SourceMap:
    """Bidirectional source map connecting original and translated source coordinates."""

    entries: List[SourceMapEntry] = field(default_factory=list)

    def add_entry(
        self,
        original_span: SourceSpan,
        translated_span: SourceSpan,
        original_text: str,
        translated_text: str,
    ) -> None:
        self.entries.append(
            SourceMapEntry(
                original_span=original_span,
                translated_span=translated_span,
                original_text=original_text,
                translated_text=translated_text,
            )
        )

    def lookup_original(self, line: int, column: Optional[int] = None) -> Optional[SourcePosition]:
        """Look up the original source position corresponding to a translated (line, column)."""
        if not self.entries:
            return None

        # Filter entries that are actually on this line (starting on this line, or spanning across it)
        line_entries = [
            e for e in self.entries
            if e.translated_span.start.line == line
            or (e.translated_span.start.line < line and (e.translated_span.end.line > line or (e.translated_span.end.line == line and e.translated_span.end.column > 0)))
        ]

        if not line_entries:
            # Fallback to closest line entry
            closest = min(self.entries, key=lambda e: abs(e.translated_span.start.line - line))
            return closest.original_span.start

        if column is None:
            # Prefer the first token starting on this line if available
            starts_on_line = [e for e in line_entries if e.translated_span.start.line == line]
            target = starts_on_line[0] if starts_on_line else line_entries[0]
            return target.original_span.start

        # Search for entry containing (line, column)
        for e in line_entries:
            t_start = e.translated_span.start
            t_end = e.translated_span.end

            if (t_start.line < line or (t_start.line == line and t_start.column <= column)) and (
                line < t_end.line or (line == t_end.line and column <= t_end.column)
            ):
                # Within this entry
                if t_start.line == line and e.original_span.start.line == e.original_span.end.line:
                    offset = column - t_start.column
                    mapped_col = e.original_span.start.column + min(offset, len(e.original_text))
                    return SourcePosition(line=e.original_span.start.line, column=mapped_col)
                return e.original_span.start

        # If column is past the last token on this line
        return line_entries[-1].original_span.end

    def lookup_translated(self, line: int, column: Optional[int] = None) -> Optional[SourcePosition]:
        """Look up the translated source position corresponding to an original (line, column)."""
        if not self.entries:
            return None

        line_entries = [
            e for e in self.entries
            if e.original_span.start.line == line
            or (e.original_span.start.line < line and (e.original_span.end.line > line or (e.original_span.end.line == line and e.original_span.end.column > 0)))
        ]

        if not line_entries:
            closest = min(self.entries, key=lambda e: abs(e.original_span.start.line - line))
            return closest.translated_span.start

        if column is None:
            starts_on_line = [e for e in line_entries if e.original_span.start.line == line]
            target = starts_on_line[0] if starts_on_line else line_entries[0]
            return target.translated_span.start

        for e in line_entries:
            o_start = e.original_span.start
            o_end = e.original_span.end

            if (o_start.line < line or (o_start.line == line and o_start.column <= column)) and (
                line < o_end.line or (line == o_end.line and column <= o_end.column)
            ):
                if o_start.line == line and e.translated_span.start.line == e.translated_span.end.line:
                    offset = column - o_start.column
                    mapped_col = e.translated_span.start.column + min(offset, len(e.translated_text))
                    return SourcePosition(line=e.translated_span.start.line, column=mapped_col)
                return e.translated_span.start

        return line_entries[-1].translated_span.end

    def to_dict(self) -> Dict[str, Any]:
        return {"entries": [e.to_dict() for e in self.entries]}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SourceMap:
        return cls(entries=[SourceMapEntry.from_dict(d) for d in data.get("entries", [])])
