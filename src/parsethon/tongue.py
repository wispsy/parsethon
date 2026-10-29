"""Tongue specification, validation, serialization, and registry."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


class TongueValidationError(ValueError):
    """Raised when a Tongue specification is invalid or has token collisions."""


@dataclass
class Tongue:
    """A Tongue specifies an alternate vocabulary/lexicon for Python."""

    name: str
    version: str = "1.0.0"
    description: str = ""
    keywords: Dict[str, str] = field(default_factory=dict)
    constants: Dict[str, str] = field(default_factory=dict)
    operators: Dict[str, str] = field(default_factory=dict)
    delimiters: Dict[str, str] = field(default_factory=dict)
    builtins: Dict[str, str] = field(default_factory=dict)

    # Cached translation maps
    _forward_map: Dict[str, str] = field(init=False, default_factory=dict, repr=False)
    _reverse_map: Dict[str, str] = field(init=False, default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        self.validate()
        self._rebuild_maps()

    def validate(self) -> None:
        """Validate that all mappings are unambiguous and non-colliding."""
        if not self.name or not self.name.strip():
            raise TongueValidationError("Tongue name must be a non-empty string.")

        # Check for reverse collisions (two Python tokens mapping to the same Tongue token)
        seen_replacements: Dict[str, str] = {}
        for category_name, mapping in (
            ("keywords", self.keywords),
            ("constants", self.constants),
            ("operators", self.operators),
            ("delimiters", self.delimiters),
            ("builtins", self.builtins),
        ):
            for orig, repl in mapping.items():
                if not orig or not str(orig).strip():
                    raise TongueValidationError(
                        f"Empty original token key found in {category_name}."
                    )
                if not repl or not str(repl).strip():
                    raise TongueValidationError(
                        f"Empty replacement token for '{orig}' in {category_name}."
                    )
                if repl in seen_replacements and seen_replacements[repl] != orig:
                    raise TongueValidationError(
                        f"Colliding replacement token '{repl}': mapped by both "
                        f"'{seen_replacements[repl]}' and '{orig}'."
                    )
                seen_replacements[repl] = orig

    def _rebuild_maps(self) -> None:
        """Build forward and reverse token translation lookup dictionaries."""
        forward: Dict[str, str] = {}
        # Merge all sections into unified dictionary
        for mapping in (
            self.keywords,
            self.constants,
            self.operators,
            self.delimiters,
            self.builtins,
        ):
            forward.update(mapping)

        self._forward_map = forward
        self._reverse_map = {repl: orig for orig, repl in forward.items()}

    @property
    def forward_map(self) -> Dict[str, str]:
        """Mapping from Python canonical token -> Tongue token."""
        return dict(self._forward_map)

    @property
    def reverse_map(self) -> Dict[str, str]:
        """Mapping from Tongue token -> Python canonical token."""
        return dict(self._reverse_map)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize Tongue to a dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "keywords": self.keywords,
            "constants": self.constants,
            "operators": self.operators,
            "delimiters": self.delimiters,
            "builtins": self.builtins,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Tongue:
        """Create a Tongue from a dictionary."""
        return cls(
            name=data["name"],
            version=data.get("version", "1.0.0"),
            description=data.get("description", ""),
            keywords=data.get("keywords", {}),
            constants=data.get("constants", {}),
            operators=data.get("operators", {}),
            delimiters=data.get("delimiters", {}),
            builtins=data.get("builtins", {}),
        )

    def to_json(self, indent: int = 2) -> str:
        """Serialize Tongue to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> Tongue:
        """Deserialize Tongue from a JSON string."""
        return cls.from_dict(json.loads(json_str))

    def save(self, path: str | Path) -> None:
        """Save Tongue definition to a JSON file."""
        Path(path).write_text(self.to_json(), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> Tongue:
        """Load Tongue definition from a JSON file."""
        content = Path(path).read_text(encoding="utf-8")
        return cls.from_json(content)


class TongueRegistry:
    """Central registry for discovering and storing available Tongues."""

    def __init__(self) -> None:
        self._tongues: Dict[str, Tongue] = {}
        self._register_builtins()

    def register(self, tongue: Tongue, overwrite: bool = False) -> None:
        """Register a Tongue in the registry."""
        if tongue.name in self._tongues and not overwrite:
            raise ValueError(f"Tongue '{tongue.name}' is already registered.")
        self._tongues[tongue.name] = tongue

    def get(self, name: str) -> Tongue:
        """Retrieve a Tongue by name."""
        if name not in self._tongues:
            available = ", ".join(repr(k) for k in self._tongues.keys())
            raise KeyError(f"Tongue '{name}' not found. Available tongues: [{available}]")
        return self._tongues[name]

    def list_tongues(self) -> List[str]:
        """Return names of all registered Tongues."""
        return sorted(self._tongues.keys())

    def _register_builtins(self) -> None:
        """Register default built-in tongues: Spanish, Emoji, and Pirate."""
        # 1. Spanish Tongue
        self.register(
            Tongue(
                name="es",
                version="1.0.0",
                description="Spanish language Python Tongue",
                keywords={
                    "def": "definir",
                    "return": "retornar",
                    "if": "si",
                    "elif": "siosi",
                    "else": "sino",
                    "while": "mientras",
                    "for": "para",
                    "in": "en",
                    "break": "romper",
                    "continue": "continuar",
                    "pass": "pasar",
                    "class": "clase",
                    "import": "importar",
                    "from": "desde",
                    "as": "como",
                    "try": "intentar",
                    "except": "excepto",
                    "finally": "finalmente",
                    "raise": "lanzar",
                    "with": "con",
                    "lambda": "funcion",
                    "match": "coincidir",
                    "case": "caso",
                },
                constants={
                    "True": "Verdadero",
                    "False": "Falso",
                    "None": "Nada",
                },
                operators={
                    "and": "y",
                    "or": "o",
                    "not": "no",
                    "is": "es",
                },
                builtins={
                    "print": "imprimir",
                    "range": "rango",
                    "len": "longitud",
                },
            )
        )

        # 2. Emoji Tongue
        self.register(
            Tongue(
                name="emoji",
                version="1.0.0",
                description="Iconic Emoji Python Tongue",
                keywords={
                    "def": "🔨",
                    "return": "📦",
                    "if": "❓",
                    "elif": "❔",
                    "else": "❗",
                    "while": "🔄",
                    "for": "🔁",
                    "in": "📥",
                    "break": "🛑",
                    "continue": "⏩",
                    "pass": "💤",
                    "class": "🏛️",
                    "import": "🚚",
                    "from": "🏠",
                    "as": "🏷️",
                    "try": "🛡️",
                    "except": "⚠️",
                    "finally": "🏁",
                    "raise": "💥",
                    "with": "🤝",
                },
                constants={
                    "True": "✅",
                    "False": "❌",
                    "None": "🕳️",
                },
                operators={
                    "and": "➕",
                    "or": "🔀",
                    "not": "🚫",
                },
                builtins={
                    "print": "📢",
                    "len": "📏",
                },
            )
        )

        # 3. Pirate Tongue
        self.register(
            Tongue(
                name="pirate",
                version="1.0.0",
                description="Swashbuckling Pirate Python Tongue",
                keywords={
                    "def": "chart",
                    "return": "booty",
                    "if": "perchance",
                    "elif": "or_perchance",
                    "else": "otherwise_avast",
                    "while": "tide",
                    "for": "reckon",
                    "in": "aboard",
                    "break": "abandon_ship",
                    "continue": "sail_on",
                    "pass": "belay",
                    "class": "galleon",
                    "import": "plunder",
                    "from": "isle",
                    "as": "known_as",
                    "try": "brave",
                    "except": "scurvy",
                    "finally": "anchors_aweigh",
                    "raise": "mutiny",
                },
                constants={
                    "True": "aye",
                    "False": "nay",
                    "None": "davy_jones",
                },
                operators={
                    "and": "an'",
                    "or": "or_else",
                    "not": "nay_not",
                },
                builtins={
                    "print": "ahoy",
                    "len": "tally",
                },
            )
        )


# Global default registry instance
registry = TongueRegistry()
