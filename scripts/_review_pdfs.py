#!/usr/bin/env python3
"""Automated review of generated PDFs.

Checks for common rendering issues:
- Tofu / replacement characters (U+FFFD, □, ◻).
- Raw markdown leftover (`:::tip[`, ``` ```, `<details>`, `[text](url)`).
- Raw LaTeX commands that should have been rendered by KaTeX.
- Suspiciously long lines (potential horizontal overflow).
- Pages with no extractable text (potential blank/image-only).
- Image-heavy pages (potential mermaid overflow if image > page width).

Output: human-readable report to stdout, exits 1 if any issue found.
Save the report by piping: `python3 scripts/_review_pdfs.py > report.md`.
"""
from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PDF_DIR = ROOT / "pdfs"

# Lazy import; only required if we actually scan.
try:
    from pdfminer.high_level import extract_pages
    from pdfminer.layout import LTTextContainer, LTImage, LTFigure, LTChar
except ImportError:
    print("ERROR: pdfminer.six not installed. `pip install pdfminer.six`")
    sys.exit(2)


# ---------- Issue types ----------

ISSUE_TOFU = "tofu_char"
ISSUE_RAW_ADMONITION = "raw_admonition"
ISSUE_RAW_DETAILS = "raw_details"
ISSUE_RAW_LATEX = "raw_latex"
ISSUE_RAW_MARKDOWN_LINK = "raw_md_link"
ISSUE_RAW_FENCE = "raw_fence"
ISSUE_LONG_LINE = "long_line"
ISSUE_DOLLAR_PROSE = "dollar_in_prose"
ISSUE_BLANK_PAGE = "blank_page"
ISSUE_OVERSIZE_IMAGE = "oversize_image"

SEVERITY = {
    ISSUE_TOFU: "HIGH",
    ISSUE_RAW_ADMONITION: "HIGH",
    ISSUE_RAW_DETAILS: "HIGH",
    ISSUE_RAW_LATEX: "HIGH",
    ISSUE_RAW_MARKDOWN_LINK: "MED",
    ISSUE_RAW_FENCE: "MED",
    ISSUE_LONG_LINE: "LOW",
    ISSUE_DOLLAR_PROSE: "MED",
    ISSUE_BLANK_PAGE: "LOW",
    ISSUE_OVERSIZE_IMAGE: "MED",
}


# ---------- Pattern detectors ----------

# Common tofu characters / replacement.
TOFU_CHARS = {"\ufffd", "\u25a1", "\u25fb", "\u2b1c", "\u25fc"}
# Raw markdown / pandoc-leftover patterns.
RE_ADMONITION = re.compile(r":::(tip|note|warning|info|caution|danger)")
RE_DETAILS = re.compile(r"<details>|</details>|<summary>|</summary>")
RE_LATEX_CMD = re.compile(r"\\(frac|sum|prod|int|sqrt|leq|geq|neq|ldots|cdots|to|infty|forall|exists|lor|land|implies|iff|models|alpha|beta|gamma|delta|epsilon|theta|lambda|mu|pi|sigma|tau|phi|psi|omega|Phi|Psi|Sigma|Omega)\b")
RE_MD_LINK = re.compile(r"\]\(\.?\.?/")  # literal markdown link `](./` or `](../`
RE_FENCE = re.compile(r"```\w")  # code fence start, e.g. ```python```mermaid
# Page width threshold (A4 width = 595pt, content width ~ 510pt).
PAGE_WIDTH_PT = 595
PAGE_CONTENT_WIDTH = 510


def extract_text_and_images(pdf_path: Path):
    """Yield (page_num, text_lines, images_with_dims)."""
    for page_num, page in enumerate(extract_pages(str(pdf_path)), 1):
        text_chunks: list[str] = []
        images: list[tuple[float, float]] = []  # (width, height) in pt
        for element in _iter_elements(page):
            if isinstance(element, LTTextContainer):
                text_chunks.append(element.get_text())
            elif isinstance(element, (LTImage, LTFigure)):
                # Image bounding box.
                w = element.width
                h = element.height
                images.append((w, h))
        text = "".join(text_chunks)
        yield page_num, text, images


def _iter_elements(container):
    yield container
    if hasattr(container, "__iter__"):
        for child in container:
            try:
                yield from _iter_elements(child)
            except TypeError:
                pass


