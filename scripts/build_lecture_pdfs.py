#!/usr/bin/env python3
"""Build one PDF per lecture cluster from the docs/ markdown files.

Usage:
    python3 scripts/build_lecture_pdfs.py

Output goes to static/pdfs/lectures/. Requires pandoc + xelatex with a Unicode font
(falls back to system default if "Inter" is not installed).
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
OUT_DIR = ROOT / "static" / "pdfs" / "lectures"

# Mapping cluster -> (output filename, ordered list of source markdown files)
CLUSTERS: list[tuple[str, str, list[Path]]] = [
    (
        "Lecture 1-2 - Giới thiệu Software Security",
        "lecture-1-2-full.pdf",
        [
            DOCS / "intro.md",
            DOCS / "01-introduction" / "01-overview.md",
            DOCS / "01-introduction" / "02-cia-and-properties.md",
            DOCS / "01-introduction" / "03-vulnerabilities-catalog.md",
            DOCS / "01-introduction" / "04-web-vulnerabilities.md",
            DOCS / "01-introduction" / "05-formal-verification-intro.md",
            DOCS / "01-introduction" / "06-bmc-and-smt-basics.md",
        ],
    ),
    (
        "Lecture 3 - Static Analysis I (BMC + SMT)",
        "lecture-3-full.pdf",
        [DOCS / "02-static-analysis-i" / f for f in [
            "01-overview.md",
            "02-verification-vs-validation.md",
            "03-state-space-exploration.md",
            "04-sat-and-dpll.md",
            "05-smt-theories.md",
            "06-encoding-numbers-and-floats.md",
            "07-encoding-pointers-and-memory.md",
        ]],
    ),
    (
        "Lecture 4 - Static Analysis II (Concurrency)",
        "lecture-4-full.pdf",
        [DOCS / "03-static-analysis-ii" / f for f in [
            "01-overview.md",
            "02-loop-unwinding-and-safety.md",
            "03-bit-blasting-and-arrays.md",
            "04-concurrency-verification.md",
            "05-context-bounded-analysis.md",
            "06-lazy-vs-schedule-recording.md",
            "07-sequentialization-kiss-lr.md",
        ]],
    ),
    (
        "Lecture 5 - Dynamic Analysis (Testing + Fuzzing)",
        "lecture-5-full.pdf",
        [DOCS / "04-dynamic-analysis" / f for f in [
            "01-overview.md",
            "02-security-testing.md",
            "03-coverage-criteria.md",
            "04-monitoring-ltl-buchi.md",
            "05-fuzzing-basics.md",
            "06-blackbox-grammar-mutation.md",
            "07-whitebox-fuzzing-symbolic.md",
            "08-bmc-for-test-generation.md",
        ]],
    ),
    (
        "Lecture 6 - Case Study (Tư vấn dự án)",
        "lecture-6-case-study-full.pdf",
        [DOCS / "05-case-study" / f for f in [
            "01-overview.md",
            "02-web-saas.md",
            "03-fintech.md",
            "04-iot.md",
            "05-enterprise-cloud.md",
        ]],
    ),
    (
        "Lecture 7 - Topics Bổ sung",
        "lecture-7-additional-topics-full.pdf",
        [DOCS / "06-additional-topics" / f for f in [
            "01-overview.md",
            "02-cryptography-basics.md",
            "03-owasp-top-10.md",
            "04-cbmc-tutorial.md",
            "05-secure-sdlc.md",
        ]],
    ),
    (
        "Lecture 8 - Phân tích Code C C++",
        "lecture-8-code-analysis-full.pdf",
        [DOCS / "07-code-analysis" / f for f in [
            "01-overview.md",
            "02-code-patterns-cluster-1.md",
            "03-code-patterns-cluster-2.md",
            "04-code-patterns-cluster-3.md",
            "05-code-patterns-cluster-4.md",
            "06-exercise-analysis.md",
        ]],
    ),
]

FRONT_MATTER_RE = re.compile(r"^---\n.*?\n---\n", re.DOTALL)
# Strip Docusaurus :::admonition blocks and replace with quote-like blocks
ADMONITION_RE = re.compile(
    r":::(tip|note|warning|info|caution|danger)(?:\s+([^\n]+))?\n(.*?):::",
    re.DOTALL,
)


def strip_frontmatter(text: str) -> str:
    return FRONT_MATTER_RE.sub("", text, count=1)


def transform_admonitions(text: str) -> str:
    def repl(m: re.Match) -> str:
        kind, title, body = m.group(1), m.group(2), m.group(3).strip()
        label = (title or kind.upper()).strip()
        prefix = f"> **{label}**\n>\n"
        body_quoted = "\n".join(("> " + ln if ln else ">") for ln in body.splitlines())
        return prefix + body_quoted
    return ADMONITION_RE.sub(repl, text)


MERMAID_PATTERN = re.compile(r"```mermaid\n(.*?)```", re.DOTALL)
_MERMAID_TMPDIR: Path | None = None
_MERMAID_COUNTER = [0]


def _ensure_mermaid_tmpdir() -> Path:
    global _MERMAID_TMPDIR
    if _MERMAID_TMPDIR is None:
        _MERMAID_TMPDIR = ROOT / "scripts" / "_tmp" / "mermaid_renders"
        _MERMAID_TMPDIR.mkdir(parents=True, exist_ok=True)
    return _MERMAID_TMPDIR


def transform_mermaid(text: str) -> str:
    """Render mermaid blocks to PNG using mmdc, replace block with image ref.

    Requires mmdc (@mermaid-js/mermaid-cli) installed. Falls back to a note if
    rendering fails so the build still produces a PDF.
    """
    tmpdir = _ensure_mermaid_tmpdir()

    def repl(m: re.Match) -> str:
        diagram = m.group(1).strip()
        _MERMAID_COUNTER[0] += 1
        idx = _MERMAID_COUNTER[0]
        mmd_path = tmpdir / f"diagram_{idx:03d}.mmd"
        png_path = tmpdir / f"diagram_{idx:03d}.png"
        mmd_path.write_text(diagram, encoding="utf-8")
        try:
            subprocess.run(
                [
                    "npx",
                    "mmdc",
                    "-i", str(mmd_path),
                    "-o", str(png_path),
                    "-b", "white",
                    "-w", "1400",
                ],
                check=True,
                capture_output=True,
                text=True,
                cwd=ROOT,
            )
            if png_path.exists():
                return f"\n\n![Sơ đồ {idx}]({png_path.as_posix()})\n\n"
        except subprocess.CalledProcessError as e:
            print(f"  WARN mermaid render failed for diagram {idx}: {e.stderr[:200]}", file=sys.stderr)
        return (
            "> *Sơ đồ Mermaid (không render được, xem trên web)*\n```\n"
            + diagram
            + "\n```"
        )

    return MERMAID_PATTERN.sub(repl, text)


def transform_details(text: str) -> str:
    """Convert <details><summary>...</summary> ... </details> to readable Markdown."""
    pattern = re.compile(
        r"<details>\s*<summary>(.*?)</summary>(.*?)</details>",
        re.DOTALL,
    )

    def repl(m: re.Match) -> str:
        summary = m.group(1).strip()
        body = m.group(2).strip()
        return f"\n**{summary}**\n\n{body}\n"

    return pattern.sub(repl, text)


def prepare_markdown(files: list[Path]) -> str:
    parts: list[str] = []
    for f in files:
        if not f.exists():
            print(f"WARN: missing {f}", file=sys.stderr)
            continue
        raw = f.read_text(encoding="utf-8")
        raw = strip_frontmatter(raw)
        raw = transform_admonitions(raw)
        raw = transform_mermaid(raw)
        raw = transform_details(raw)
        parts.append(raw.strip())
    return "\n\n\\newpage\n\n".join(parts)


def build_pdf(title: str, content: str, out_path: Path) -> None:
    print(f"[build] {out_path.name} ...")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # Write combined markdown to a temp file (pandoc needs a file or stdin)
    tmp_md = out_path.with_suffix(".tmp.md")
    header = f"---\ntitle: \"{title}\"\nlang: vi-VN\ngeometry: margin=2cm\nfontsize: 11pt\n---\n\n"
    tmp_md.write_text(header + content, encoding="utf-8")

    # Use xelatex for Unicode; main font defaults to system if specified font missing.
    cmd = [
        "pandoc",
        str(tmp_md),
        "-o", str(out_path),
        "--pdf-engine=xelatex",
        "-V", "mainfont=Helvetica",
        "-V", "monofont=Menlo",
        "-V", "colorlinks=true",
        "-V", "linkcolor=blue",
        "--toc",
        "--toc-depth=2",
        "--highlight-style=tango",
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"  OK {out_path.stat().st_size // 1024} KB")
    except subprocess.CalledProcessError as e:
        print(f"  FAIL: {e.stderr[:500]}", file=sys.stderr)
    finally:
        if tmp_md.exists():
            tmp_md.unlink()


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # Reset mermaid tmpdir each run to avoid stale renders
    tmpdir = ROOT / "scripts" / "_tmp" / "mermaid_renders"
    if tmpdir.exists():
        for f in tmpdir.glob("*"):
            f.unlink()
    for title, filename, files in CLUSTERS:
        content = prepare_markdown(files)
        out = OUT_DIR / filename
        build_pdf(title, content, out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
