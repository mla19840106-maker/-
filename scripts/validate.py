#!/usr/bin/env python3
"""Offline checks for this Markdown prompt repository (Python 3.10+).

No model calls or external URL requests. Passing these checks does not validate
legal advice, document facts, or a model's adherence to the prompts.
"""

from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = (
    "README.md",
    "prompts/full.md",
    "prompts/lite.md",
    "templates/task.md",
    "templates/revision-log.md",
    "checklists/review-30.md",
    "examples/usage.md",
    "docs/revision-notes.md",
    "docs/references.md",
    "tests/acceptance-cases.md",
    "tests/test_validate.py",
    "scripts/validate.py",
    "examples/validate.yml.example",
    ".gitignore",
    ".gitattributes",
)
SKIP_DIRS = {".git", ".venv", "node_modules", "__pycache__", "private", "workpapers"}
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
HEADING = re.compile(r"^ {0,3}#{1,6}\s+(.+?)\s*#*\s*$")
INLINE_LINK = re.compile(r"!?\[[^\]\n]*\]\(([^\s)]+)(?:\s+\"[^\"]*\")?\)")
CONFLICT = re.compile(r"^(?:<{7}|={7}|>{7}|\|{7})(?:\s.*)?$")


def chinese_number(number: int) -> str:
    """The chapter numbers needed here, 1 through 29."""
    digits = "零一二三四五六七八九"
    if not 1 <= number <= 29:
        raise ValueError("Chapter number must be between 1 and 29")
    if number < 10:
        return digits[number]
    tens, units = divmod(number, 10)
    return ("" if tens == 1 else digits[tens]) + "十" + (digits[units] if units else "")


def without_fenced_code(text: str) -> tuple[str, int | None]:
    """Remove code content, preserving line numbers; report an unclosed fence."""
    output: list[str] = []
    opened: tuple[str, int, int] | None = None
    for number, line in enumerate(text.splitlines(), 1):
        match = FENCE.match(line)
        if opened is not None:
            if (
                match
                and match[1][0] == opened[0]
                and len(match[1]) >= opened[1]
                and not match[2].strip()
            ):
                opened = None
            output.append("")
        elif match:
            opened = (match[1][0], len(match[1]), number)
            output.append("")
        else:
            output.append(line)
    return "\n".join(output), opened[2] if opened else None


def heading_anchors(text: str) -> set[str]:
    """GitHub-style slugs for the plain-text headings used in this repo."""
    anchors: set[str] = set()
    for line in text.splitlines():
        match = HEADING.match(line)
        if not match:
            continue
        title = re.sub(r"<[^>]*>", "", match[1]).replace("`", "").lower()
        base = "".join(
            char
            for char in title
            if char in "-_" or unicodedata.category(char)[0] not in "PS"
        )
        base = re.sub(r"\s", "-", base)
        slug = base
        suffix = 0
        while slug in anchors:
            suffix += 1
            slug = f"{base}-{suffix}"
        anchors.add(slug)
    return anchors


def section(text: str, start: str, end: str) -> str:
    """Extract between two full, unique chapter headings."""
    start_match = re.search(rf"^{re.escape(start)}[^\n]*$", text, re.MULTILINE)
    if not start_match:
        raise ValueError(f"Missing heading: {start}")
    end_match = re.search(rf"^{re.escape(end)}[^\n]*$", text[start_match.end():], re.MULTILINE)
    if not end_match:
        raise ValueError(f"Missing heading: {end}")
    return text[start_match.end():start_match.end() + end_match.start()]


def numbered_items(text: str) -> list[tuple[int, str]]:
    return [(int(n), item) for n, item in re.findall(r"^(\d+)\. (.+)$", text, re.MULTILINE)]


def table_errors(text: str, name: str) -> list[str]:
    """Check the explicit pipe tables used here, including their separator row."""
    errors: list[str] = []
    rows: list[tuple[int, list[str]]] = []

    def finish_table() -> None:
        if not rows:
            return
        start, header = rows[0]
        width = len(header)
        if len(rows) < 2 or not all(re.fullmatch(r":?-{3,}:?", cell.strip()) for cell in rows[1][1]):
            errors.append(f"{name}:{start}: table has no valid separator row")
        for line_number, cells in rows[1:]:
            if len(cells) != width:
                errors.append(f"{name}:{line_number}: table has {len(cells)} columns, expected {width}")
        rows.clear()

    for number, line in enumerate(text.splitlines(), 1):
        value = line.strip()
        if value.startswith("|") and value.endswith("|"):
            cells = re.split(r"(?<!\\)\|", value)[1:-1]
            rows.append((number, cells))
        else:
            finish_table()
    finish_table()
    return errors


