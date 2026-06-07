#!/usr/bin/env python3
"""Check a generated study pack for common unfinished-template issues."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


MIN_FILES = [
    "00-learning-path.md",
    "01-lesson-notes.md",
    "02-active-recall.md",
    "source-map.md",
]
CHECKER_VERSION = "1.3"
FULL_FILES = MIN_FILES + [
    "03-exercises.md",
    "04-glossary.md",
    "05-review-plan.md",
    "06-memory-cards.md",
    "07-code-extracts.md",
]
MAX_MARKDOWN_CHARS = 120_000
MAX_MARKDOWN_LINES = 1800

PLACEHOLDER_PATTERNS = [
    ("placeholder_lo_x", re.compile(r"\bLOx\b")),
    ("placeholder_pdf_page", re.compile(r"\[PDF p\.x\]")),
    ("placeholder_book_page", re.compile(r"\[Book p\.y\]")),
    ("placeholder_section", re.compile(r"\[Section x\]")),
    ("placeholder_can_zh", re.compile(r"能\.\.\.")),
    ("placeholder_can_en", re.compile(r"\bCan\.\.\.")),
    ("blank_table_row", re.compile(r"^\|\s*(\|\s*){2,}$")),
]

BLANK_REQUIRED_LABELS = [
    "题目",
    "标准答案",
    "评分要点",
    "常见错误",
    "来源依据",
    "进一步追问",
    "这一节回答什么问题",
    "先给结论",
    "原文依据",
    "直觉理解",
    "核心机制/展开",
    "为什么这样设计",
    "边界/易错点",
    "最小自测",
    "最小自测参考答案",
    "简单具体例子",
    "提示",
    "最低完成标准",
    "类型",
    "提问",
    "答案",
    "为什么要记",
    "自检标准",
    "答案要点",
    "为什么错",
    "正确说法",
    "重测目标",
    "任务",
    "完成标准",
    "抽取工具",
    "章节定位依据",
    "文本质量",
    "公式限制",
    "表格限制",
    "图示限制",
    "Prompt",
    "Expected answer",
    "Scoring points",
    "Common wrong answer",
    "Source basis",
    "Follow-up",
    "Question this subsection answers",
    "Short conclusion",
    "Source evidence",
    "Intuition",
    "Mechanism / development",
    "Why this design or idea exists",
    "Boundary / common confusion",
    "Minimum self-check",
    "Self-check answer key",
    "Simple concrete example",
    "Hint",
    "Minimum Completion Standard",
    "Type",
    "Answer",
    "Why memorize",
    "Self-check standard",
    "Answer points",
    "Why it is wrong",
    "Correct version",
    "Objectives to retest",
    "Task",
    "Completion standard",
    "Extraction tool",
    "Chapter-boundary evidence",
    "Text quality",
    "Formula limitations",
    "Table limitations",
    "Figure limitations",
]


def add_issue(issues: list[dict[str, Any]], severity: str, code: str, path: Path, line: int, message: str) -> None:
    issues.append(
        {
            "severity": severity,
            "code": code,
            "file": str(path),
            "line": line,
            "message": message,
        }
    )


def scan_placeholders(path: Path, issues: list[dict[str, Any]]) -> None:
    text = path.read_text(encoding="utf-8")
    for index, line in enumerate(text.splitlines(), start=1):
        for code, pattern in PLACEHOLDER_PATTERNS:
            if pattern.search(line):
                add_issue(issues, "warning", code, path, index, "template placeholder appears unfinished")
        stripped = line.strip()
        for label in BLANK_REQUIRED_LABELS:
            if re.match(rf"^[-*]?\s*{re.escape(label)}[：:]\s*$", stripped):
                add_issue(issues, "warning", "blank_required_label", path, index, f"`{label}` is blank")


def check_markdown_size(path: Path, issues: list[dict[str, Any]]) -> None:
    text = path.read_text(encoding="utf-8")
    line_count = text.count("\n") + 1
    if len(text) > MAX_MARKDOWN_CHARS:
        add_issue(
            issues,
            "warning",
            "oversized_markdown_file",
            path,
            1,
            f"file has {len(text)} characters; split long course material into chapter/module packs",
        )
    if line_count > MAX_MARKDOWN_LINES:
        add_issue(
            issues,
            "warning",
            "oversized_markdown_file",
            path,
            1,
            f"file has {line_count} lines; split long course material into chapter/module packs",
        )


def check_chapter_note_contract(root: Path, issues: list[dict[str, Any]]) -> None:
    path = root / "01-lesson-notes.md"
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    required_groups = [
        ("chapter_problem", ("本章解决的问题", "Problem This Chapter Solves")),
        ("conceptual_spine", ("概念主线", "Conceptual Spine")),
        ("closed_loop_subsections", ("小节闭环笔记", "Closed-Loop Subsection Notes")),
        ("concrete_examples", ("简单具体例子", "Simple concrete example")),
        ("minimum_standard", ("最低完成标准", "Minimum Completion Standard")),
    ]
    for code, headings in required_groups:
        if not any(heading in text for heading in headings):
            add_issue(
                issues,
                "warning",
                f"missing_{code}",
                path,
                1,
                f"chapter note is missing required section: {' / '.join(headings)}",
            )


def check_learning_path_contract(root: Path, issues: list[dict[str, Any]]) -> None:
    path = root / "00-learning-path.md"
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    if not any(heading in text for heading in ("章节学习用时表", "Chapter Study Time Table")):
        add_issue(
            issues,
            "warning",
            "missing_study_time_table",
            path,
            1,
            "learning path is missing a per-chapter study time table",
        )


def check_answer_key_contract(root: Path, issues: list[dict[str, Any]]) -> None:
    required = {
        "02-active-recall.md": ("答案区", "Answer Key"),
        "03-exercises.md": ("完整答案与评分标准", "Complete Answers and Scoring"),
    }
    for filename, headings in required.items():
        path = root / filename
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        if not any(heading in text for heading in headings):
            add_issue(
                issues,
                "warning",
                "missing_final_answer_key",
                path,
                1,
                f"{filename} is missing a final answer-key section: {' / '.join(headings)}",
            )


def check_memory_card_contract(root: Path, issues: list[dict[str, Any]], full: bool) -> None:
    path = root / "06-memory-cards.md"
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    required_groups = [
        ("memorization_selection", ("必须记忆项筛选", "Memorization Selection")),
        ("core_cards", ("Core Cards",)),
        ("trap_cards", ("Trap Cards",)),
        ("oral_review", ("3 分钟口头复习", "3-Minute Oral Review")),
    ]
    for code, headings in required_groups:
        if not any(heading in text for heading in headings):
            add_issue(
                issues,
                "warning",
                f"missing_{code}",
                path,
                1,
                f"memory cards file is missing required section: {' / '.join(headings)}",
            )


def check_code_extract_contract(root: Path, issues: list[dict[str, Any]]) -> None:
    path = root / "07-code-extracts.md"
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    required_groups = [
        ("code_index", ("代码索引", "Code Index")),
        ("copyable_code_blocks", ("可复制代码块", "Copyable Code Blocks")),
        ("verification_checklist", ("人工核对清单", "Manual Verification Checklist")),
    ]
    for code, headings in required_groups:
        if not any(heading in text for heading in headings):
            add_issue(
                issues,
                "warning",
                f"missing_{code}",
                path,
                1,
                f"code extracts file is missing required section: {' / '.join(headings)}",
            )


def extract_ids(pattern: str, text: str) -> set[str]:
    return set(re.findall(pattern, text))


def check_objective_mapping(root: Path, issues: list[dict[str, Any]]) -> None:
    path = root / "00-learning-path.md"
    if not path.exists():
        return
    learning_text = path.read_text(encoding="utf-8")
    objectives = extract_ids(r"\bLO\d+\b", learning_text)
    if not objectives:
        add_issue(issues, "warning", "no_learning_objectives", path, 1, "no concrete LO ids found")
        return

    assessment_text = ""
    for filename in ("02-active-recall.md", "03-exercises.md"):
        candidate = root / filename
        if candidate.exists():
            assessment_text += "\n" + candidate.read_text(encoding="utf-8")
    assessed = extract_ids(r"\bLO\d+\b", assessment_text)
    for objective in sorted(objectives - assessed):
        add_issue(
            issues,
            "warning",
            "objective_not_assessed",
            path,
            1,
            f"{objective} does not appear in recall questions or exercises",
        )
    for objective in sorted(assessed - objectives):
        add_issue(
            issues,
            "warning",
            "unknown_objective_reference",
            path,
            1,
            f"{objective} appears in recall/exercises but is not defined in learning objectives",
        )


def check_meta_warnings(root: Path, issues: list[dict[str, Any]]) -> None:
    path = root / "_meta.json"
    if not path.exists():
        return
    try:
        meta = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        add_issue(issues, "warning", "invalid_meta_json", path, 1, f"_meta.json is invalid: {exc}")
        return
    warnings = meta.get("warnings") or []
    if warnings:
        add_issue(
            issues,
            "warning",
            "meta_warnings",
            path,
            1,
            f"_meta.json contains warnings: {', '.join(map(str, warnings))}",
        )


def check_required_files(root: Path, issues: list[dict[str, Any]], full: bool) -> None:
    expected = FULL_FILES if full else MIN_FILES
    for filename in expected:
        path = root / filename
        if not path.exists():
            add_issue(issues, "error", "missing_file", path, 0, f"missing required file: {filename}")


def check_pack(root: Path, full: bool) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    check_required_files(root, issues, full)
    for path in sorted(root.glob("*.md")):
        scan_placeholders(path, issues)
        check_markdown_size(path, issues)
    check_objective_mapping(root, issues)
    check_learning_path_contract(root, issues)
    check_chapter_note_contract(root, issues)
    check_answer_key_contract(root, issues)
    check_memory_card_contract(root, issues, full)
    check_code_extract_contract(root, issues)
    check_meta_warnings(root, issues)

    errors = sum(1 for issue in issues if issue["severity"] == "error")
    warnings = sum(1 for issue in issues if issue["severity"] == "warning")
    return {
        "path": str(root),
        "checker_version": CHECKER_VERSION,
        "full": full,
        "errors": errors,
        "warnings": warnings,
        "issues": issues,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check a Markdown study pack for unfinished fields.")
    parser.add_argument("study_pack", help="Study-pack directory.")
    parser.add_argument("--short", action="store_true", help="Require only short-pack files.")
    parser.add_argument("--strict", action="store_true", help="Deprecated: warnings already fail by default.")
    parser.add_argument("--allow-warnings", action="store_true", help="Exit zero when only warnings are present.")
    parser.add_argument("--json", action="store_true", help="Print JSON report.")
    args = parser.parse_args()

    root = Path(args.study_pack)
    if not root.exists() or not root.is_dir():
        print(f"study pack directory not found: {root}", file=sys.stderr)
        return 2

    report = check_pack(root, full=not args.short)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"errors={report['errors']} warnings={report['warnings']} path={report['path']}")
        for issue in report["issues"]:
            location = f"{issue['file']}:{issue['line']}" if issue["line"] else issue["file"]
            print(f"{issue['severity']} {issue['code']} {location} - {issue['message']}")

    if report["errors"] or (report["warnings"] and not args.allow_warnings):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
