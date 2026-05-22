#!/usr/bin/env python3
"""Convert Docusaurus admonition titles from old syntax to new bracket syntax.

Old: ':::tip Phép loại suy'
New: ':::tip[Phép loại suy]'

Docusaurus 3.4+ requires the bracket syntax for titles.
"""
import re
import pathlib

ADMON_RE = re.compile(
    r"^(:::(tip|note|warning|info|caution|danger))\s+(.+?)\s*$",
    re.MULTILINE,
)


def main():
    root = pathlib.Path("docs")
    total = 0
    for f in root.rglob("*.md"):
        text = f.read_text(encoding="utf-8")
        new_text, n = ADMON_RE.subn(
            lambda m: f"{m.group(1)}[{m.group(3)}]", text
        )
        if n > 0:
            f.write_text(new_text, encoding="utf-8")
            total += n
            print(f"{f}: {n} admonition(s) fixed")
    print(f"\nTotal admonitions fixed: {total}")


if __name__ == "__main__":
    main()