def validate(root: Path) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    for name in REQUIRED_FILES:
        if not (root / name).is_file():
            errors.append(f"Missing required file: {name}")

    texts: dict[Path, str] = {}
    for path in sorted(root.rglob("*.md")):
        relative = path.relative_to(root)
        if SKIP_DIRS.intersection(relative.parts):
            continue
        name = relative.as_posix()
        if not path.resolve().is_relative_to(root):
            errors.append(f"{name}: file resolves outside repository")
            continue
        raw = path.read_bytes()
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            errors.append(f"{name}: invalid UTF-8 ({exc})")
            continue
        if text.startswith("\ufeff"):
            errors.append(f"{name}: remove UTF-8 BOM")
        if not text.endswith("\n"):
            errors.append(f"{name}: missing final newline")
        if "\r" in text:
            errors.append(f"{name}: use LF line endings")
        for number, line in enumerate(text.splitlines(), 1):
            if line.rstrip() != line:
                errors.append(f"{name}:{number}: trailing whitespace")
            if CONFLICT.match(line):
                errors.append(f"{name}:{number}: possible merge conflict marker")
        clean, unclosed = without_fenced_code(text)
        if unclosed:
            errors.append(f"{name}:{unclosed}: unclosed code fence")
        texts[path.resolve()] = clean
        errors.extend(table_errors(clean, name))

    # Check local inline links only. Code samples and external URLs are not fetched.
    for path, text in texts.items():
        name = path.relative_to(root).as_posix()
        for number, line in enumerate(text.splitlines(), 1):
            for match in INLINE_LINK.finditer(line):
                href = match[1].strip("<>")
                try:
                    url = urlsplit(href)
                except ValueError:
                    errors.append(f"{name}:{number}: malformed link {href}")
                    continue
                if url.scheme or url.netloc:
                    continue
                target = (path.parent / unquote(url.path)).resolve() if url.path else path
                if not target.is_relative_to(root):
                    errors.append(f"{name}:{number}: link escapes repository: {href}")
                elif not target.exists():
                    errors.append(f"{name}:{number}: missing link target: {href}")
                elif url.fragment and target.suffix == ".md":
                    if unquote(url.fragment) not in heading_anchors(texts.get(target, "")):
                        errors.append(f"{name}:{number}: missing heading anchor: {href}")

    full = texts.get(root / "prompts/full.md", "")
    parts = re.findall(r"^## (第[一二三四]编 .+)$", full, re.MULTILINE)
    expected_parts = ["第一编 总纲", "第二编 核心规则", "第三编 场景规则", "第四编 流程与输出"]
    if parts != expected_parts:
        errors.append("prompts/full.md: expected the four parts in order")
    chapters = re.findall(r"^### 第([一二三四五六七八九十]+)章\s", full, re.MULTILINE)
    if chapters != [chinese_number(n) for n in range(1, 30)]:
        errors.append("prompts/full.md: expected chapters 1 through 29 exactly once, in order")
    tables = [int(n) for n in re.findall(r"^#### 表(\d+)\s", full, re.MULTILINE)]
    if tables != list(range(1, 17)):
        errors.append("prompts/full.md: expected vocabulary tables 1 through 16 in order")
    try:
        review = numbered_items(section(full, "### 第二十四章 ", "### 第二十五章 "))
        if [n for n, _ in review] != list(range(1, 31)):
            errors.append("prompts/full.md: review checklist must contain items 1 through 30")
        checklist = texts.get(root / "checklists/review-30.md", "")
        standalone = [(int(n), item) for n, item in re.findall(r"^- \[ \] (\d+)\. (.+)$", checklist, re.MULTILINE)]
        if standalone != review:
            errors.append("checklists/review-30.md: checklist differs from full prompt chapter 24")
        forbidden = numbered_items(section(full, "### 第二十八章 ", "### 第二十九章 "))
        if [n for n, _ in forbidden] != list(range(1, 21)):
            errors.append("prompts/full.md: prohibitions must contain items 1 through 20")
    except ValueError as exc:
        errors.append(str(exc))

    cases = texts.get(root / "tests/acceptance-cases.md", "")
    case_ids = re.findall(r"^\| (T\d{2}) \|", cases, re.MULTILINE)
    if case_ids != [f"T{n:02d}" for n in range(1, 21)]:
        errors.append("tests/acceptance-cases.md: expected manual cases T01 through T20")
    return errors


def main() -> int:
    errors = validate(ROOT)
    if errors:
        print(f"FAIL: {len(errors)} issue(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: required files, UTF-8/LF, fences, tables, local links and anchors")
    print("PASS: 4 parts, 29 chapters, 16 vocabulary tables, 30 synced checks, 20 prohibitions")
    print("PASS: manual acceptance cases T01-T20 are present (model behavior NOT tested)")
    print("NOTE: external links, legal validity, real facts and model behavior require human review")
    return 0


if __name__ == "__main__":
    sys.exit(main())
