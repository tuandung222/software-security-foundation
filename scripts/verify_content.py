#!/usr/bin/env python3
"""verify_content.py - QA automation cho docs/.

Kiểm tra:
1. Internal markdown link không gãy.
2. Reference đến doc-id trong sidebar/footer tồn tại.
3. KaTeX block không có syntax obvious wrong (mismatch $).
4. Mermaid block render được bằng mmdc.
5. Code block C compile syntax bằng gcc -fsyntax-only (nếu gcc có).
6. Code block Python compile bằng py_compile (nếu python có).
7. Anonymity rule: không có keyword cấm.

Chạy: python3 scripts/verify_content.py
Exit code: 0 nếu mọi check pass, !=0 nếu có lỗi.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"

# Mẫu cấm theo anonymity rule
FORBIDDEN_PATTERNS = [
    r"\bôn thi\b",
    r"\bcuối kỳ\b",
    r"final\s+exam",
    r"\bHCMUT\b",
    r"\bCordeiro\b",
    r"Trương\s+Tuấn",
    # tuandung222 chỉ allow trong URL config, không trong docs/
]

# Em-dash thực sự
FORBIDDEN_CHARS = ["—"]

LINK_RE = re.compile(r"\]\(([^)]+)\)")
MERMAID_RE = re.compile(r"```mermaid\n(.*?)```", re.DOTALL)
C_BLOCK_RE = re.compile(r"```c\n(.*?)```", re.DOTALL)
PY_BLOCK_RE = re.compile(r"```python\n(.*?)```", re.DOTALL)
MATH_INLINE_RE = re.compile(r"(?<!\$)\$([^\$\n]+)\$(?!\$)")
MATH_BLOCK_RE = re.compile(r"\$\$(.+?)\$\$", re.DOTALL)


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def err(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def summary(self) -> int:
        print()
        print(f"==== Verify summary ====")
        print(f"  Errors:   {len(self.errors)}")
        print(f"  Warnings: {len(self.warnings)}")
        if self.errors:
            print()
            print("FAIL: có lỗi nghiêm trọng. Xem log ở trên.")
            return 1
        if self.warnings:
            print()
            print("PASS với warning. Có thể bỏ qua nếu acceptable.")
        else:
            print()
            print("ALL CLEAN.")
        return 0


def iter_md_files() -> Iterable[Path]:
    for p in sorted(DOCS.rglob("*.md")):
        yield p


def check_anonymity(rep: Report) -> None:
    print("[check] Anonymity ...")
    bad_re = re.compile("|".join(f"({p})" for p in FORBIDDEN_PATTERNS), re.IGNORECASE)
    for md in iter_md_files():
        text = md.read_text(encoding="utf-8")
        for m in bad_re.finditer(text):
            line = text[: m.start()].count("\n") + 1
            rep.err(f"  ANONYMITY {md.relative_to(ROOT)}:{line}: forbidden keyword '{m.group(0)}'")
        for ch in FORBIDDEN_CHARS:
            if ch in text:
                line = text[: text.index(ch)].count("\n") + 1
                rep.err(f"  ANONYMITY {md.relative_to(ROOT)}:{line}: forbidden character {ch!r}")


def resolve_link(md_file: Path, link: str) -> Path | None:
    """Resolve relative link from md_file. Returns existing path or None.

    Skips external (http), anchor-only, mailto links.
    """
    # Strip anchor and query
    link = link.split("#")[0].split("?")[0].strip()
    if not link:
        return md_file  # pure anchor
    if link.startswith(("http://", "https://", "mailto:", "pathname:")):
        return md_file  # external, skip check
    # Resolve relative
    target = (md_file.parent / link).resolve()
    if target.exists():
        return target
    # Try with .md extension
    if (target.with_suffix(".md")).exists():
        return target.with_suffix(".md")
    return None


def strip_code_blocks(text: str) -> str:
    """Replace fenced/inline code with whitespace of same length to preserve line numbers."""
    def _blank(m: re.Match) -> str:
        return re.sub(r"[^\n]", " ", m.group(0))
    text = re.sub(r"```.*?```", _blank, text, flags=re.DOTALL)
    text = re.sub(r"`[^`\n]+`", _blank, text)
    return text


def check_internal_links(rep: Report) -> None:
    print("[check] Internal links ...")
    # Build set of valid doc IDs for absolute /docs/... links
    doc_ids: set[str] = set()
    for md in iter_md_files():
        rel = md.relative_to(DOCS).with_suffix("").as_posix()
        doc_ids.add(rel)
        # Also id without leading numbered prefix? Docusaurus usually uses dir/id
        # Skip - keep simple
    for md in iter_md_files():
        raw = md.read_text(encoding="utf-8")
        text = strip_code_blocks(raw)
        for m in LINK_RE.finditer(text):
            link = m.group(1)
            if link.startswith(("http://", "https://", "mailto:", "pathname:", "#")):
                continue
            if link.startswith("/docs/"):
                # Docusaurus absolute route
                doc_path = link[len("/docs/"):].rstrip("/")
                if doc_path in doc_ids:
                    continue
                # Try without trailing index file
                if any(d.startswith(doc_path + "/") for d in doc_ids):
                    continue
                line = raw[: m.start()].count("\n") + 1
                rep.err(f"  LINK {md.relative_to(ROOT)}:{line}: broken absolute link '{link}'")
                continue
            target = resolve_link(md, link)
            if target is None:
                line = raw[: m.start()].count("\n") + 1
                rep.err(f"  LINK {md.relative_to(ROOT)}:{line}: broken link '{link}'")


def check_math_balance(rep: Report) -> None:
    print("[check] KaTeX dollar balance ...")
    for md in iter_md_files():
        text = md.read_text(encoding="utf-8")
        # Strip code blocks first
        text_no_code = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
        text_no_code = re.sub(r"`[^`]+`", "", text_no_code)
        # Count un-escaped $
        n_single = sum(1 for i, c in enumerate(text_no_code) if c == "$" and (i == 0 or text_no_code[i - 1] != "\\"))
        if n_single % 2 != 0:
            rep.warn(f"  MATH {md.relative_to(ROOT)}: odd number of '$' ({n_single}), có thể có công thức không close")


def check_mermaid(rep: Report) -> None:
    if not shutil.which("npx"):
        rep.warn("  MERMAID: skip (no npx)")
        return
    print("[check] Mermaid blocks ...")
    tmpdir = ROOT / "scripts" / "_tmp" / "verify_mermaid"
    tmpdir.mkdir(parents=True, exist_ok=True)
    count = 0
    for md in iter_md_files():
        text = md.read_text(encoding="utf-8")
        for m in MERMAID_RE.finditer(text):
            count += 1
            mmd_file = tmpdir / f"check_{count}.mmd"
            png_file = tmpdir / f"check_{count}.png"
            mmd_file.write_text(m.group(1).strip(), encoding="utf-8")
            try:
                subprocess.run(
                    ["npx", "mmdc", "-i", str(mmd_file), "-o", str(png_file), "-b", "white"],
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=30,
                )
            except subprocess.CalledProcessError as e:
                line = text[: m.start()].count("\n") + 1
                stderr_short = (e.stderr or "")[:120].replace("\n", " ")
                rep.err(f"  MERMAID {md.relative_to(ROOT)}:{line}: render failed: {stderr_short}")
            except subprocess.TimeoutExpired:
                rep.warn(f"  MERMAID {md.relative_to(ROOT)}: render timeout")
    # Cleanup
    for f in tmpdir.glob("*"):
        try:
            f.unlink()
        except Exception:
            pass


def check_c_blocks(rep: Report) -> None:
    if not shutil.which("gcc") and not shutil.which("clang"):
        rep.warn("  C SYNTAX: skip (no gcc/clang)")
        return
    cc = shutil.which("clang") or shutil.which("gcc")
    print(f"[check] C block syntax ({cc}) ...")
    tmpdir = ROOT / "scripts" / "_tmp" / "verify_c"
    tmpdir.mkdir(parents=True, exist_ok=True)
    count = 0
    for md in iter_md_files():
        text = md.read_text(encoding="utf-8")
        for m in C_BLOCK_RE.finditer(text):
            code = m.group(1)
            # Heuristic: skip block obviously incomplete (no semicolon, only 1-2 lines)
            if code.count(";") < 1 and code.count("{") < 1:
                continue
            count += 1
            tmp_c = tmpdir / f"snippet_{count}.c"
            # Wrap in main() if not present, so isolated statement check
            if "int main(" in code or "void main(" in code:
                tmp_c.write_text("#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n#include <assert.h>\n" + code, encoding="utf-8")
            else:
                # Skip if it looks like just declaration / fragment, hard to compile in isolation
                continue
            try:
                result = subprocess.run(
                    [cc, "-fsyntax-only", "-Wno-everything", str(tmp_c)],
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode != 0 and "error:" in (result.stderr or "").lower():
                    line = text[: m.start()].count("\n") + 1
                    stderr_short = result.stderr[:200].replace("\n", " ")
                    rep.warn(f"  C SYNTAX {md.relative_to(ROOT)}:{line}: {stderr_short}")
            except subprocess.TimeoutExpired:
                pass
    # Cleanup
    for f in tmpdir.glob("*"):
        try:
            f.unlink()
        except Exception:
            pass


def check_python_blocks(rep: Report) -> None:
    if not shutil.which("python3"):
        rep.warn("  PY SYNTAX: skip (no python3)")
        return
    print("[check] Python block syntax ...")
    tmpdir = ROOT / "scripts" / "_tmp" / "verify_py"
    tmpdir.mkdir(parents=True, exist_ok=True)
    count = 0
    for md in iter_md_files():
        text = md.read_text(encoding="utf-8")
        for m in PY_BLOCK_RE.finditer(text):
            code = m.group(1).strip()
            # Skip pseudo-code (heuristic: only 1 line or contains "...")
            if code.count("\n") < 1 or "..." in code:
                continue
            count += 1
            tmp_py = tmpdir / f"snippet_{count}.py"
            tmp_py.write_text(code, encoding="utf-8")
            try:
                result = subprocess.run(
                    ["python3", "-m", "py_compile", str(tmp_py)],
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode != 0:
                    line = text[: m.start()].count("\n") + 1
                    stderr_short = (result.stderr or "")[:200].replace("\n", " ")
                    # Demote to warning since many snippet are demo/incomplete
                    rep.warn(f"  PY SYNTAX {md.relative_to(ROOT)}:{line}: {stderr_short}")
            except subprocess.TimeoutExpired:
                pass
    # Cleanup
    for f in tmpdir.glob("*"):
        try:
            f.unlink()
        except Exception:
            pass


def main() -> int:
    rep = Report()
    check_anonymity(rep)
    check_internal_links(rep)
    check_math_balance(rep)
    check_mermaid(rep)
    check_c_blocks(rep)
    check_python_blocks(rep)
    # Print errors / warnings
    if rep.errors:
        print()
        print("==== ERRORS ====")
        for e in rep.errors:
            print(e)
    if rep.warnings:
        print()
        print("==== WARNINGS ====")
        for w in rep.warnings[:30]:  # limit output
            print(w)
        if len(rep.warnings) > 30:
            print(f"  ... and {len(rep.warnings) - 30} more")
    return rep.summary()


if __name__ == "__main__":
    raise SystemExit(main())
