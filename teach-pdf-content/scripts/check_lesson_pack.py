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
CHECKER_VERSION = "1.1"
FULL_FILES = MIN_FILES + [
    "03-exercises.md",
    "04-glossary.md",
    "05-review-plan.md",
]

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
    check_objective_mapping(root, issues)
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
