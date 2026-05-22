#!/usr/bin/env python3
"""Verify PDF rendering: check currency renders and no tofu."""
from pdfminer.high_level import extract_text
import re
import pathlib
import sys


def main():
    pdf_dir = pathlib.Path(__file__).resolve().parent.parent / "pdfs"

    print("=== Currency render check (lecture-6 case study) ===")
    t = extract_text(str(pdf_dir / "lecture-6-case-study-full.pdf"))
    matches = re.findall(r"\$\d+[KM]?(?:/\w+|\+|-\d+\w*)", t)
    print(f"Found {len(matches)} currency-pattern strings (expected: many).")
    for m in matches[:8]:
        print(f"  OK: {m}")

    print("\n=== Tofu check across all PDFs ===")
    tofu_chars = ["\ufffd", "\u25a1", "\u25fb", "\u2b1c", "\u25fc"]
    total_tofu = 0
    for pdf in sorted(pdf_dir.glob("*-full.pdf")):
        t = extract_text(str(pdf))
        cnt = sum(t.count(c) for c in tofu_chars)
        total_tofu += cnt
        status = "CLEAN" if cnt == 0 else f"TOFU={cnt}"
        print(f"  {pdf.name:50s} {status}")

    print(f"\nTotal tofu chars: {total_tofu}")
    return 1 if total_tofu > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
