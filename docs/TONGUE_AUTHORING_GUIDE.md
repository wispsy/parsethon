# Tongue Authoring Guide

A **Tongue** defines an alternate vocabulary and lexicon for writing Python code. It is a declarative specification that allows developers to replace Python keywords, literal constants, logical operators, and standard built-ins with custom terminology, symbols, or localized languages.

---

## 1. Anatomy of a Tongue

A Tongue specification contains:
- `name`: Unique short identifier (e.g. `es`, `fr`, `emoji`, `pirate`, `math`).
- `version`: Semantic version string (e.g. `1.0.0`).
- `description`: Human-readable summary.
- `keywords`: Dictionary mapping canonical Python keywords to Tongue replacements.
- `constants`: Dictionary mapping literal constants (`True`, `False`, `None`) to Tongue replacements.
- `operators`: Dictionary mapping word operators (`and`, `or`, `not`, `is`, `in`) to Tongue replacements.
- `delimiters`: (Optional) Symbol or punctuation aliases.
- `builtins`: (Optional) Function aliases for standard built-ins (`print`, `len`, `range`).

---

## 2. Defining a Tongue in Python

```python
from parsethon import Tongue, registry

french = Tongue(
    name="fr",
    version="1.0.0",
    description="French Python Tongue",
    keywords={
        "def": "definir",
        "return": "retourner",
        "if": "si",
        "elif": "sinonsi",
        "else": "sinon",
        "while": "tantque",
        "for": "pour",
        "in": "dans",
        "break": "rompre",
        "continue": "continuer",
        "class": "classe",
        "import": "importer",
        "from": "depuis",
        "try": "essayer",
        "except": "sauf",
        "finally": "enfin",
        "raise": "lever",
        "with": "avec",
    },
    constants={
        "True": "Vrai",
        "False": "Faux",
        "None": "Rien",
    },
    operators={
        "and": "et",
        "or": "ou",
        "not": "non",
        "is": "est",
    },
    builtins={
        "print": "afficher",
        "len": "longueur",
    },
)

# Register into the global registry
registry.register(french)
```

---

## 3. Collision Validation Rules

Parsethon enforces strict ambiguity checks upon Tongue creation:
1. **No Duplicate Targets (Reverse Collisions):**
   Two distinct Python elements cannot map to the same Tongue replacement:
   ```python
   # INVALID: will raise TongueValidationError!
   Tongue(name="bad", keywords={"def": "creer", "class": "creer"})
   ```
2. **Non-Empty Tokens:**
   Neither the original key nor the replacement value may be whitespace or empty strings.

---

## 4. Saving and Loading Tongues (JSON)

Tongues can be saved to and loaded from JSON files:

```python
# Save to disk
french.save("tongues/french.json")

# Load from disk
loaded_tongue = Tongue.load("tongues/french.json")
registry.register(loaded_tongue)
```

### JSON Format:
```json
{
  "name": "fr",
  "version": "1.0.0",
  "description": "French Python Tongue",
  "keywords": {
    "def": "definir",
    "return": "retourner",
    "if": "si"
  },
  "constants": {
    "True": "Vrai",
    "False": "Faux",
    "None": "Rien"
  },
  "operators": {
    "and": "et",
    "or": "ou"
  },
  "delimiters": {},
  "builtins": {
    "print": "afficher"
  }
}
```

---

## 5. File Naming & Header Conventions

To allow Parsethon to auto-detect which Tongue a file uses:
1. **Filename Extension:**
   - `<name>.<tongue>.py` (e.g. `calculateur.fr.py` or `game.emoji.py`)
2. **File Header Directive (in first 5 lines):**
   ```python
   # tongue: fr
   ```
   or
   ```python
   # coding: parsethon-fr
   ```
