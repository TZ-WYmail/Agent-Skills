#!/usr/bin/env python3
"""Check a vNext lesson pack for missing structure or unfinished placeholders."""

from __future__ import annotations

import argparse
from difflib import SequenceMatcher
import json
import re
import sys
from pathlib import Path


CHECKER_VERSION = "3.1"
REQUIRED_FILES = [
    "detailed-notes.md",
    "practice.md",
    "review-notes.md",
    "knowledge-map.json",
    "knowledge-pages.json",
    "source-map.md",
    "_meta.json",
]

PAGE_KIND_VALUES = {
    "concept",
    "representation",
    "procedure",
    "comparison",
    "principle",
    "formula",
    "implementation",
}
TEACHING_PROFILE_VALUES = {"lite", "standard", "deep"}
CLARITY_RISK_VALUES = {"low", "medium", "high"}
TYPE_TO_PAGE_KIND = {
    "concept_explanation": "concept",
    "representation_explanation": "representation",
    "procedure_explanation": "procedure",
    "comparison_explanation": "comparison",
    "principle_explanation": "principle",
    "formula_explanation": "formula",
    "implementation_bridge": "implementation",
}
PLACEHOLDER_MARKERS = (
    "TODO",
    "TBD",
    "LOx",
    "KP-x",
    "待补充",
    "待补",
    "未完成",
    "placeholder",
)


def add_issue(issues: list[dict[str, object]], severity: str, code: str, file: str, message: str) -> None:
    issues.append({"severity": severity, "code": code, "file": file, "message": message})


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def flatten_content(content: object) -> str:
    if isinstance(content, list):
        return "\n".join(flatten_content(item) for item in content)
    if isinstance(content, dict):
        return "\n".join(flatten_content(value) for value in content.values())
    return str(content or "")


def normalized_text(text: object) -> str:
    value = str(text or "").strip().lower()
    value = re.sub(r"\s+", "", value)
    return value


def similarity(a: object, b: object) -> float:
    left = normalized_text(a)
    right = normalized_text(b)
    if not left or not right:
        return 0.0
    return SequenceMatcher(None, left, right).ratio()


def nonempty_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    result: list[str] = []
    for item in value:
        text = str(item or "").strip()
        if text:
            result.append(text)
    return result


def has_placeholder_marker(text: object) -> bool:
    value = str(text or "")
    return any(marker.lower() in value.lower() for marker in PLACEHOLDER_MARKERS)


def is_meaningful_text(text: object, min_chars: int) -> bool:
    value = normalized_text(text)
    return len(value) >= min_chars and not has_placeholder_marker(text)


def contains_any(text: object, patterns: list[str]) -> bool:
    value = str(text or "")
    return any(re.search(pattern, value, re.IGNORECASE) for pattern in patterns)


def contains_any_literal(text: object, terms: list[str]) -> bool:
    value = str(text or "").lower()
    return any(str(term).lower() in value for term in terms)


def has_concrete_marker(text: object) -> bool:
    return contains_any(
        text,
        [
            r"[0-9A-Za-z]",
            r"```",
            r"->|=>|→",
            r"\|",
            r"例如|比如|设|若|假设|输入|输出|顶点|边|数组|队列|栈",
            r"example|input|output|array|queue|stack|graph|node|edge",
        ],
    )


def has_step_marker(text: object) -> bool:
    return contains_any(
        text,
        [
            r"(^|\n)\s*(\d+\.\s|-\s)",
            r"->|=>|→",
            r"\|",
            r"先|再|然后|最后|步骤|第.+步",
            r"first|then|next|finally|step",
        ],
    )


def has_table_marker(text: object) -> bool:
    value = str(text or "")
    return "|" in value and "---" in value


def effective_page_kind(page: dict[str, object]) -> str:
    page_kind = str(page.get("page_kind") or "").strip().lower()
    if page_kind:
        return page_kind
    page_type = str(page.get("type") or "").strip().lower()
    return TYPE_TO_PAGE_KIND.get(page_type, "")


def effective_teaching_profile(page: dict[str, object]) -> str:
    profile = str(page.get("teaching_profile") or "").strip().lower()
    if profile:
        return profile
    complexity = str(page.get("complexity_level") or "").strip().upper()
    if complexity in {"C3", "C4"}:
        return "deep"
    return "standard"


def effective_clarity_risk(page: dict[str, object]) -> str:
    risk = str(page.get("clarity_risk") or "").strip().lower()
    if risk:
        return risk
    importance = str(page.get("importance_level") or "").strip().lower()
    return "high" if importance == "high" else "medium"


