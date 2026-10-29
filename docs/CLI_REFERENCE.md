# Parsethon CLI Reference

The Parsethon CLI tool is exported via [`expose-interface`](https://pypi.org/project/expose-interface/) and registered as the console script `parsethon`.

---

## Global Options

```bash
parsethon [-h] [--help] COMMAND [ARGS...]
```

---

## Commands

### 1. `run`
Executes a Tongue source file directly with the CPython interpreter.

**Usage:**
```bash
parsethon run PATH [--tongue TONGUE]
```

**Arguments:**
- `PATH`: Path to the Tongue script to execute.
- `--tongue` (optional): Name of the Tongue to use. If omitted, inferred from filename or header.

**Example:**
```bash
parsethon run examples/fibonacci.es.py
```

---

### 2. `translate`
Translates source code between a Tongue and canonical Python syntax.

**Usage:**
```bash
parsethon translate PATH [--tongue TONGUE] [--to_python BOOL] [--output FILE]
```

**Arguments:**
- `PATH`: Path to input source file.
- `--tongue` (optional): Name of Tongue.
- `--to_python` (optional, default: `True`): Set to `False` to translate Python -> Tongue.
- `--output` (optional): Destination file path. If omitted, outputs to stdout.

**Examples:**
```bash
# Tongue to Python (to stdout)
parsethon translate script.es.py

# Tongue to Python (to file)
parsethon translate script.es.py --output script.py

# Python to Tongue (to file)
parsethon translate script.py --tongue es --to_python False --output script.es.py
```

---

### 3. `tokenize`
Tokenizes a source file and prints the lexical taxonomy classification and subelement for every token.

**Usage:**
```bash
parsethon tokenize PATH [--verbose BOOL]
```

**Arguments:**
- `PATH`: Path to file to tokenize.
- `--verbose` (optional, default: `False`): Include whitespace and newline trivia tokens.

**Example:**
```bash
parsethon tokenize examples/counter.emoji.py
```

---

### 4. `list-tongues`
Enumerates all registered built-in and loaded Tongues.

**Usage:**
```bash
parsethon list-tongues
```

---

### 5. `check`
Validates that a Tongue file translates to a valid Python AST without executing the code.

**Usage:**
```bash
parsethon check PATH [--tongue TONGUE]
```

**Example:**
```bash
parsethon check examples/fibonacci.es.py
```
