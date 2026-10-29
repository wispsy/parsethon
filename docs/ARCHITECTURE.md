# Parsethon Architectural Deep Dive

Parsethon is architected around a layered pipeline separating lexical scanning, token taxonomy classification, dialect translation, and CPython runtime execution.

---

## 1. Pipeline Architecture

```
+---------------------------------------------------------+
|                  Tongue Source Code                     |
+----------------------------+----------------------------+
                             |
                             v
+---------------------------------------------------------+
|                1. Lexical Tokenizer                     |
|  - Multi-char greedy symbol scanner                     |
|  - Extended Unicode & Grapheme cluster matching         |
|  - Trivia extraction (whitespace, comments, newlines)   |
|  - Precise SourceSpan (line, col) tracking              |
+----------------------------+----------------------------+
                             |
                             v
+---------------------------------------------------------+
|                2. Subelement Classifier                 |
|  - TokenCategory (KEYWORD, OPERATOR, LITERAL, etc.)     |
|  - TokenSubelement (KW_CONTROL_FLOW, OP_LOGICAL, etc.)  |
+----------------------------+----------------------------+
                             |
                             v
+---------------------------------------------------------+
|                3. Translation Engine                    |
|  - Token-level replacement via Tongue reverse_map       |
|  - Literal string and comment protection                |
|  - F-string expression isolation and translation        |
|  - Attribute access dot guarding (obj.name)             |
+----------------------------+----------------------------+
                             |
                             v
+---------------------------------------------------------+
|                4. CPython Runtime Engine                |
|  - compile(py_source, filename, 'exec')                 |
|  - exec(code_obj, globals)                              |
|  - Traceback and SyntaxError source location mapping    |
+---------------------------------------------------------+
```

---

## 2. Lossless Trivia and Precision Spans

Unlike standard AST transformers which strip comments, line breaks, and whitespace trivia, Parsethon's tokenizer:
1. Emits `LexicalToken` objects for code elements alongside `WHITESPACE`, `COMMENT`, and `NEWLINE` trivia tokens.
2. Reconstructing the source via `ParsethonTokenizer.reconstruct(tokens)` guarantees `100%` character-for-character fidelity with the original source.
3. Translation modifies only target tokens while leaving all formatting, indentation, and comments intact.

---

## 3. Contextual Translation Guards

Direct regex or string replacements in code often cause catastrophic corruption. Parsethon prevents this through token-level context awareness:

### A. String & Comment Isolation
Tokens classified as `STRING` or `COMMENT` are never translated. A comment `# definir un valor` or a string `"si o no"` remains verbatim.

### B. Substring & Identifier Protection
Identifiers such as `si_condicion` or `silla` are classified as `ID_STANDARD` and never confused with the keyword `si`.

### C. F-String Expression Parsing
In f-strings (e.g. `f"El valor es: {definir_calc(x)} y {Verdadero}"`), literal string parts are protected while embedded `{...}` expressions are recursively tokenized and translated.

### D. Attribute Access Guarding
If a token is preceded by `.` (such as `obj.campo`), it is treated as an attribute access. If the mapped target is a Python keyword that would violate attribute syntax, translation is safely suppressed.

---

## 4. Traceback & Error Mapping

When an exception or `SyntaxError` occurs in CPython during compilation or runtime:
1. The error line number and frame stack are captured.
2. The line number is mapped back to the original Tongue source code file.
3. A `TongueExecutionError` is raised displaying the original Tongue code line, pointing the developer directly to the problem in their native Tongue syntax.
