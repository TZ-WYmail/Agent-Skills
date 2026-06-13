#!/usr/bin/env python3
"""Build knowledge-pages.json from a vNext chapter pack.

Compatibility helper for legacy or transitional chapter packs that still
start from detailed-notes.md. The preferred vNext flow is page-first:
knowledge-map.json -> knowledge-pages.json -> detailed-notes.md.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")


def read_text(path: Path) -> str:
    for encoding in ("utf-8", "utf-8-sig", "gb18030"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def load_json(path: Path) -> dict:
    return json.loads(read_text(path))


def slugify(value: str) -> str:
    value = re.sub(r"<[^>]+>", "", value).strip().lower()
    value = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    return value or "section"


def normalize_heading_for_match(value: str) -> str:
    value = re.sub(r"<[^>]+>", "", value).strip().lower()
    value = re.sub(r"[^\w\u4e00-\u9fff]+", "", value)
    return value


def numeric_prefix(value: str) -> str:
    match = re.match(r"^(\d+(?:\.\d+)+)", value.strip())
    return match.group(1) if match else ""


def clean_line(line: str) -> str:
    line = line.strip()
    line = re.sub(r"^[-*]\s*", "", line)
    line = re.sub(r"^\d+\.\s*", "", line)
    return line.strip()


def summarize_markdown(text: str) -> str:
    for chunk in re.split(r"\n\s*\n", text.strip()):
        parts: list[str] = []
        for line in chunk.splitlines():
            stripped = clean_line(line)
            if not stripped:
                continue
            if stripped.startswith("|") or stripped.startswith("```"):
                continue
            parts.append(stripped)
        if parts:
            return " ".join(parts)
    return ""


def split_paragraphs(text: str) -> list[str]:
    paragraphs: list[str] = []
    for chunk in re.split(r"\n\s*\n", text.strip()):
        parts: list[str] = []
        for line in chunk.splitlines():
            stripped = clean_line(line)
            if not stripped:
                continue
            if stripped.startswith("|") or stripped.startswith("```"):
                continue
            parts.append(stripped)
        if parts:
            paragraphs.append(" ".join(parts))
    return paragraphs


def heading_has(title: str, *keywords: str) -> bool:
    lowered = title.lower()
    return any(keyword.lower() in lowered for keyword in keywords)


def heading_spans(lines: list[str]) -> list[dict[str, object]]:
    headings: list[dict[str, object]] = []
    for index, line in enumerate(lines):
        match = HEADING_RE.match(line.strip())
        if not match:
            continue
        headings.append(
            {
                "index": index,
                "level": len(match.group(1)),
                "title": match.group(2).strip(),
            }
        )
    return headings


def candidate_anchor_slugs(node: dict) -> list[str]:
    candidates: list[str] = []
    for key in ("notes_anchor", "section_anchor"):
        anchor = str(node.get(key) or "")
        if "#" in anchor:
            candidates.append(anchor.split("#", 1)[1].strip())
        elif anchor:
            candidates.append(anchor.strip())
    title = str(node.get("title") or "").strip()
    if title:
        candidates.append(slugify(title))
    deduped: list[str] = []
    for value in candidates:
        if value and value not in deduped:
            deduped.append(value)
    return deduped


def find_section(lines: list[str], node: dict) -> tuple[int, str, list[str]] | None:
    headings = heading_spans(lines)
    candidates = candidate_anchor_slugs(node)
    title_hint = normalize_heading_for_match(str(node.get("title") or ""))
    numeric_candidates = {
        numeric_prefix(candidate.replace("-", "."))
        for candidate in candidates
        if numeric_prefix(candidate.replace("-", "."))
    }
    slug_candidates = {candidate for candidate in candidates if candidate}
    normalized_candidates = {
        normalize_heading_for_match(candidate) for candidate in candidates if candidate
    }

    for offset, heading in enumerate(headings):
        title = str(heading["title"])
        title_slug = slugify(title)
        title_numeric = numeric_prefix(title)
        title_normalized = normalize_heading_for_match(title_slug)
        matches_slug = title_slug in slug_candidates
        matches_normalized = title_normalized in normalized_candidates
        matches_numeric = bool(title_numeric and title_numeric in numeric_candidates)
        matches_title_hint = bool(title_hint and title_hint in normalize_heading_for_match(title))
        if not (matches_slug or matches_normalized or matches_numeric or matches_title_hint):
            continue
        level = int(heading["level"])
        start = int(heading["index"]) + 1
        end = len(lines)
        for next_heading in headings[offset + 1 :]:
            if int(next_heading["level"]) <= level:
                end = int(next_heading["index"])
                break
        return level, title, lines[start:end]
    return None


def child_blocks(section_level: int, section_lines: list[str]) -> list[dict[str, str]]:
    headings = heading_spans(section_lines)
    blocks: list[dict[str, str]] = []
    child_level = section_level + 1
    for offset, heading in enumerate(headings):
        if int(heading["level"]) != child_level:
            continue
        title = str(heading["title"])
        start = int(heading["index"]) + 1
        end = len(section_lines)
        for next_heading in headings[offset + 1 :]:
            if int(next_heading["level"]) <= child_level:
                end = int(next_heading["index"])
                break
        body = "\n".join(section_lines[start:end]).strip()
        blocks.append({"title": title, "body": body})
    return blocks


def page_type_for(node: dict) -> str:
    node_type = str(node.get("type") or "")
    complexity = str(node.get("complexity_level") or "")
    if node_type == "procedure":
        return "procedure_explanation"
    if node_type == "comparison":
        return "comparison_explanation"
    if node_type == "implementation":
        return "representation_explanation"
    if node_type == "formula":
        return "formula_explanation"
    if node_type == "application" and complexity in {"C3", "C4"}:
        return "principle_explanation"
    return "concept_explanation"


def minutes_for(complexity: str) -> int:
    return {"C1": 6, "C2": 8, "C3": 12, "C4": 15}.get(complexity, 10)


def block_type_for(title: str) -> str | None:
    mappings = [
        (("本节主问题", "主问题", "Subsection Question"), "hook"),
        (("先看一个最小例子", "最小例子", "Minimum Example"), "minimum_example"),
        (("先观察会发生什么", "直觉", "Observation", "Intuition"), "intuition"),
        (("正式结论", "定义", "Formal Result", "Definition"), "formal_statement"),
        (("为什么成立", "Why It Holds"), "why_it_holds"),
        (("过程追踪", "Trace"), "trace"),
        (("边界", "反例", "误解", "易错", "Traps", "Confusion"), "confusion_fix"),
        (("和相邻概念的区别", "区别", "Difference From Nearby Concepts"), "comparison"),
        (("代码 / 实现 / 题型连接", "实现连接", "Implementation", "Code /"), "implementation_bridge"),
        (("本节闭卷输出模板", "闭卷输出", "Closed-Book"), "closed_book_retell"),
        (("本节自测", "Self-Check"), "mini_check"),
    ]
    for patterns, block_type in mappings:
        if heading_has(title, *patterns):
            return block_type
    return None


def infer_entry_question_from_title(title: str, page_type: str) -> str:
    if page_type == "procedure_explanation":
        return f"{title}的核心过程是怎样一步步发生的，为什么这样走不会出错？"
    if page_type == "representation_explanation":
        return f"{title}这种表示法到底在优化什么，它比相邻表示法强在哪里？"
    if page_type == "comparison_explanation":
        return f"{title}到底应该怎么选，最容易混淆的判断边界是什么？"
    if page_type == "principle_explanation":
        return f"{title}为什么成立，关键机制解释应该抓哪几步？"
    return f"{title}到底在解决什么问题，学完后最少要会说什么？"


def ordered_nodes(knowledge_map: dict) -> list[dict]:
    nodes = [node for node in knowledge_map.get("nodes", []) if isinstance(node, dict)]
    lookup = {str(node.get("id")): node for node in nodes if node.get("id")}
    ordered_ids: list[str] = []
    for path_name in ("study", "review"):
        for node_id in knowledge_map.get("recommended_paths", {}).get(path_name, []):
            node_key = str(node_id)
            if node_key in lookup and node_key not in ordered_ids:
                ordered_ids.append(node_key)

    def rank(node: dict) -> tuple[int, str]:
        importance_order = {"high": 0, "medium": 1, "low": 2}
        importance = str(node.get("importance_level") or "medium").lower()
        return importance_order.get(importance, 3), str(node.get("id") or "")

    remaining = sorted(
        (node for node_id, node in lookup.items() if node_id not in ordered_ids),
        key=rank,
    )
    return [lookup[node_id] for node_id in ordered_ids] + remaining


def build_fallback_blocks(
    section_title: str,
    entry_question: str,
    summary: str,
    paragraphs: list[str],
    teaching_goal: str,
) -> list[dict[str, object]]:
    fallback_formal = summary or section_title
    fallback_why = paragraphs[0] if paragraphs else ""
    blocks: list[dict[str, object]] = [
        {"type": "hook", "title": "入口问题", "content": entry_question},
        {"type": "formal_statement", "title": "核心结论", "content": fallback_formal},
    ]
    if fallback_why and fallback_why != fallback_formal:
        blocks.append(
            {
                "type": "why_it_holds",
                "title": "理解抓手",
                "content": fallback_why,
            }
        )
    blocks.append(
        {
            "type": "closed_book_retell",
            "title": "闭卷输出",
            "content": teaching_goal or fallback_formal,
        }
    )
    return blocks


def build_page(
    node: dict,
    node_exercise_map: dict[str, dict],
    node_review_map: dict[str, dict],
    lines: list[str],
) -> dict[str, object]:
    notes_anchor = str(node.get("notes_anchor") or "")
    section = find_section(lines, node)

    section_title = str(node.get("title") or node.get("id") or "")
    raw_blocks: list[dict[str, str]] = []
    if section:
        section_level, detected_title, section_lines = section
        section_title = detected_title or section_title
        raw_blocks = child_blocks(section_level, section_lines)

    page_type = page_type_for(node)
    extracted_blocks: list[dict[str, object]] = []
    entry_question = ""
    for block in raw_blocks:
        block_type = block_type_for(block["title"])
        if not block_type:
            continue
        body = block["body"].strip()
        if not body:
            continue
        if block_type == "hook" and not entry_question:
            entry_question = summarize_markdown(body)
        extracted_blocks.append(
            {
                "type": block_type,
                "title": block["title"],
                "content": body,
            }
        )

    if not entry_question:
        entry_question = infer_entry_question_from_title(section_title, page_type)

    combined_raw = "\n\n".join(block["body"] for block in raw_blocks)
    summary = str(node.get("summary") or "").strip() or summarize_markdown(combined_raw)
    paragraphs = split_paragraphs(combined_raw)
    teaching_goal = str(node.get("teaching_goal") or "").strip()

    if extracted_blocks:
        blocks = list(extracted_blocks)
    else:
        blocks = build_fallback_blocks(
            section_title=section_title,
            entry_question=entry_question,
            summary=summary,
            paragraphs=paragraphs,
            teaching_goal=teaching_goal,
        )

    if summary:
        blocks.append(
            {
                "type": "recap",
                "title": "一页总结",
                "content": summary,
            }
        )

    node_id = str(node.get("id") or "")
    exercise_entry = node_exercise_map.get(node_id, {})
    review_entry = node_review_map.get(node_id, {})
    practice_refs = [str(item) for item in node.get("related_exercises", [])]
    if not practice_refs:
        practice_refs = [str(item) for item in exercise_entry.get("exercise_ids", [])]
    review_refs = [str(item) for item in review_entry.get("card_ids", [])]
    if prompt := str(review_entry.get("oral_prompt") or "").strip():
        review_refs.append(prompt)

    return {
        "page_id": node_id,
        "knowledge_point_id": node_id,
        "title": str(node.get("title") or ""),
        "type": page_type,
        "complexity_level": str(node.get("complexity_level") or ""),
        "importance_level": str(node.get("importance_level") or ""),
        "estimated_teaching_minutes": minutes_for(str(node.get("complexity_level") or "")),
        "prerequisites": [str(item) for item in node.get("prerequisites", [])],
        "learning_goal": teaching_goal,
        "entry_question": entry_question,
        "page_summary": summary,
        "notes_anchor": notes_anchor,
        "practice_refs": practice_refs,
        "review_refs": review_refs,
        "source_refs": [],
        "blocks": blocks,
    }


def update_meta(chapter_dir: Path, overwrite: bool) -> None:
    meta_path = chapter_dir / "_meta.json"
    if not meta_path.exists():
        return
    meta = load_json(meta_path)
    files = meta.get("files")
    if not isinstance(files, list):
        files = []
    if "knowledge-pages.json" not in files:
        files.append("knowledge-pages.json")
    meta["files"] = files
    old_meta = load_json(meta_path)
    if overwrite or "knowledge-pages.json" not in old_meta.get("files", []):
        write_text(meta_path, json.dumps(meta, ensure_ascii=False, indent=2) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build knowledge-pages.json from a vNext chapter pack."
    )
    parser.add_argument(
        "chapter_dir",
        help="Chapter directory containing knowledge-map.json and detailed-notes.md.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite an existing knowledge-pages.json.",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON summary.")
    args = parser.parse_args()

    chapter_dir = Path(args.chapter_dir).resolve()
    knowledge_map_path = chapter_dir / "knowledge-map.json"
    notes_path = chapter_dir / "detailed-notes.md"
    out_path = chapter_dir / "knowledge-pages.json"
    if not knowledge_map_path.exists():
        raise SystemExit(f"missing file: {knowledge_map_path}")
    if not notes_path.exists():
        raise SystemExit(f"missing file: {notes_path}")
    if out_path.exists() and not args.overwrite:
        raise SystemExit(f"target exists: {out_path}; use --overwrite")

    knowledge_map = load_json(knowledge_map_path)
    lines = read_text(notes_path).replace("\r\n", "\n").split("\n")
    node_exercise_map = {
        str(item.get("knowledge_point_id")): item
        for item in knowledge_map.get("exercise_map", [])
        if isinstance(item, dict) and item.get("knowledge_point_id")
    }
    node_review_map = {
        str(item.get("knowledge_point_id")): item
        for item in knowledge_map.get("review_map", [])
        if isinstance(item, dict) and item.get("knowledge_point_id")
    }
    pages = [
        build_page(node, node_exercise_map, node_review_map, lines)
        for node in ordered_nodes(knowledge_map)
    ]
    payload = {
        "version": "1.0",
        "chapter_id": str(knowledge_map.get("chapter_id") or chapter_dir.name),
        "chapter_title": str(knowledge_map.get("chapter_title") or chapter_dir.name),
        "source_id": str(knowledge_map.get("source_id") or ""),
        "output_mode": str(knowledge_map.get("output_mode") or ""),
        "generated_at": str(knowledge_map.get("generated_at") or ""),
        "pages": pages,
    }
    write_text(out_path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    update_meta(chapter_dir, overwrite=True)

    summary = {
        "chapter_dir": str(chapter_dir),
        "output": str(out_path),
        "page_count": len(pages),
    }
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(f"built {len(pages)} pages -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
