# Parsethon Architectural Deep Dive

Rather than creating a new programming language implementation, Parsethon is a mechanism for expressing Python in multiple syntactic vocabularies while retaining Python's ecosystem and runtime.

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
|  - Stateful string and f-string scanner (PEP 701)       |
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
|  - Semantically correct bidirectional translation       |
|  - Context-aware name resolution & attribute guarding   |
|  - Soft keywords contextual isolation (match, case)     |
|  - Python 3.12+ nested f-string grammar translation     |
|  - Explicit bidirectional SourceMap generation          |
+----------------------------+----------------------------+
                             |
                             v
+---------------------------------------------------------+
|                4. CPython Runtime Engine                |
|  - compile(py_source, filename, 'exec')                 |
|  - exec(code_obj, globals)                              |
|  - SourceMap-guided traceback and SyntaxError mapping   |
+---------------------------------------------------------+
```

---

## 2. Semantically Correct Bidirectional Translation

Unlike standard AST transformers which strip comments, line breaks, and whitespace trivia:
1. Parsethon emits `LexicalToken` objects for code elements alongside `WHITESPACE`, `COMMENT`, and `NEWLINE` trivia tokens.
2. Reconstructing the source via `ParsethonTokenizer.reconstruct(tokens)` guarantees complete fidelity with the original source.
3. Translation achieves **semantically correct bidirectional translation**: converting between Python and Tongue vocabularies with AST equivalence and reversible semantics across all supported constructs.

---

## 3. Contextual Translation Guards & Soft Keywords

Direct regex or string replacements in code cause syntax corruption. Parsethon prevents this through robust context awareness:

### A. String & Comment Isolation
Tokens classified as `STRING` or `COMMENT` are scanned statefully. Escape sequences (even/odd backslashes) are handled with standard CPython semantics. Comments and strings remain verbatim.

### B. Substring & Identifier Protection
Identifiers such as `si_condicion` or `silla` are classified as `ID_STANDARD` and never confused with the keyword `si`. User variables matching builtin names are preserved when assigned or defined.

### C. F-String Expression Parsing (Python 3.12+ PEP 701)
F-strings support arbitrary expressions, internal quotes matching outer delimiters, nested f-strings, format specifiers, and conversion flags.

### D. Attribute Access Guarding
If a token is preceded by `.` (such as `obj.match` or `printer.print`), it is recognized as an attribute access and protected from keyword or builtin substitution.

### E. Soft Keywords Context Resolution (`match`, `case`)
Soft keywords `match` and `case` are only translated when they appear as actual statement headers in pattern matching. User variables (`match = 5`, `case = 10`), kwargs (`func(match=1)`), and function definitions (`def match(case):`) are preserved as ordinary identifiers.

---

## 4. Explicit SourceMap & Error Mapping

During translation, an explicit `SourceMap` tracks every token transformation from original spans to translated spans:
1. When a `SyntaxError` or runtime exception occurs in CPython, `source_map.lookup_original(lineno, col)` maps the exact error coordinates back to the original source.
2. `TongueExecutionError` reports the exact line and position in the developer's Tongue source file.

---

## 5. JavaScript-Style Syntax & Whitespace Indifference Engine

Parsethon v0.3.0 expands the syntax vocabulary with native support for JavaScript-style syntax idioms:

### A. Braces `{ ... }` vs Dictionary/Set Literals
The desugaring pass distinguishes compound block delimiters from dictionary and set literals:
- **Block Braces**: A brace preceded by `)`, statement keywords (`else`, `try`, `finally`), `:`, or statement start position is treated as a block delimiter and desugared into indented suites with `:`.
- **Expression Braces**: A brace preceded by `=`, `+=`, `,`, `(`, `[`, `in`, `return`, `yield`, or arithmetic/assignment operators is preserved as a dictionary or set literal.
- **Empty Blocks**: An empty block `{}` is desugared into `:` followed by `pass`.

### B. Statement Termination via Semicolons `;`
Semicolons are parsed as statement terminators at paren depth 0, allowing multi-statement lines or single-line scripts.

### C. Whitespace Indifference
Python's significant whitespace is synthesized directly from the structural nesting depth of the block braces rather than requiring source indentation. As a result, code may be flat (zero indentation), single-line, or arbitrarily formatted.

### D. Importer & Loader Integration
Modules ending in `.js` or `<module>.js.py` are discovered by `TongueMetaPathFinder` and loaded by `TongueSourceLoader` into valid CPython bytecode with `console` object globals automatically injected.
