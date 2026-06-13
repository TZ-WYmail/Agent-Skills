#!/usr/bin/env python3
"""Ensure every knowledge page has a page_brief planning block."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def load_json(path: Path) -> dict:
    return json.loads(read_text(path))


def dump_json(path: Path, data: dict) -> None:
    write_text(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def normalize_requested_page_ids(values: list[str] | None) -> set[str]:
    result: set[str] = set()
    for value in values or []:
        for item in str(value or "").split(","):
            text = item.strip()
            if text:
                result.add(text)
    return result


def nonempty_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    result: list[str] = []
    for item in value:
        text = str(item or "").strip()
        if text:
            result.append(text)
    return result


def page_label(page: dict) -> str:
    return str(page.get("title") or page.get("knowledge_point_id") or page.get("page_id") or "该知识点").strip()


def infer_best_entry_point(page: dict) -> str:
    entry_question = str(page.get("entry_question") or "").strip()
    if entry_question:
        return f"先从这个疑问切入：{entry_question}"
    kind = str(page.get("page_kind") or "").strip().lower()
    title = page_label(page)
    if kind == "comparison":
        return f"先给出最容易混淆的两个对象，再说明 {title} 的判别标准。"
    if kind in {"procedure", "principle", "formula"}:
        return f"先给一个最小过程或现象，再解释 {title} 为什么这样走。"
    if kind in {"representation", "implementation"}:
        return f"先说明为什么要这样存或这样实现，再展开 {title} 的字段与代价。"
    return f"先用一个最小例子让学习者看到 {title} 在解决什么问题。"


def infer_minimum_example_hint(page: dict) -> str:
    title = page_label(page)
    kind = str(page.get("page_kind") or "").strip().lower()
    if kind in {"procedure", "principle"}:
        return f"必须给出能手工追踪步骤的最小例子，不能只给定义；例子要足以解释 {title} 的机制。"
    if kind in {"comparison", "representation", "implementation"}:
        return f"必须给出可并排对照的最小例子，帮助学习者看清 {title} 的取舍与适用场景。"
    return f"必须给出一个能直接落到对象、数据、图或代码上的最小例子来解释 {title}。"


def infer_why_it_holds_focus(page: dict) -> str:
    title = page_label(page)
    must_answer = nonempty_list(page.get("must_answer"))
    for item in must_answer:
        if "为什么" in item or "为何" in item:
            return item
    kind = str(page.get("page_kind") or "").strip().lower()
    if kind in {"procedure", "principle", "formula"}:
        return f"必须讲清 {title} 为什么成立，或者它的关键步骤为什么这样安排。"
    return f"必须讲清 {title} 的核心判别标准为什么这样定义，而不是只给结论。"


def infer_confusion_priority(page: dict) -> str:
    failure_signals = nonempty_list(page.get("failure_signals"))
    if failure_signals:
        return failure_signals[0]
    title = page_label(page)
    return f"重点消除学习者把 {title} 和相邻概念混淆，或者只会背结论不会解释机制的问题。"


def infer_closed_book_target(page: dict) -> str:
    exit_outcomes = nonempty_list(page.get("exit_outcomes"))
    if exit_outcomes:
        return exit_outcomes[0]
    learning_goal = str(page.get("learning_goal") or "").strip()
    if learning_goal:
        return learning_goal
    return f"闭卷时至少能用自己的话讲清 {page_label(page)} 的核心机制。"


def build_page_brief(page: dict) -> dict[str, str]:
    return {
        "learner_doubt": str(page.get("entry_question") or "").strip() or f"{page_label(page)} 到底在回答什么问题？",
        "best_entry_point": infer_best_entry_point(page),
        "minimum_example_hint": infer_minimum_example_hint(page),
        "why_it_holds_focus": infer_why_it_holds_focus(page),
        "confusion_priority": infer_confusion_priority(page),
        "closed_book_target": infer_closed_book_target(page),
    }


def page_aliases(page: dict) -> set[str]:
    result = {
        str(page.get("page_id") or "").strip(),
        str(page.get("knowledge_point_id") or "").strip(),
    }
    return {item for item in result if item}


def main() -> int:
    parser = argparse.ArgumentParser(description="Ensure every knowledge page has a page_brief plan.")
    parser.add_argument("chapter_dir", help="Chapter directory containing knowledge-pages.json.")
    parser.add_argument(
        "--page-id",
        action="append",
        help="Only update the selected page_id or knowledge_point_id. Repeatable; commas are also accepted.",
    )
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing page_brief fields.")
    parser.add_argument("--json", action="store_true", help="Print JSON summary.")
    args = parser.parse_args()

    chapter_dir = Path(args.chapter_dir).resolve()
    pages_path = chapter_dir / "knowledge-pages.json"
    if not pages_path.exists():
        raise SystemExit(f"missing file: {pages_path}")

    selected_page_ids = normalize_requested_page_ids(args.page_id)
    data = load_json(pages_path)
    pages = data.get("pages", [])
    updated: list[dict[str, object]] = []
    missing_targets = set(selected_page_ids)

    if isinstance(pages, list):
        for page in pages:
            if not isinstance(page, dict):
                continue
            aliases = page_aliases(page)
            if selected_page_ids and aliases.isdisjoint(selected_page_ids):
                continue
            missing_targets -= aliases

            existing = page.get("page_brief")
            if isinstance(existing, dict) and existing and not args.overwrite:
                continue

            brief = build_page_brief(page)
            page["page_brief"] = brief
            updated.append(
                {
                    "page_id": str(page.get("knowledge_point_id") or page.get("page_id") or ""),
                    "title": page.get("title"),
                }
            )

    if updated:
        dump_json(pages_path, data)

    summary = {
        "chapter_dir": str(chapter_dir),
        "selected_page_ids": sorted(selected_page_ids),
        "missing_target_page_ids": sorted(missing_targets),
        "updated_pages": len(updated),
        "updates": updated,
    }
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(f"updated {len(updated)} page briefs in {pages_path}")
        for item in updated:
            print(f"{item['page_id']}: page_brief")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
