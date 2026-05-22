#!/usr/bin/env python3
"""Scan for problematic dollar signs in markdown.

A line is flagged if, after stripping inline code (`...`), code fences,
display-math fences, and escaped `\\$`, it contains an ODD number of `$`.
Such lines confuse KaTeX which expects paired `$...$` for inline math.

Typical false-positive avoidance:
- Skip inside ``` ... ``` fenced blocks.
- Skip inside `$$ ... $$` display math.
- Strip backtick spans before counting (currency in code is fine).
- `\\$` (escaped) does not count.

Run: `python3 scripts/_scan_dollar.py`. Exit code 1 if any flagged.
"""
import re
import sys
import pathlib

docs = pathlib.Path(__file__).resolve().parent.parent / "docs"

flagged: list[tuple[str, int, str]] = []

for f in sorted(docs.rglob("*.md")):
    text = f.read_text(encoding="utf-8")
    in_code = False
    in_math = False
    for ln_num, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code = not in_code
            continue
        if stripped == "$$" or stripped.startswith("$$"):
            # Toggle on a `$$` that opens or closes a display math block.
            # Note: single-line `$$ ... $$` toggles twice; handled below.
            count_dollar_dollar = stripped.count("$$")
            if count_dollar_dollar % 2 == 1:
                in_math = not in_math
            continue
        if in_code or in_math:
            continue
        # Strip inline code spans.
        cleaned = re.sub(r"`[^`]*`", "", line)
        # If $ is escaped, treat as text (remove for analysis).
        cleaned = cleaned.replace(r"\$", "")
        # Currency patterns we want to catch (most common in prose):
        #   $200, $50K, $5-10K, $200/month, $500+, $1, $0.99, $2K-5K
        # Math patterns we want to keep:
        #   $1024$, $-5$, $2^n$, $n+1$, $\frac{a}{b}$, $1/256$
        # Heuristic: currency = `$` followed by digit, followed by a
        # currency-specific suffix (K, M, /word, -, +, space-then-word) or
        # end-of-text; AND not closed by another `$` shortly after.
        currency_pat = re.compile(
            r"\$\d+(?:\.\d+)?[KMB]?"
            r"(?:[+\-]\$?\d|/[a-zA-Z]|K\b|M\b|B\b|\+|\s+(?:tr|tu|cho|per|each|tới|tới|hoặc|và|month|năm|year))"
        )
        if currency_pat.search(cleaned):
            rel = f.relative_to(docs.parent)
            flagged.append((str(rel), ln_num, line.rstrip()))
            continue
        # Also flag lone unbalanced `$` (odd count after stripping inline math).
        # Strip math spans `$...$` where content has `\` or `^` or `_` (likely math).
        cleaned_no_math = re.sub(r"\$[^$\n]*[\\^_{}=][^$\n]*\$", "", cleaned)
        if cleaned_no_math.count("$") % 2 == 1:
            rel = f.relative_to(docs.parent)
            flagged.append((str(rel), ln_num, line.rstrip()))

if not flagged:
    print("OK: no unbalanced $ found in prose.")
    sys.exit(0)

print(f"Found {len(flagged)} line(s) with odd number of unescaped $:")
print("(These confuse KaTeX inline-math parser.)\n")
for path, ln, line in flagged:
    snippet = line if len(line) < 150 else line[:147] + "..."
    print(f"  {path}:{ln}")
    print(f"    {snippet}")
sys.exit(1)
