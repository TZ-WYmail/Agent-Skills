#!/usr/bin/env python3
"""Check a vNext lesson pack for missing structure or unfinished placeholders."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


CHECKER_VERSION = "3.0"
REQUIRED_FILES = [
    "detailed-notes.md",
    "practice.md",
    "review-notes.md",
    "knowledge-map.json",
    "knowledge-pages.json",
    "source-map.md",
    "_meta.json",
]


def add_issue(issues: list[dict[str, object]], severity: str, code: str, file: str, message: str) -> None:
    issues.append({"severity": severity, "code": code, "file": file, "message": message})


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def check_required_files(root: Path, issues: list[dict[str, object]]) -> None:
    for name in REQUIRED_FILES:
        if not (root / name).exists():
            add_issue(issues, "error", "missing_file", name, f"missing required file: {name}")


def check_placeholders(name: str, text: str, issues: list[dict[str, object]]) -> None:
    patterns = [
        (r"\bLOx\b", "placeholder_lo"),
        (r"\[PDF p\.x\]", "placeholder_pdf_page"),
        (r"\bKP-x\b", "placeholder_kp"),
    ]
    for pattern, code in patterns:
        if re.search(pattern, text):
            add_issue(issues, "warning", code, name, "unfinished placeholder found")


def check_detailed_notes(path: Path, issues: list[dict[str, object]]) -> None:
    text = read_text(path)
    required = [
        "这章解决什么问题",
        "本章知识地图",
        "建议学习路径",
        "起步例子",
        "本章主线",
        "本节主问题",
        "本节知识点",
        "为什么成立",
        "过程追踪 / Trace",
        "本节闭卷输出模板",
        "10 分钟速读路线",
    ]
    for item in required:
        if item not in text:
            add_issue(issues, "warning", "missing_section", path.name, f"missing required section or marker: {item}")
    check_placeholders(path.name, text, issues)


def check_practice(path: Path, issues: list[dict[str, object]]) -> None:
    text = read_text(path)
    required = [
        "知识点与题目映射",
        "闭卷解释题",
        "判断与辨析题",
        "过程追踪题",
        "完整答案与评分点",
    ]
    for item in required:
        if item not in text:
            add_issue(issues, "warning", "missing_section", path.name, f"missing required section: {item}")
    if "标准答案：" in text and text.find("标准答案：") < text.find("完整答案与评分点"):
        add_issue(issues, "warning", "answer_leak", path.name, "answer content appears before final answer section")
    check_placeholders(path.name, text, issues)


def check_review(path: Path, issues: list[dict[str, object]]) -> None:
    text = read_text(path)
    required = [
        "本章 3 分钟回忆路线",
        "本章 10 分钟复习路线",
        "口头复述模板",
        "错题回炉规则",
        "分日复习计划",
    ]
    for item in required:
        if item not in text:
            add_issue(issues, "warning", "missing_section", path.name, f"missing required section: {item}")
    check_placeholders(path.name, text, issues)


def check_source_map(path: Path, issues: list[dict[str, object]]) -> None:
    text = read_text(path)
    required = ["提取记录", "关键结论依据", "提取质量"]
    for item in required:
        if item not in text:
            add_issue(issues, "warning", "missing_section", path.name, f"missing required section: {item}")


def check_knowledge_map(path: Path, issues: list[dict[str, object]]) -> None:
    try:
        data = json.loads(read_text(path))
    except json.JSONDecodeError as exc:
        add_issue(issues, "error", "invalid_json", path.name, f"invalid JSON: {exc}")
        return
    for key in ("chapter_id", "chapter_title", "recommended_paths", "nodes", "edges"):
        if key not in data:
            add_issue(issues, "warning", "missing_key", path.name, f"missing top-level key: {key}")


def check_knowledge_pages(path: Path, issues: list[dict[str, object]]) -> None:
    try:
        data = json.loads(read_text(path))
    except json.JSONDecodeError as exc:
        add_issue(issues, "error", "invalid_json", path.name, f"invalid JSON: {exc}")
        return
    for key in ("chapter_id", "chapter_title", "pages"):
        if key not in data:
            add_issue(issues, "warning", "missing_key", path.name, f"missing top-level key: {key}")
    pages = data.get("pages")
    if not isinstance(pages, list) or not pages:
        add_issue(issues, "warning", "missing_pages", path.name, "knowledge-pages.json should contain at least one page scaffold")
        return
    first = pages[0]
    if not isinstance(first, dict):
        add_issue(issues, "warning", "invalid_page", path.name, "first page entry should be an object")
        return
    for key in ("page_id", "knowledge_point_id", "title", "learning_goal", "entry_question", "page_summary", "blocks"):
        if key not in first:
            add_issue(issues, "warning", "missing_page_key", path.name, f"page is missing key: {key}")
    blocks = first.get("blocks")
    if not isinstance(blocks, list) or not blocks:
        add_issue(issues, "warning", "missing_blocks", path.name, "page should contain at least one block")


def check_meta(path: Path, issues: list[dict[str, object]]) -> None:
    try:
        data = json.loads(read_text(path))
    except json.JSONDecodeError as exc:
        add_issue(issues, "error", "invalid_json", path.name, f"invalid JSON: {exc}")
        return
    if data.get("output_format") != "vnext":
        add_issue(issues, "warning", "wrong_output_format", path.name, "output_format should be `vnext`")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check a vNext lesson pack.")
    parser.add_argument("study_pack", help="Study-pack directory.")
    parser.add_argument("--json", action="store_true", help="Print a JSON report.")
    parser.add_argument("--allow-warnings", action="store_true", help="Exit zero when only warnings are present.")
    args = parser.parse_args()

    root = Path(args.study_pack)
    if not root.exists() or not root.is_dir():
        print(f"study pack directory not found: {root}", file=sys.stderr)
        return 2

    issues: list[dict[str, object]] = []
    check_required_files(root, issues)

    if (root / "detailed-notes.md").exists():
        check_detailed_notes(root / "detailed-notes.md", issues)
    if (root / "practice.md").exists():
        check_practice(root / "practice.md", issues)
    if (root / "review-notes.md").exists():
        check_review(root / "review-notes.md", issues)
    if (root / "source-map.md").exists():
        check_source_map(root / "source-map.md", issues)
    if (root / "knowledge-map.json").exists():
        check_knowledge_map(root / "knowledge-map.json", issues)
    if (root / "knowledge-pages.json").exists():
        check_knowledge_pages(root / "knowledge-pages.json", issues)
    if (root / "_meta.json").exists():
        check_meta(root / "_meta.json", issues)

    errors = sum(1 for issue in issues if issue["severity"] == "error")
    warnings = sum(1 for issue in issues if issue["severity"] == "warning")
    report = {
        "path": str(root),
        "checker_version": CHECKER_VERSION,
        "errors": errors,
        "warnings": warnings,
        "issues": issues,
    }

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"errors={errors} warnings={warnings} path={root}")
        for issue in issues:
            print(f"{issue['severity']} {issue['code']} {issue['file']} - {issue['message']}")

    if errors or (warnings and not args.allow_warnings):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
