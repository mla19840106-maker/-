"""Regression tests for the offline documentation checker, not for an LLM."""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.validate import (
    REQUIRED_FILES,
    ROOT,
    chinese_number,
    heading_anchors,
    table_errors,
    validate,
    without_fenced_code,
)


class ParserTests(unittest.TestCase):
    def test_chinese_chapter_numbers(self) -> None:
        expected = {1: "一", 10: "十", 11: "十一", 20: "二十", 29: "二十九"}
        for number, label in expected.items():
            self.assertEqual(chinese_number(number), label)
        with self.assertRaises(ValueError):
            chinese_number(30)

    def test_fences_preserve_line_numbers_and_hide_examples(self) -> None:
        clean, unclosed = without_fenced_code("before\n```text\n[bad](missing.md)\n```\nafter\n")
        self.assertEqual(clean, "before\n\n\n\nafter")
        self.assertIsNone(unclosed)

    def test_shorter_fence_does_not_close_block(self) -> None:
        _, unclosed = without_fenced_code("before\n````text\nexample\n```\n")
        self.assertEqual(unclosed, 2)

    def test_chinese_and_duplicate_heading_anchors(self) -> None:
        anchors = heading_anchors("## 第一编 总纲\n## Same title\n## Same title\n")
        self.assertEqual(anchors, {"第一编-总纲", "same-title", "same-title-1"})

    def test_valid_table_with_escaped_pipe(self) -> None:
        text = "| Key | Value |\n| --- | --- |\n| a \\| b | c |\n"
        self.assertEqual(table_errors(text, "sample.md"), [])

    def test_invalid_table_column_count(self) -> None:
        text = "| Key | Value |\n| --- | --- |\n| a |\n"
        self.assertTrue(any("columns" in error for error in table_errors(text, "sample.md")))

    def test_missing_table_separator(self) -> None:
        self.assertTrue(table_errors("| a | b |\n| c | d |\n", "sample.md"))


class RepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix="prompt-docs-test-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        # Copy only deliverables, never .git, private materials, or credentials.
        for name in REQUIRED_FILES:
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)

    def append(self, name: str, text: str) -> None:
        with (self.root / name).open("a", encoding="utf-8") as handle:
            handle.write(text)

    def replace(self, name: str, old: str, new: str) -> None:
        path = self.root / name
        text = path.read_text(encoding="utf-8")
        self.assertIn(old, text)
        path.write_text(text.replace(old, new, 1), encoding="utf-8")

    def test_current_repository_passes(self) -> None:
        self.assertEqual(validate(self.root), [])

    def test_missing_required_file_fails(self) -> None:
        (self.root / "prompts/lite.md").unlink()
        self.assertTrue(any("Missing required file" in item for item in validate(self.root)))

    def test_broken_local_link_fails(self) -> None:
        self.append("README.md", "\n[missing](missing.md)\n")
        self.assertTrue(any("missing link target" in item for item in validate(self.root)))

    def test_missing_heading_anchor_fails(self) -> None:
        self.append("README.md", "\n[missing](prompts/full.md#not-a-heading)\n")
        self.assertTrue(any("missing heading anchor" in item for item in validate(self.root)))

    def test_external_links_are_not_fetched(self) -> None:
        self.append("README.md", "\n[external](https://example.invalid/not-fetched)\n")
        self.assertEqual(validate(self.root), [])

    def test_example_links_in_code_blocks_are_ignored(self) -> None:
        self.append("README.md", "\n```text\n[example](missing.md)\n```\n")
        self.assertEqual(validate(self.root), [])

    def test_links_cannot_escape_repository(self) -> None:
        self.append("README.md", "\n[outside](../outside.md)\n")
        self.assertTrue(any("escapes repository" in item for item in validate(self.root)))

    def test_duplicate_chapter_fails(self) -> None:
        self.replace("prompts/full.md", "### 第七章 ", "### 第六章 ")
        self.assertTrue(any("chapters 1 through 29" in item for item in validate(self.root)))

    def test_missing_vocabulary_table_fails(self) -> None:
        self.replace("prompts/full.md", "#### 表16 ", "#### 表17 ")
        self.assertTrue(any("vocabulary tables" in item for item in validate(self.root)))

    def test_out_of_sync_checklist_fails(self) -> None:
        self.replace("checklists/review-30.md", "文种或材料类型是否准确", "不同步的条目")
        self.assertTrue(any("checklist differs" in item for item in validate(self.root)))

    def test_duplicate_prohibition_number_fails(self) -> None:
        self.replace("prompts/full.md", "20. 不无故推翻", "19. 不无故推翻")
        self.assertTrue(any("prohibitions" in item for item in validate(self.root)))

    def test_missing_manual_case_fails(self) -> None:
        self.replace("tests/acceptance-cases.md", "| T20 |", "| T21 |")
        self.assertTrue(any("manual cases" in item for item in validate(self.root)))

    def test_invalid_utf8_fails(self) -> None:
        (self.root / "README.md").write_bytes(b"\xff\n")
        self.assertTrue(any("invalid UTF-8" in item for item in validate(self.root)))

    def test_conflict_marker_fails(self) -> None:
        self.append("README.md", "\n<<<<<<< HEAD\n")
        self.assertTrue(any("merge conflict marker" in item for item in validate(self.root)))

    def test_unclosed_code_fence_fails(self) -> None:
        self.append("README.md", "\n```text\nnot closed\n")
        self.assertTrue(any("unclosed code fence" in item for item in validate(self.root)))

    def test_private_markdown_is_not_read(self) -> None:
        private = self.root / "private/notes.md"
        private.parent.mkdir()
        private.write_bytes(b"\xff")
        self.assertEqual(validate(self.root), [])


if __name__ == "__main__":
    unittest.main()
