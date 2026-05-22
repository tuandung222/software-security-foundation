#!/usr/bin/env python3
"""Extract raw text from lecture PDFs using pdfplumber.

Outputs go to `scripts/_extracted/` (gitignored). Used as raw material to
draft markdown lectures; not committed.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pdfplumber

ROOT = Path(__file__).resolve().parent.parent
PDF_DIR = ROOT / "static" / "pdfs"
OUT_DIR = ROOT / "scripts" / "_extracted"


def extract_one(pdf_path: Path, out_path: Path) -> None:
    print(f"[extract] {pdf_path.name} -> {out_path.relative_to(ROOT)}")
    with pdfplumber.open(pdf_path) as pdf:
        chunks: list[str] = []
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            chunks.append(f"\n\n===== PAGE {i} =====\n{text}")
    out_path.write_text("".join(chunks), encoding="utf-8")
    print(f"  pages: {len(pdf.pages)}  chars: {out_path.stat().st_size}")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pdfs = sorted(PDF_DIR.glob("*.pdf"))
    if not pdfs:
        print(f"No PDFs found under {PDF_DIR}", file=sys.stderr)
        return 1
    for pdf in pdfs:
        out = OUT_DIR / f"{pdf.stem}.txt"
        extract_one(pdf, out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