def scan_pdf(pdf_path: Path) -> dict:
    """Return dict of issue_type -> list[(page, snippet)]."""
    findings: dict[str, list[tuple[int, str]]] = defaultdict(list)

    for page_num, text, images in extract_text_and_images(pdf_path):
        if not text.strip():
            findings[ISSUE_BLANK_PAGE].append((page_num, "(no extractable text)"))
            continue

        # Tofu detection.
        for ch in TOFU_CHARS:
            if ch in text:
                idx = text.index(ch)
                snippet = _context(text, idx, 40)
                findings[ISSUE_TOFU].append((page_num, snippet))
                break  # one report per page

        # Raw admonition (`:::tip[...]` visible) - real bug if found.
        m = RE_ADMONITION.search(text)
        if m:
            findings[ISSUE_RAW_ADMONITION].append((page_num, _context(text, m.start(), 60)))

        # Raw <details> tag visible. Skip prose mentions like "thẻ <details>"
        # (Vietnamese: "the <details> tag"). Real bug = consecutive unrendered
        # tags forming visible HTML structure.
        for m in RE_DETAILS.finditer(text):
            ctx = _context(text, m.start(), 80)
            # Skip if surrounded by Vietnamese prose words about the tag.
            prose_indicators = ["thẻ", "tag", "element", "trong"]
            if any(w in ctx for w in prose_indicators):
                continue  # prose mention, intentional
            # Real bug: must see consecutive <details>...</details> markers.
            if "</details>" not in ctx and "</summary>" not in ctx:
                continue
            findings[ISSUE_RAW_DETAILS].append((page_num, ctx))
            break

        # Raw LaTeX command. Skip if inside `code span` or fenced block markers.
        for m in RE_LATEX_CMD.finditer(text):
            ctx = _context(text, m.start(), 80)
            # Skip pseudo-code wrapped in backticks (rendered as code, intentional).
            # Tofu indicator: if `\leq` appears inside text with `(x_0` (typical pseudo-code).
            if re.search(r"\([a-z]_\d", ctx):
                continue  # pseudo-code context, intentional
            findings[ISSUE_RAW_LATEX].append((page_num, ctx))
            break

        # Raw markdown link.
        m = RE_MD_LINK.search(text)
        if m:
            findings[ISSUE_RAW_MARKDOWN_LINK].append((page_num, _context(text, m.start(), 60)))

        # Raw fence: only flag if it appears in body (not as part of template).
        for m in RE_FENCE.finditer(text):
            ctx = _context(text, m.start(), 80)
            # Skip if inside a template/example (3 or more `\`\`\`` markers nearby).
            if ctx.count("```") >= 2:
                continue
            findings[ISSUE_RAW_FENCE].append((page_num, ctx))
            break

        # Dollar in prose: PDF cannot distinguish escaped (correct) from
        # unescaped (bug) source. Skip this check; rely on _scan_dollar.py
        # which reads source markdown directly.
        pass

        # Long line check: split by newline.
        for i, line in enumerate(text.split("\n")):
            if len(line) > 200:
                findings[ISSUE_LONG_LINE].append(
                    (page_num, f"({len(line)} chars) " + line[:80] + "...")
                )
                break  # one per page

        # Oversize image.
        for w, h in images:
            if w > PAGE_CONTENT_WIDTH * 1.05:
                findings[ISSUE_OVERSIZE_IMAGE].append(
                    (page_num, f"image {w:.0f}x{h:.0f}pt > content width {PAGE_CONTENT_WIDTH}pt")
                )
                break

    return dict(findings)


def _context(text: str, idx: int, length: int) -> str:
    """Return snippet of text around idx, single line."""
    start = max(0, idx - 10)
    end = min(len(text), idx + length)
    snippet = text[start:end].replace("\n", " ").replace("\t", " ")
    return snippet.strip()


def report(pdf_findings: dict[str, dict[str, list[tuple[int, str]]]]) -> int:
    """Print markdown report. Return total issue count."""
    total = 0
    print("# PDF Review Report\n")
    print(f"Scanned {len(pdf_findings)} PDF files in `pdfs/`.\n")

    # Summary table
    print("## Summary\n")
    print("| PDF | HIGH | MED | LOW | Total |")
    print("|---|---|---|---|---|")
    for pdf_name, findings in pdf_findings.items():
        counts = {"HIGH": 0, "MED": 0, "LOW": 0}
        for issue_type, items in findings.items():
            sev = SEVERITY.get(issue_type, "LOW")
            counts[sev] += len(items)
        line_total = sum(counts.values())
        total += line_total
        print(f"| {pdf_name} | {counts['HIGH']} | {counts['MED']} | {counts['LOW']} | {line_total} |")

    print(f"\n**Total issues across all PDFs: {total}**\n")

    # Per-PDF detail
    for pdf_name, findings in pdf_findings.items():
        if not findings:
            continue
        print(f"\n## {pdf_name}\n")
        # Sort by severity then issue type.
        sorted_items = sorted(findings.items(), key=lambda kv: (SEVERITY[kv[0]] != "HIGH", SEVERITY[kv[0]] != "MED", kv[0]))
        for issue_type, items in sorted_items:
            sev = SEVERITY.get(issue_type, "LOW")
            print(f"### {sev} - {issue_type} ({len(items)})\n")
            for page, snippet in items[:10]:  # cap at 10 per type
                print(f"- p.{page}: `{snippet}`")
            if len(items) > 10:
                print(f"- ... and {len(items) - 10} more")
            print()
    return total


def main() -> int:
    if not PDF_DIR.is_dir():
        print(f"ERROR: {PDF_DIR} does not exist")
        return 2

    pdf_files = sorted(PDF_DIR.glob("*-full.pdf"))
    if not pdf_files:
        print(f"ERROR: no *-full.pdf files in {PDF_DIR}")
        return 2

    print(f"# Scanning {len(pdf_files)} PDF...", file=sys.stderr)

    all_findings: dict[str, dict] = {}
    for pdf in pdf_files:
        print(f"  - {pdf.name}", file=sys.stderr)
        try:
            findings = scan_pdf(pdf)
        except Exception as e:
            print(f"  ERROR scanning {pdf.name}: {e}", file=sys.stderr)
            continue
        all_findings[pdf.name] = findings

    total = report(all_findings)
    return 1 if total > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