def block_text_map(page: dict[str, object]) -> dict[str, str]:
    result: dict[str, str] = {}
    blocks = page.get("blocks")
    if not isinstance(blocks, list):
        return result
    for block in blocks:
        if not isinstance(block, dict):
            continue
        block_type = str(block.get("type") or "").strip()
        if not block_type or block_type in result:
            continue
        result[block_type] = flatten_content(block.get("content"))
    return result


def required_page_blocks(page: dict[str, object]) -> set[str]:
    page_kind = effective_page_kind(page)
    profile = effective_teaching_profile(page)
    clarity_risk = effective_clarity_risk(page)
    complexity = str(page.get("complexity_level") or "").strip().upper()

    required = {"hook", "formal_statement", "minimum_example", "confusion_fix", "recap"}
    if profile in {"standard", "deep"} or clarity_risk == "high":
        required.add("closed_book_retell")

    if page_kind in {"procedure", "principle", "formula"}:
        required.update({"why_it_holds", "trace"})
    if page_kind == "comparison":
        required.add("comparison")
    if page_kind in {"representation", "implementation"}:
        required.add("implementation_bridge")
    if profile == "deep" or complexity in {"C3", "C4"}:
        required.update({"why_it_holds", "trace", "closed_book_retell"})
    if page_kind == "concept" and clarity_risk == "high":
        required.add("why_it_holds")

    return required


def page_label(page: dict[str, object], index: int) -> str:
    page_id = str(page.get("page_id") or f"page-{index + 1}")
    title = str(page.get("title") or "").strip()
    return f"{page_id}{' ' + title if title else ''}"


def normalize_requested_page_ids(values: list[str] | None) -> set[str]:
    result: set[str] = set()
    for value in values or []:
        for item in str(value or "").split(","):
            text = item.strip()
            if text:
                result.add(text)
    return result


def page_identity_set(page: dict[str, object]) -> set[str]:
    identities = {
        str(page.get("page_id") or "").strip(),
        str(page.get("knowledge_point_id") or "").strip(),
    }
    return {item for item in identities if item}


def add_page_issue(
    issues: list[dict[str, object]],
    severity: str,
    code: str,
    file: str,
    page: dict[str, object],
    index: int,
    message: str,
) -> None:
    add_issue(issues, severity, code, file, f"{page_label(page, index)} - {message}")


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


