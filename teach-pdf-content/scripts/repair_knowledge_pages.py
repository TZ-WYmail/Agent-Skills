#!/usr/bin/env python3
"""Repair flagged knowledge-page blocks without rerunning the whole chapter."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


REPAIRABLE_CODES = {
    "duplicate_recap",
    "weak_comparison",
    "weak_implementation_bridge",
    "weak_confusion_fix",
}


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


def block_map(page: dict) -> dict[str, dict]:
    result: dict[str, dict] = {}
    for block in page.get("blocks", []):
        if not isinstance(block, dict):
            continue
        block_type = str(block.get("type") or "").strip()
        if block_type and block_type not in result:
            result[block_type] = block
    return result


def ensure_block(page: dict, block_type: str, title: str) -> dict:
    blocks = page.setdefault("blocks", [])
    if not isinstance(blocks, list):
        blocks = []
        page["blocks"] = blocks
    for block in blocks:
        if isinstance(block, dict) and str(block.get("type") or "").strip() == block_type:
            if not block.get("title"):
                block["title"] = title
            return block
    block = {"type": block_type, "title": title, "content": [""]}
    blocks.append(block)
    return block


def page_label(page: dict) -> str:
    return str(page.get("title") or page.get("knowledge_point_id") or "该知识点").strip()


def list_to_bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items if item.strip())


def choose_distinctions(page: dict) -> list[str]:
    title = page_label(page)
    must_answer = nonempty_list(page.get("must_answer"))
    distinctions: list[str] = []
    for item in must_answer:
        if "区别" in item or "选用" in item or "判断标准" in item:
            distinctions.append(item)
    if distinctions:
        return distinctions[:2]
    page_kind = str(page.get("page_kind") or "")
    if page_kind in {"comparison", "representation", "implementation"}:
        return [
            f"{title}和相邻方案的关键区别是什么",
            f"{title}在什么场景下更合适，什么场景下不合适",
        ]
    return [f"{title}最容易和哪个相邻概念混淆，判断标准是什么"]


def build_comparison_content(page: dict) -> str:
    title = page_label(page)
    distinctions = choose_distinctions(page)
    lines = [
        f"{title}的对比重点不是“名字像不像”，而是看判断标准、使用目标和代价：",
    ]
    for item in distinctions:
        lines.append(f"- 区别标准：{item}")
    lines.append(f"- 如果题目在问“该选哪种方案”，就要回到 {title} 的使用场景、查询方式和代价去判断。")
    return "\n".join(lines)


def build_implementation_content(page: dict) -> str:
    title = page_label(page)
    practice_refs = nonempty_list(page.get("practice_refs"))
    lines = [
        f"{title}在实现层面至少要落到“代码对象 / 数据布局 / 使用代价”三个点上：",
        "- 代码对象：这一页涉及哪些常见字段、数组、指针、队列、栈，或中间状态记录。",
        "- 数据布局：这些字段分别在记录什么信息，谁依赖谁更新。",
        "- 使用代价：它主要优化的是判边、扫描邻接点、入度统计、最短路更新，还是别的操作。",
    ]
    if practice_refs:
        lines.append(f"- 题型连接：这页常会在 {', '.join(practice_refs[:3])} 这类题里出现，答题时要把机制说到实现层。")
    else:
        lines.append("- 题型连接：答题时不要只背结论，要能指出实现里靠什么字段或状态支撑。")
    return "\n".join(lines)


def build_confusion_content(page: dict) -> str:
    title = page_label(page)
    failure_signals = nonempty_list(page.get("failure_signals"))
    lines = [f"{title}最容易错的不是定义本身，而是以下误用："]
    if failure_signals:
        for item in failure_signals[:3]:
            lines.append(f"- 易错点：{item}")
    else:
        lines.extend(
            [
                f"- 易错点：把 {title} 和相邻概念混为一谈。",
                f"- 易错点：只记住口号，却说不清 {title} 为什么这样设计或为什么这样成立。",
            ]
        )
    lines.append("- 纠正动作：先回到最小例子，再用判断标准逐条排除误解。")
    return "\n".join(lines)


def build_recap_content(page: dict) -> str:
    title = page_label(page)
    exit_outcomes = nonempty_list(page.get("exit_outcomes"))
    must_answer = nonempty_list(page.get("must_answer"))
    if exit_outcomes:
        return f"{title}这页看完后，你至少应该能做到：{exit_outcomes[0]}。"
    if must_answer:
        return f"{title}这页的核心不是背标题，而是回答：{must_answer[0]}"
    return f"{title}这页的目标是把核心机制压缩成一句可回忆的话，而不是重复摘要。"


def collect_checker_issues(chapter_dir: Path) -> dict[str, set[str]]:
    return collect_checker_issues_for_pages(chapter_dir, selected_page_ids=None)


def collect_checker_issues_for_pages(
    chapter_dir: Path,
    selected_page_ids: set[str] | None,
) -> dict[str, set[str]]:
    checker_path = Path(__file__).with_name("check_lesson_pack_vnext.py")
    import importlib.util

    spec = importlib.util.spec_from_file_location("checker", checker_path)
    checker = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(checker)

    issues: list[dict[str, object]] = []
    checker.check_knowledge_pages(
        chapter_dir / "knowledge-pages.json",
        issues,
        selected_page_ids=selected_page_ids,
    )

    page_codes: dict[str, set[str]] = {}
    for issue in issues:
        if issue.get("file") != "knowledge-pages.json":
            continue
        code = str(issue.get("code") or "")
        if code not in REPAIRABLE_CODES:
            continue
        message = str(issue.get("message") or "")
        page_id = message.split(" ", 1)[0].strip()
        if not page_id:
            continue
        page_codes.setdefault(page_id, set()).add(code)
    return page_codes


def repair_page(page: dict, codes: set[str]) -> list[str]:
    changed: list[str] = []
    if "weak_comparison" in codes:
        block = ensure_block(page, "comparison", "和相邻概念的区别")
        block["content"] = build_comparison_content(page)
        changed.append("comparison")
    if "weak_implementation_bridge" in codes:
        block = ensure_block(page, "implementation_bridge", "代码 / 实现 / 题型连接")
        block["content"] = build_implementation_content(page)
        changed.append("implementation_bridge")
    if "weak_confusion_fix" in codes:
        block = ensure_block(page, "confusion_fix", "边界、反例与易错点")
        block["content"] = build_confusion_content(page)
        changed.append("confusion_fix")
    if "duplicate_recap" in codes:
        block = ensure_block(page, "recap", "一句话回顾")
        block["content"] = build_recap_content(page)
        changed.append("recap")
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description="Repair flagged knowledge-page blocks.")
    parser.add_argument("chapter_dir", help="Chapter directory containing knowledge-pages.json.")
    parser.add_argument(
        "--page-id",
        action="append",
        help="Only repair the selected page_id or knowledge_point_id. Repeatable; commas are also accepted.",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON summary.")
    args = parser.parse_args()

    chapter_dir = Path(args.chapter_dir).resolve()
    pages_path = chapter_dir / "knowledge-pages.json"
    if not pages_path.exists():
        raise SystemExit(f"missing file: {pages_path}")

    selected_page_ids = normalize_requested_page_ids(args.page_id)
    page_codes = collect_checker_issues_for_pages(chapter_dir, selected_page_ids=selected_page_ids or None)
    data = load_json(pages_path)
    pages = data.get("pages", [])
    repaired: list[dict[str, object]] = []
    missing_targets = set(selected_page_ids)
    if isinstance(pages, list):
        for page in pages:
            if not isinstance(page, dict):
                continue
            page_id = str(page.get("knowledge_point_id") or page.get("page_id") or "").strip()
            page_aliases = {
                page_id,
                str(page.get("page_id") or "").strip(),
                str(page.get("knowledge_point_id") or "").strip(),
            }
            page_aliases.discard("")
            if selected_page_ids and page_aliases.isdisjoint(selected_page_ids):
                continue
            missing_targets -= page_aliases
            codes = page_codes.get(page_id, set())
            if not codes:
                continue
            changed_blocks = repair_page(page, codes)
            if changed_blocks:
                repaired.append(
                    {
                        "page_id": page_id,
                        "title": page.get("title"),
                        "codes": sorted(codes),
                        "changed_blocks": changed_blocks,
                    }
                )

    if repaired:
        dump_json(pages_path, data)

    summary = {
        "chapter_dir": str(chapter_dir),
        "selected_page_ids": sorted(selected_page_ids),
        "missing_target_page_ids": sorted(missing_targets),
        "repaired_pages": len(repaired),
        "repairs": repaired,
    }
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(f"repaired {len(repaired)} pages in {pages_path}")
        for item in repaired:
            print(f"{item['page_id']}: {', '.join(item['changed_blocks'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
