# Parsethon 🐍🗣️

**Parsethon** is an extensible Python lexical parser, tokenization engine, and language translation system.

It enables developers to:
1. **Tokenize** Python source code with fine-grained lexical classification and subelement taxonomy (keywords, operators, delimiters, literals, trivia, and spans).
2. **Define a "Tongue"**: A declarative mapping of replacement keywords, operators, literals, and built-ins.
3. **Losslessly Translate**: Convert source code written in a Tongue back to standard canonical Python syntax (and vice-versa).
4. **Execute under CPython**: Run Tongue source files directly with standard CPython runtime semantics and mapped tracebacks.
5. **Import Seamlessly**: Import `.tongue.py` modules directly via Python's `sys.meta_path` loader or codec hook (`# coding: parsethon-<tongue>`).

Built with **zero third-party dependencies** beyond the in-house CLI interface library [`expose-interface`](https://pypi.org/project/expose-interface/).

---

## Installation

Using `uv`:
```bash
uv add parsethon
```

Using `pip`:
```bash
pip install parsethon
```

---

## Quickstart

### 1. Command Line Interface (powered by `expose-interface`)

Parsethon exports a unified CLI tool:

#### List available Tongues
```bash
parsethon list-tongues
```
Output:
```
Available Tongues:
  * emoji      (v1.0.0): Iconic Emoji Python Tongue [def->🔨, return->📦, if->❓...]
  * es         (v1.0.0): Spanish language Python Tongue [def->definir, return->retornar, if->si...]
  * pirate     (v1.0.0): Swashbuckling Pirate Python Tongue [def->chart, return->booty, if->perchance...]
```

#### Run a Tongue file
```bash
parsethon run examples/fibonacci.es.py
```

#### Translate Tongue code to Python
```bash
parsethon translate examples/fibonacci.es.py --output fibonacci.py
```

#### Inspect Token Breakdown
```bash
parsethon tokenize examples/counter.emoji.py
```

#### Validate Syntax
```bash
parsethon check examples/fibonacci.es.py
```

---

## 2. Python API

### Tokenizing Code with Subelement Taxonomy
```python
from parsethon import ParsethonTokenizer

code = "def add(x: int, y: int) -> int:\n    return x + y\n"
tokenizer = ParsethonTokenizer(code)
tokens = tokenizer.tokenize()

for token in tokens:
    if token.category.value not in ("whitespace", "newline"):
        print(f"{token.span}: {token.category.value} ({token.subelement.value}) -> {token.value}")
```

### Defining a Custom Tongue
```python
from parsethon import Tongue, registry

# Create a Latin Tongue
latin = Tongue(
    name="la",
    version="1.0.0",
    description="Latin Python Tongue",
    keywords={
        "def": "definire",
        "return": "reddere",
        "if": "si",
        "else": "aliter",
        "while": "dum",
        "for": "pro",
        "in": "in",
    },
    constants={
        "True": "Verum",
        "False": "Falsum",
        "None": "Nihil",
    },
    builtins={
        "print": "scribere",
    },
)

# Register it
registry.register(latin)
```

### Translating Between Tongue and Python
```python
from parsethon import translate_to_python, translate_from_python

latin_code = """
definire addere(a, b):
    si a > 0:
        reddere a + b
    aliter:
        reddere b
"""

py_code = translate_to_python(latin_code, "la")
print(py_code)
# Output:
# def addere(a, b):
#     if a > 0:
#         return a + b
#     else:
#         return b
```

### Direct CPython Execution
```python
from parsethon import execute

scope = execute(latin_code, tongue="la")
# Functions and variables are ready in scope!
```

### Seamless Module Imports
```python
import parsethon

# Enable Tongue import hooks
parsethon.enable()

# Directly import foo.es.py or foo.emoji.py!
import my_spanish_module
my_spanish_module.saludar("Mundo")
```

---

## Architecture & Documentation

- [Implementation Plan](../../Docs/parsethon/IMPLEMENTATION_PLAN.md)
- [Tongue Authoring Guide](../../Docs/parsethon/TONGUE_AUTHORING_GUIDE.md)
- [Architecture Deep Dive](../../Docs/parsethon/ARCHITECTURE.md)
- [CLI Reference](../../Docs/parsethon/CLI_REFERENCE.md)

---

## License

MIT