def check_knowledge_pages(
    path: Path,
    issues: list[dict[str, object]],
    selected_page_ids: set[str] | None = None,
) -> set[str]:
    try:
        data = json.loads(read_text(path))
    except json.JSONDecodeError as exc:
        add_issue(issues, "error", "invalid_json", path.name, f"invalid JSON: {exc}")
        return set()
    for key in ("chapter_id", "chapter_title", "pages"):
        if key not in data:
            add_issue(issues, "warning", "missing_key", path.name, f"missing top-level key: {key}")
    pages = data.get("pages")
    if not isinstance(pages, list) or not pages:
        add_issue(issues, "warning", "missing_pages", path.name, "knowledge-pages.json should contain at least one page scaffold")
        return set()
    page_ids: set[str] = set()
    kp_ids: set[str] = set()
    matched_page_ids: set[str] = set()
    for index, page in enumerate(pages):
        if not isinstance(page, dict):
            add_issue(issues, "warning", "invalid_page", path.name, f"page #{index + 1} entry should be an object")
            continue

        page_identity = page_identity_set(page)
        if selected_page_ids and page_identity.isdisjoint(selected_page_ids):
            continue
        matched_page_ids.update(page_identity & selected_page_ids if selected_page_ids else page_identity)

        for key in (
            "page_id",
            "knowledge_point_id",
            "title",
            "learning_goal",
            "entry_question",
            "page_summary",
            "blocks",
        ):
            if key not in page:
                add_page_issue(issues, "warning", "missing_page_key", path.name, page, index, f"missing key: {key}")

        page_id = str(page.get("page_id") or "").strip()
        kp_id = str(page.get("knowledge_point_id") or "").strip()
        if page_id:
            if page_id in page_ids:
                add_page_issue(issues, "warning", "duplicate_page_id", path.name, page, index, "duplicate page_id")
            page_ids.add(page_id)
        if kp_id:
            if kp_id in kp_ids:
                add_page_issue(issues, "warning", "duplicate_knowledge_point_id", path.name, page, index, "duplicate knowledge_point_id")
            kp_ids.add(kp_id)

        page_kind = effective_page_kind(page)
        if not page_kind:
            add_page_issue(issues, "warning", "missing_page_kind", path.name, page, index, "missing page_kind or unmapped type")
        elif page_kind not in PAGE_KIND_VALUES:
            add_page_issue(issues, "warning", "invalid_page_kind", path.name, page, index, f"unsupported page_kind: {page_kind}")

        teaching_profile = effective_teaching_profile(page)
        if teaching_profile not in TEACHING_PROFILE_VALUES:
            add_page_issue(
                issues,
                "warning",
                "invalid_teaching_profile",
                path.name,
                page,
                index,
                f"unsupported teaching_profile: {teaching_profile}",
            )

        clarity_risk = effective_clarity_risk(page)
        if clarity_risk not in CLARITY_RISK_VALUES:
            add_page_issue(
                issues,
                "warning",
                "invalid_clarity_risk",
                path.name,
                page,
                index,
                f"unsupported clarity_risk: {clarity_risk}",
            )

        must_answer = nonempty_list(page.get("must_answer"))
        exit_outcomes = nonempty_list(page.get("exit_outcomes"))
        if not must_answer:
            add_page_issue(issues, "warning", "missing_must_answer", path.name, page, index, "page should declare `must_answer`")
        elif len(must_answer) < 2 and teaching_profile in {"standard", "deep"}:
            add_page_issue(
                issues,
                "warning",
                "thin_must_answer",
                path.name,
                page,
                index,
                "standard/deep page should usually declare at least 2 must-answer questions",
            )
        if not exit_outcomes:
            add_page_issue(issues, "warning", "missing_exit_outcomes", path.name, page, index, "page should declare `exit_outcomes`")

        failure_signals = nonempty_list(page.get("failure_signals"))
        if teaching_profile == "deep" and not failure_signals:
            add_page_issue(
                issues,
                "warning",
                "missing_failure_signals",
                path.name,
                page,
                index,
                "deep page should define `failure_signals` for teaching review",
            )

        if not is_meaningful_text(page.get("learning_goal"), 12):
            add_page_issue(issues, "warning", "thin_learning_goal", path.name, page, index, "learning_goal is too short or placeholder-like")
        if not is_meaningful_text(page.get("entry_question"), 10):
            add_page_issue(issues, "warning", "thin_entry_question", path.name, page, index, "entry_question is too short or placeholder-like")
        if not is_meaningful_text(page.get("page_summary"), 18):
            add_page_issue(issues, "warning", "thin_page_summary", path.name, page, index, "page_summary is too short or placeholder-like")

        title = str(page.get("title") or "")
        entry_question = str(page.get("entry_question") or "")
        page_summary = str(page.get("page_summary") or "")
        if similarity(title, entry_question) >= 0.82:
            add_page_issue(
                issues,
                "warning",
                "lazy_entry_question",
                path.name,
                page,
                index,
                "entry_question is too similar to the title; it should expose a learner doubt or task",
            )
        if similarity(title, page_summary) >= 0.82:
            add_page_issue(
                issues,
                "warning",
                "lazy_page_summary",
                path.name,
                page,
                index,
                "page_summary is too similar to the title; it should summarize the mechanism or conclusion",
            )
        if similarity(page.get("learning_goal"), page_summary) >= 0.9:
            add_page_issue(
                issues,
                "warning",
                "duplicate_goal_summary",
                path.name,
                page,
                index,
                "learning_goal and page_summary are nearly identical",
            )

        blocks = page.get("blocks")
        if not isinstance(blocks, list) or not blocks:
            add_page_issue(issues, "warning", "missing_blocks", path.name, page, index, "page should contain at least one block")
            continue

        block_types: set[str] = set()
        block_texts = block_text_map(page)
        for block in blocks:
            if not isinstance(block, dict):
                add_page_issue(issues, "warning", "invalid_block", path.name, page, index, "block entry should be an object")
                continue
            block_type = str(block.get("type") or "").strip()
            if not block_type:
                add_page_issue(issues, "warning", "missing_block_type", path.name, page, index, "block is missing `type`")
                continue
            if block_type in block_types:
                add_page_issue(issues, "warning", "duplicate_block_type", path.name, page, index, f"duplicate block type: {block_type}")
            block_types.add(block_type)
            content_text = flatten_content(block.get("content"))
            if not is_meaningful_text(content_text, 8):
                add_page_issue(
                    issues,
                    "warning",
                    "thin_block_content",
                    path.name,
                    page,
                    index,
                    f"`{block_type}` block is too short or placeholder-like",
                )

        for required in sorted(required_page_blocks(page)):
            if required not in block_types:
                add_page_issue(
                    issues,
                    "warning",
                    "missing_page_teaching_block",
                    path.name,
                    page,
                    index,
                    f"page is missing required block `{required}` for its teaching profile",
                )

        if "minimum_example" in block_texts and not has_concrete_marker(block_texts["minimum_example"]):
            add_page_issue(
                issues,
                "warning",
                "weak_minimum_example",
                path.name,
                page,
                index,
                "minimum_example lacks concrete objects, symbols, data, code, or a toy case",
            )
        if "trace" in block_texts and not has_step_marker(block_texts["trace"]):
            add_page_issue(
                issues,
                "warning",
                "weak_trace",
                path.name,
                page,
                index,
                "trace should show steps, transitions, or a structured walkthrough",
            )
        if "why_it_holds" in block_texts and not is_meaningful_text(block_texts["why_it_holds"], 18):
            add_page_issue(
                issues,
                "warning",
                "weak_why_it_holds",
                path.name,
                page,
                index,
                "why_it_holds is too thin to explain the mechanism",
            )
        if "confusion_fix" in block_texts and not (
            has_step_marker(block_texts["confusion_fix"])
            or contains_any_literal(
                block_texts["confusion_fix"],
                ["易错点", "纠正", "not", "wrong", "confus", "mistake", "trap"],
            )
        ):
            add_page_issue(
                issues,
                "warning",
                "weak_confusion_fix",
                path.name,
                page,
                index,
                "confusion_fix should name a specific confusion, misuse, or trap",
            )
        if "comparison" in block_texts and not (
            has_table_marker(block_texts["comparison"])
            or "vs" in str(block_texts["comparison"]).lower()
            or has_step_marker(block_texts["comparison"])
        ):
            add_page_issue(
                issues,
                "warning",
                "weak_comparison",
                path.name,
                page,
                index,
                "comparison should explicitly state the distinguishing criterion",
            )
        if "implementation_bridge" in block_texts and not (
            has_step_marker(block_texts["implementation_bridge"])
            or "`" in str(block_texts["implementation_bridge"])
            or contains_any_literal(
                block_texts["implementation_bridge"],
                ["code", "implement", "field", "array", "pointer", "queue", "stack", "cost"],
            )
        ):
            add_page_issue(
                issues,
                "warning",
                "weak_implementation_bridge",
                path.name,
                page,
                index,
                "implementation_bridge should connect the page to code, data layout, or operation cost",
            )
        if "closed_book_retell" in block_texts and not is_meaningful_text(block_texts["closed_book_retell"], 16):
            add_page_issue(
                issues,
                "warning",
                "weak_retell",
                path.name,
                page,
                index,
                "closed_book_retell is too thin to guide oral recall",
            )
        if "recap" in block_texts and similarity(block_texts["recap"], page_summary) >= 0.9:
            add_page_issue(
                issues,
                "warning",
                "duplicate_recap",
                path.name,
                page,
                index,
                "recap is nearly identical to page_summary",
            )
    if selected_page_ids:
        for page_id in sorted(selected_page_ids - matched_page_ids):
            add_issue(issues, "error", "missing_target_page", path.name, f"requested page not found: {page_id}")
    return matched_page_ids


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
    parser.add_argument(
        "--page-id",
        action="append",
        help="Only validate the selected page_id or knowledge_point_id. Repeatable; commas are also accepted.",
    )
    parser.add_argument("--json", action="store_true", help="Print a JSON report.")
    parser.add_argument("--allow-warnings", action="store_true", help="Exit zero when only warnings are present.")
    args = parser.parse_args()

    root = Path(args.study_pack)
    if not root.exists() or not root.is_dir():
        print(f"study pack directory not found: {root}", file=sys.stderr)
        return 2

    issues: list[dict[str, object]] = []
    selected_page_ids = normalize_requested_page_ids(args.page_id)
    matched_page_ids: set[str] = set()

    if selected_page_ids:
        knowledge_pages_path = root / "knowledge-pages.json"
        if not knowledge_pages_path.exists():
            add_issue(
                issues,
                "error",
                "missing_file",
                "knowledge-pages.json",
                "missing required file: knowledge-pages.json",
            )
        else:
            matched_page_ids = check_knowledge_pages(
                knowledge_pages_path,
                issues,
                selected_page_ids=selected_page_ids,
            )
    else:
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
            matched_page_ids = check_knowledge_pages(root / "knowledge-pages.json", issues)
        if (root / "_meta.json").exists():
            check_meta(root / "_meta.json", issues)

    errors = sum(1 for issue in issues if issue["severity"] == "error")
    warnings = sum(1 for issue in issues if issue["severity"] == "warning")
    report = {
        "path": str(root),
        "checker_version": CHECKER_VERSION,
        "scope": "selected_pages" if selected_page_ids else "chapter_pack",
        "selected_page_ids": sorted(selected_page_ids),
        "matched_page_ids": sorted(matched_page_ids),
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
