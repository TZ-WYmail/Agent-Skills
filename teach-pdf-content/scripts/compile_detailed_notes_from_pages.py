#!/usr/bin/env python3
"""Compile detailed-notes.md from knowledge-pages.json and support files."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


BLOCK_ORDER = [
    "hook",
    "minimum_example",
    "intuition",
    "formal_statement",
    "why_it_holds",
    "trace",
    "confusion_fix",
    "comparison",
    "implementation_bridge",
    "closed_book_retell",
    "mini_check",
    "recap",
]

BLOCK_HEADINGS = {
    "hook": "本节主问题",
    "minimum_example": "先看一个最小例子",
    "intuition": "先观察会发生什么",
    "formal_statement": "正式结论 / 定义",
    "why_it_holds": "为什么成立",
    "trace": "过程追踪 / Trace",
    "confusion_fix": "边界、反例与易错点",
    "comparison": "和相邻概念的区别",
    "implementation_bridge": "代码 / 实现 / 题型连接",
    "closed_book_retell": "本节闭卷输出模板",
    "mini_check": "本节自测",
    "recap": "本节一句话回顾",
}

TYPE_LABELS = {
    "core_concept": "核心概念",
    "comparison": "对比辨析",
    "implementation": "表示与实现",
    "procedure": "过程与算法",
    "application": "结构结论",
    "formula": "公式规则",
}

COMPLEXITY_MINUTES = {"C1": 6, "C2": 8, "C3": 12, "C4": 15}


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


def dump_json(path: Path, data: dict) -> None:
    write_text(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def slugify(value: str) -> str:
    value = re.sub(r"<[^>]+>", "", value).strip().lower()
    value = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    return value or "section"


def strip_markdown(text: str) -> str:
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*\n]+)\*", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    return text.strip()


def clean_lines(text: str) -> list[str]:
    return [line.rstrip() for line in text.replace("\r\n", "\n").split("\n")]


def first_nonempty_line(text: str) -> str:
    for line in clean_lines(str(text or "")):
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def plain_summary(value: str) -> str:
    line = first_nonempty_line(value)
    return strip_markdown(line)


def dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        normalized = item.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result


def chapter_range_from_source_map(text: str) -> str:
    for line in clean_lines(text):
        if "请求范围" in line or "范围：" in line or "Range:" in line:
            parts = line.split("：", 1) if "：" in line else line.split(":", 1)
            if len(parts) == 2:
                return parts[1].strip().strip("`")
    return ""


def extraction_quality_from_source_map(text: str) -> str:
    in_quality = False
    bullets: list[str] = []
    for line in clean_lines(text):
        stripped = line.strip()
        if stripped.startswith("## "):
            if "提取质量" in stripped or "Extraction Quality" in stripped:
                in_quality = True
                continue
            if in_quality:
                break
        if in_quality and stripped.startswith("- "):
            bullets.append(stripped[2:].strip())
            if len(bullets) >= 2:
                break
    return "；".join(bullets)


def source_path_from_source_map(text: str) -> str:
    for line in clean_lines(text):
        if line.strip().startswith("- 文件") or line.strip().startswith("- File"):
            parts = line.split("：", 1) if "：" in line else line.split(":", 1)
            if len(parts) == 2:
                return parts[1].strip().strip("`")
    return ""


def normalize_match_text(value: str) -> str:
    value = strip_markdown(str(value or "")).lower()
    value = re.sub(r"[^\w\u4e00-\u9fff]+", "", value)
    return value


def ascii_tokens(value: str) -> list[str]:
    tokens = [token.upper() for token in re.findall(r"[A-Za-z][A-Za-z0-9+._/-]*", str(value or ""))]
    return dedupe(tokens)


def keyword_variants(value: str) -> list[str]:
    normalized = normalize_match_text(value)
    if not normalized:
        return []
    variants = [normalized]
    for prefix in ("无向图的", "有向图的", "图的", "无向图", "有向图", "图"):
        if normalized.startswith(prefix):
            stripped = normalized[len(prefix) :]
            if len(stripped) >= 2:
                variants.append(stripped)
    return dedupe(variants)


def split_keywords(value: str) -> list[str]:
    raw = re.split(r"[、，,：:/（）()\- ]+|与|和|及|及其", strip_markdown(str(value or "")))
    keywords: list[str] = []
    for item in raw:
        for variant in keyword_variants(item):
            if len(variant) >= 2:
                keywords.append(variant)
    return dedupe(keywords)


def expand_section_range(section: str) -> list[str]:
    section = section.strip()
    if "-" not in section:
        return [section]
    start, end = [part.strip() for part in section.split("-", 1)]
    if re.match(r"^\d+(?:\.\d+)+$", start) and re.match(r"^\d+(?:\.\d+)+$", end):
        return [start, end]
    return [start]


def parse_source_rows(source_map_text: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    section_re = re.compile(r"^\d+(?:\.\d+)+(?:-\d+(?:\.\d+)*)?$")
    for line in clean_lines(source_map_text):
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) < 4:
            continue
        section = cells[2]
        topic = cells[3]
        if not section_re.match(section) or topic in {"标题/小节", "小节", "---"}:
            continue
        first_section = expand_section_range(section)[0]
        rows.append(
            {
                "section_number": first_section,
                "topic": topic,
                "normalized": normalize_match_text(topic),
                "keywords": split_keywords(topic),
                "tokens": ascii_tokens(topic),
            }
        )
        items = [item.strip() for item in re.split(r"[、/]", topic) if item.strip()]
        sections = expand_section_range(section)
        if len(items) == len(sections) and len(items) > 1:
            for item, section_number in zip(items, sections):
                rows.append(
                    {
                        "section_number": section_number,
                        "topic": item,
                        "normalized": normalize_match_text(item),
                        "keywords": split_keywords(item),
                        "tokens": ascii_tokens(item),
                    }
                )
    return rows


def existing_section_number(page: dict, node: dict) -> str:
    for value in (str(page.get("__section_number") or ""), str(node.get("section_number") or "")):
        if re.match(r"^\d+(?:\.\d+)+$", value):
            return value
    for value in (
        str(node.get("section_anchor") or ""),
        str(node.get("notes_anchor") or ""),
        str(page.get("notes_anchor") or ""),
    ):
        fragment = anchor_fragment(value)
        match = re.match(r"^(\d+(?:[-.]\d+)+)", fragment)
        if not match:
            continue
        parts = tuple(int(part) for part in re.split(r"[-.]", match.group(1)))
        if len(parts) >= 2:
            return ".".join(str(part) for part in parts)
    return ""


def keyword_overlap_score(page_keywords: set[str], row_keywords: set[str]) -> int:
    shared_keywords = page_keywords & row_keywords
    score = 18 * len(shared_keywords)
    score += sum(min(len(keyword), 8) for keyword in shared_keywords)

    partial_matches: list[str] = []
    for page_keyword in page_keywords:
        for row_keyword in row_keywords:
            if page_keyword == row_keyword:
                continue
            if page_keyword in row_keyword or row_keyword in page_keyword:
                shorter = page_keyword if len(page_keyword) <= len(row_keyword) else row_keyword
                if len(shorter) >= 3:
                    partial_matches.append(shorter)
    for keyword in dedupe(sorted(partial_matches, key=len, reverse=True)):
        score += 8 + min(len(keyword), 6)
    return score


def match_source_section(page: dict, node: dict, source_rows: list[dict[str, object]]) -> str:
    page_text = " ".join(
        value
        for value in (
            str(page.get("title") or "").strip(),
            str(node.get("title") or "").strip(),
        )
        if value
    )
    normalized_page = normalize_match_text(page_text)
    page_keywords = set(split_keywords(page_text))
    page_tokens = set(ascii_tokens(page_text))
    best_score = -1
    best_section = ""
    for row in source_rows:
        row_normalized = str(row.get("normalized") or "")
        row_keywords = set(row.get("keywords") or [])
        row_tokens = set(row.get("tokens") or [])
        score = 0
        if normalized_page and row_normalized:
            if normalized_page == row_normalized:
                score += 120
            elif normalized_page in row_normalized or row_normalized in normalized_page:
                score += 90
        shared_tokens = page_tokens & row_tokens
        score += keyword_overlap_score(page_keywords, row_keywords)
        score += 24 * len(shared_tokens)
        if score > best_score:
            best_score = score
            best_section = str(row.get("section_number") or "")
    return best_section if best_score >= 18 else ""


def infer_section_numbers(
    pages: list[dict],
    node_lookup: dict[str, dict],
    source_rows: list[dict[str, object]],
    chapter_number: int | None,
) -> dict[str, str]:
    def page_rank(page: dict) -> tuple[int, str]:
        page_id = str(page.get("page_id") or page.get("knowledge_point_id") or "")
        match = re.search(r"(\d+)$", page_id)
        return (int(match.group(1)) if match else 9999, page_id)

    ordered_pages = sorted(pages, key=page_rank)
    inferred: dict[str, str] = {}
    for page in ordered_pages:
        page_id = str(page.get("knowledge_point_id") or page.get("page_id") or "")
        node = node_lookup.get(page_id, {})
        inferred[page_id] = match_source_section(page, node, source_rows) or existing_section_number(page, node)

    for index, page in enumerate(ordered_pages):
        page_id = str(page.get("knowledge_point_id") or page.get("page_id") or "")
        if inferred.get(page_id):
            continue
        prev_section = ""
        next_section = ""
        for back in range(index - 1, -1, -1):
            other_id = str(ordered_pages[back].get("knowledge_point_id") or ordered_pages[back].get("page_id") or "")
            if inferred.get(other_id):
                prev_section = inferred[other_id]
                break
        for ahead in range(index + 1, len(ordered_pages)):
            other_id = str(ordered_pages[ahead].get("knowledge_point_id") or ordered_pages[ahead].get("page_id") or "")
            if inferred.get(other_id):
                next_section = inferred[other_id]
                break

        candidate = ""
        if prev_section and next_section:
            prev_parts = prev_section.split(".")
            next_parts = next_section.split(".")
            if len(prev_parts) >= 2 and len(next_parts) >= 2 and prev_parts[:2] == next_parts[:2]:
                candidate = ".".join(prev_parts[:2])
            elif len(next_parts) >= 2:
                candidate = ".".join(next_parts[:2])
        elif next_section:
            next_parts = next_section.split(".")
            if (
                index == 0
                and chapter_number is not None
                and len(next_parts) >= 2
                and next_parts[0].isdigit()
                and next_parts[1].isdigit()
                and int(next_parts[0]) == chapter_number
                and int(next_parts[1]) > 1
            ):
                candidate = f"{chapter_number}.{int(next_parts[1]) - 1}"
            elif len(next_parts) >= 3:
                candidate = ".".join(next_parts[:2])
            elif len(next_parts) >= 2:
                candidate = next_section
        elif prev_section:
            prev_parts = prev_section.split(".")
            if len(prev_parts) >= 3:
                candidate = ".".join(prev_parts[:2])
            elif len(prev_parts) >= 2:
                candidate = prev_section

        if not candidate and chapter_number is not None and next_section:
            next_parts = next_section.split(".")
            if len(next_parts) >= 2 and next_parts[0].isdigit() and next_parts[1].isdigit():
                next_major = int(next_parts[1])
                if next_major > 1:
                    candidate = f"{chapter_number}.{next_major - 1}"

        if candidate:
            inferred[page_id] = candidate
    return inferred


def source_basis_for_page(page: dict) -> str:
    refs = [str(item).strip() for item in page.get("source_refs", []) if str(item).strip()]
    if refs:
        return "；".join(refs)
    return ""


def anchor_fragment(value: str) -> str:
    if "#" in value:
        return value.split("#", 1)[1].strip()
    return value.strip()


def anchor_text_for(page: dict, node: dict) -> str:
    for value in (
        str(node.get("section_anchor") or ""),
        str(node.get("notes_anchor") or ""),
        str(page.get("notes_anchor") or ""),
        str(page.get("title") or ""),
    ):
        fragment = anchor_fragment(value)
        if fragment:
            return fragment
    return ""


def numeric_parts_for(page: dict, node: dict) -> tuple[int, ...]:
    explicit = existing_section_number(page, node)
    if explicit:
        return tuple(int(part) for part in explicit.split("."))
    anchor = anchor_text_for(page, node)
    match = re.match(r"^(\d+(?:[-.]\d+)+)", anchor)
    if match:
        return tuple(int(part) for part in re.split(r"[-.]", match.group(1)))
    title = str(page.get("title") or "").strip()
    match = re.match(r"^(\d+(?:\.\d+)+)", title)
    if match:
        return tuple(int(part) for part in match.group(1).split("."))
    return ()


def build_section_number(page: dict, node: dict, fallback_index: int) -> str:
    parts = numeric_parts_for(page, node)
    if parts:
        return ".".join(str(part) for part in parts)
    title = str(page.get("title") or "").strip()
    match = re.match(r"^(\d+(?:\.\d+)+)", title)
    if match:
        return match.group(1)
    return str(fallback_index)


def subsection_title_for(page: dict, node: dict, fallback_index: int) -> str:
    title = str(page.get("title") or page.get("page_id") or f"知识点 {fallback_index}").strip()
    number = build_section_number(page, node, fallback_index)
    if title.startswith(number):
        return title
    return f"{number} {title}"


def heading_anchor(section_title: str) -> str:
    return slugify(section_title)


def render_markdown_content(content: object) -> str:
    if isinstance(content, list):
        values = [str(item).rstrip() for item in content if str(item).strip()]
        if not values:
            return ""
        if all("\n" not in item for item in values):
            return "\n".join(f"- {item}" for item in values)
        return "\n\n".join(values)
    return str(content or "").strip()


def block_lookup(page: dict) -> dict[str, dict]:
    items = [item for item in page.get("blocks", []) if isinstance(item, dict)]
    ordered = sorted(
        items,
        key=lambda item: (
            BLOCK_ORDER.index(str(item.get("type"))) if str(item.get("type")) in BLOCK_ORDER else len(BLOCK_ORDER),
            str(item.get("title") or ""),
        ),
    )
    result: dict[str, dict] = {}
    for item in ordered:
        block_type = str(item.get("type") or "")
        if block_type and block_type not in result:
            result[block_type] = item
    return result


def fallback_block_content(page: dict, block_type: str) -> str:
    if block_type == "hook":
        return str(page.get("entry_question") or "").strip()
    if block_type == "formal_statement":
        return str(page.get("page_summary") or "").strip()
    if block_type == "closed_book_retell":
        return str(page.get("learning_goal") or page.get("page_summary") or "").strip()
    return ""


def render_block(page: dict, block_type: str) -> str:
    lookup = block_lookup(page)
    block = lookup.get(block_type)
    content = ""
    if block:
        content = render_markdown_content(block.get("content"))
    if not content:
        content = fallback_block_content(page, block_type)
    if not content:
        return ""
    heading = BLOCK_HEADINGS[block_type]
    return f"#### {heading}\n{content.strip()}\n"


def section_kind(node: dict) -> str:
    node_type = str(node.get("type") or "")
    return TYPE_LABELS.get(node_type, "知识点")


def practice_ref_line(page: dict) -> str:
    refs = [str(item).strip() for item in page.get("practice_refs", []) if str(item).strip()]
    return "、".join(refs) if refs else "待补充"


def review_ref_line(page: dict) -> str:
    refs = [str(item).strip() for item in page.get("review_refs", []) if str(item).strip()]
    return "、".join(refs) if refs else "待补充"


def prerequisite_titles(page: dict, node_lookup: dict[str, dict]) -> list[str]:
    titles: list[str] = []
    for node_id in page.get("prerequisites", []):
        title = str(node_lookup.get(str(node_id), {}).get("title") or "").strip()
        if title:
            titles.append(title)
    return dedupe(titles)


def build_kp_table(page: dict, node: dict) -> str:
    page_id = str(page.get("knowledge_point_id") or page.get("page_id") or "").strip()
    title = str(page.get("title") or page_id).strip()
    complexity = str(page.get("complexity_level") or "").strip() or "C2"
    importance = str(page.get("importance_level") or "").strip() or "medium"
    learning_goal = str(page.get("learning_goal") or "").strip() or "理解并复述"
    importance_label = {"high": "高", "medium": "中", "low": "低"}.get(importance.lower(), importance)
    is_new = "是" if bool(node.get("is_new_concept", True)) else "否"
    return "\n".join(
        [
            "#### 本节知识点",
            "| 知识点 ID | 名称 | 是否新概念 | 复杂度 | 重要度 | 掌握目标 |",
            "| --- | --- | --- | --- | --- | --- |",
            f"| {page_id} | {title} | {is_new} | {complexity} | {importance_label} | {learning_goal} |",
            "",
        ]
    )


def build_intro(
    chapter_title: str,
    chapter_range: str,
    source_path: str,
    output_mode: str,
    chapter_problem: str,
    clusters: list[dict],
    study_titles: list[str],
    review_titles: list[str],
    extraction_quality: str,
) -> str:
    title_line = chapter_title
    if "学习笔记" not in title_line:
        title_line = f"{chapter_title}：学习笔记"
    lines = [
        f"# {title_line}",
        "",
        "## 标题与范围",
        f"- 章节：{chapter_title}",
        f"- 来源：`{source_path or '待补充'}`",
        f"- 页码或范围：`{chapter_range or '待补充'}`",
        "- 来源映射：`source-map.md`",
        f"- 提取质量 / 待核对：{extraction_quality or '待补充'}",
        "- 文件编码：`UTF-8`",
        f"- 输出模式：`{output_mode}`",
        "",
        "## 如何使用本笔记",
        "- 第一遍先看：这章解决什么问题、本章知识地图、建议学习路径、起步例子、本章主线。",
        "- 第二遍再看：逐节追踪过程、补齐为什么成立、对照练习与复习入口。",
        "- 做题前确认：能口头复述核心机制，而不是只会背结论。",
        "- 配套练习：`practice.md`",
        "- 配套复习：`review-notes.md`",
        "",
        "## 输出模式与学习策略",
        f"- 当前模式：`{output_mode}`",
        "- 本章默认按初学讲义路线展开：先给入口问题和最小例子，再解释正式结论与为什么成立。",
        "- 高复杂度知识点按“10 到 15 分钟微讲”组织，再汇编成整章讲义。",
        "",
        "## 先修提醒",
        "- 先确认你已经熟悉数组、链表、栈、队列、递归，以及树的基本遍历。",
        "- 如果某个知识点看不懂，先回到它的前置知识点，而不是直接硬背结论。",
        "",
        "## 这章解决什么问题？",
        chapter_problem.strip() or "本章回答：如何表示图、如何遍历图，以及如何在图上完成连通性、依赖关系、最优连接和最短路径分析。",
        "",
        "## 本章知识地图",
    ]
    if clusters:
        for cluster in clusters:
            title = str(cluster.get("title") or "").strip()
            summary = str(cluster.get("summary") or "").strip()
            node_ids = [str(item) for item in cluster.get("node_ids", [])]
            if not title:
                continue
            node_text = "、".join(node_ids) if node_ids else "待补充"
            if summary:
                lines.append(f"- {title}：{summary}（节点：{node_text}）")
            else:
                lines.append(f"- {title}（节点：{node_text}）")
    else:
        lines.append("- 详见 `knowledge-map.json`。")
    lines.extend(
        [
            "",
            "## 建议学习路径",
            f"- 第一遍学习：{' -> '.join(study_titles) if study_titles else '待补充'}",
            f"- 复习回看：{' -> '.join(review_titles) if review_titles else '待补充'}",
            "",
            "## 起步例子 / 章节引子",
            "```text",
            "从一个足够小的图出发，先观察它有哪些点、边、连通块、可能的遍历顺序和最短路问题。",
            "```",
            "- 先观察什么：图上的问题往往先区分“怎么表示”“怎么走”“在优化什么”。",
            "- 看完后至少要能说出什么：同一张图可以同时承载遍历、连通、依赖、最优连接和最短路径问题。",
            "",
            "## 本章主线",
            "1. 先建立图的语言和表示法，知道图和树、线性结构的区别。",
            "2. 再用 DFS / BFS 建立访问机制，理解连通分量、生成树等结构结果从哪里来。",
            "3. 最后再进入图上的最优性与约束问题，如 MST、拓扑序、关键路径和最短路径。",
            "",
            "## 分层学习路线",
            "- 第一遍：只抓主干知识点，先建立地图。",
            "- 第二遍：补齐 why / trace / 边界。",
            "- 复习：优先回顾高复杂度与高频混淆点。",
            "",
            "## 初学者卡点预警",
            "- 不要把“生成树”和“最小生成树”混为一谈。",
            "- 不要把“连通分量”和“强连通分量”混为一谈。",
            "- 不要把“BFS 处理无权最短路”和“Dijkstra 处理非负带权最短路”混为一谈。",
            "",
            "## 小节闭环笔记",
            "",
        ]
    )
    return "\n".join(lines)


def render_section(
    page: dict,
    node: dict,
    node_lookup: dict[str, dict],
    section_index: int,
) -> str:
    section_title = subsection_title_for(page, node, section_index)
    prerequisites = prerequisite_titles(page, node_lookup)
    summary = str(page.get("page_summary") or "").strip()
    learning_goal = str(page.get("learning_goal") or "").strip()
    kind = section_kind(node)
    estimated = page.get("estimated_teaching_minutes") or COMPLEXITY_MINUTES.get(str(page.get("complexity_level") or ""), 10)

    parts = [
        f"### {section_title}",
        f"<!-- page-id: {page.get('page_id', '')} | anchor: {heading_anchor(section_title)} -->",
        f"- 类型：{kind}",
        f"- 预计讲解时长：{estimated} 分钟",
        f"- 前置知识点：{'、'.join(prerequisites) if prerequisites else '无'}",
        f"- 对应练习：{practice_ref_line(page)}",
        f"- 对应复习：{review_ref_line(page)}",
    ]
    basis = source_basis_for_page(page)
    if basis:
        parts.append(f"- 原文依据：{basis}")
    if learning_goal:
        parts.append(f"- 学习目标：{learning_goal}")
    if summary:
        parts.append(f"- 一句话摘要：{summary}")
    parts.append("")
    parts.append(build_kp_table(page, node))

    lookup = block_lookup(page)
    emitted = False
    for block_type in BLOCK_ORDER:
        block = lookup.get(block_type)
        if block or fallback_block_content(page, block_type):
            parts.append(render_block(page, block_type).rstrip())
            parts.append("")
            emitted = True
    if not emitted:
        parts.extend(
            [
                "#### 本节主问题",
                str(page.get("entry_question") or "待补充"),
                "",
                "#### 正式结论 / 定义",
                summary or "待补充",
                "",
                "#### 本节闭卷输出模板",
                learning_goal or summary or "待补充",
                "",
            ]
        )
    return "\n".join(parts).rstrip() + "\n"


def build_closing(chapter_title: str, pages: list[dict], node_lookup: dict[str, dict]) -> str:
    formula_rows: list[str] = []
    compare_rows: list[str] = []
    oral_lines: list[str] = []
    seen_formula: set[str] = set()
    seen_compare: set[tuple[str, str]] = set()

    for page in pages:
        page_title = str(page.get("title") or page.get("page_id") or "").strip()
        node = node_lookup.get(str(page.get("knowledge_point_id") or page.get("page_id") or ""), {})
        for item in node.get("related_formulas", []):
            formula = str(item).strip()
            if formula and formula not in seen_formula:
                seen_formula.add(formula)
                formula_rows.append(f"| {page_title} | `{formula}` | 见对应知识点页 |")
        confusions = node.get("common_confusions", [])
        for confusion in confusions[:2]:
            other = str(node_lookup.get(str(confusion), {}).get("title") or confusion).strip()
            key = tuple(sorted((page_title, other)))
            if page_title and other and key not in seen_compare:
                seen_compare.add(key)
                compare_rows.append(f"| {page_title} | {other} | 见对应页中的“和相邻概念的区别” |")
        goal = str(page.get("learning_goal") or "").strip()
        if page_title and goal:
            oral_lines.append(f"- {page_title}：{goal}")

    if not formula_rows:
        formula_rows.append("| 待补充 | 待补充 | 待补充 |")
    if not compare_rows:
        compare_rows.append("| 待补充 | 待补充 | 待补充 |")
    if not oral_lines:
        oral_lines.append("- 待补充")

    fast_review = [
        "1. 先回看本章知识地图，定位主干知识点。",
        "2. 再挑出所有高复杂度知识点，只看它们的“为什么成立”和“过程追踪 / Trace”。",
        "3. 最后对照 `practice.md` 和 `review-notes.md` 进行闭卷复述与错题回炉。",
    ]

    return "\n".join(
        [
            "## 关键术语与公式速查",
            "| 所属知识点 | 术语 / 公式 | 备注 |",
            "| --- | --- | --- |",
            *formula_rows,
            "",
            "## 实现与代码连接",
            "- 优先在对应知识点页查看“代码 / 实现 / 题型连接”。",
            "- 如果章节中涉及代码实现，建议按知识图谱中的学习路径逐个回看，而不是按文件顶部到底通读代码。",
            "",
            "## 易混概念总对比",
            "| A | B | 关键区别 |",
            "| --- | --- | --- |",
            *compare_rows,
            "",
            "## 闭卷输出模板",
            f"- {chapter_title} 一句话版：先表示图，再理解遍历，最后解决图上的连通、依赖、最优连接和最短路径问题。",
            *oral_lines[:6],
            "",
            "## 10 分钟速读路线",
            *fast_review,
            "",
        ]
    )


def ordered_nodes(knowledge_map: dict) -> list[dict]:
    nodes = [node for node in knowledge_map.get("nodes", []) if isinstance(node, dict)]
    lookup = {str(node.get("id")): node for node in nodes if node.get("id")}
    ordered_ids: list[str] = []
    for path_name in ("study", "review"):
        for node_id in knowledge_map.get("recommended_paths", {}).get(path_name, []):
            key = str(node_id)
            if key in lookup and key not in ordered_ids:
                ordered_ids.append(key)

    def rank(node: dict) -> tuple[int, str]:
        order = {"high": 0, "medium": 1, "low": 2}
        importance = str(node.get("importance_level") or "medium").lower()
        return order.get(importance, 3), str(node.get("id") or "")

    remaining = sorted((node for key, node in lookup.items() if key not in ordered_ids), key=rank)
    return [lookup[key] for key in ordered_ids] + remaining


def page_sort_key(page: dict, node: dict, fallback_rank: int) -> tuple[tuple[int, ...], int, str]:
    numeric = numeric_parts_for(page, node)
    if numeric:
        return numeric, 0, str(page.get("page_id") or "")
    return (9999, fallback_rank), 1, str(page.get("page_id") or "")


def sync_anchors(
    chapter_dir: Path,
    knowledge_map: dict,
    knowledge_pages: dict,
    page_titles: dict[str, str],
) -> None:
    updated_nodes = False
    for node in knowledge_map.get("nodes", []):
        if not isinstance(node, dict):
            continue
        node_id = str(node.get("id") or "")
        title = page_titles.get(node_id)
        if not title:
            continue
        anchor = heading_anchor(title)
        notes_anchor = f"detailed-notes#{anchor}"
        if page_number := str(node.get("section_number") or ""):
            node["section_number"] = page_number
        if node.get("section_anchor") != anchor:
            node["section_anchor"] = anchor
            updated_nodes = True
        if node.get("notes_anchor") != notes_anchor:
            node["notes_anchor"] = notes_anchor
            updated_nodes = True

    updated_pages = False
    for page in knowledge_pages.get("pages", []):
        if not isinstance(page, dict):
            continue
        page_id = str(page.get("knowledge_point_id") or page.get("page_id") or "")
        title = page_titles.get(page_id)
        if not title:
            continue
        notes_anchor = f"detailed-notes#{heading_anchor(title)}"
        if page_number := str(page.get("__section_number") or ""):
            page["section_number"] = page_number
        if page.get("notes_anchor") != notes_anchor:
            page["notes_anchor"] = notes_anchor
            updated_pages = True

    if updated_nodes:
        dump_json(chapter_dir / "knowledge-map.json", knowledge_map)
    if updated_pages:
        dump_json(chapter_dir / "knowledge-pages.json", knowledge_pages)


def update_meta(chapter_dir: Path, overwrite: bool) -> None:
    meta_path = chapter_dir / "_meta.json"
    if not meta_path.exists():
        return
    meta = load_json(meta_path)
    files = meta.get("files")
    if not isinstance(files, list):
        files = []
    if "detailed-notes.md" not in files:
        files.append("detailed-notes.md")
    if overwrite:
        meta["files"] = files
        dump_json(meta_path, meta)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compile detailed-notes.md from knowledge-pages.json."
    )
    parser.add_argument(
        "chapter_dir",
        help="Chapter directory containing knowledge-pages.json and knowledge-map.json.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite an existing detailed-notes.md.",
    )
    parser.add_argument(
        "--sync-anchors",
        action="store_true",
        help="Update notes anchors in knowledge-map.json and knowledge-pages.json to match compiled headings.",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON summary.")
    args = parser.parse_args()

    chapter_dir = Path(args.chapter_dir).resolve()
    pages_path = chapter_dir / "knowledge-pages.json"
    knowledge_map_path = chapter_dir / "knowledge-map.json"
    source_map_path = chapter_dir / "source-map.md"
    meta_path = chapter_dir / "_meta.json"
    out_path = chapter_dir / "detailed-notes.md"

    for path in (pages_path, knowledge_map_path):
        if not path.exists():
            raise SystemExit(f"missing file: {path}")
    if out_path.exists() and not args.overwrite:
        raise SystemExit(f"target exists: {out_path}; use --overwrite")

    knowledge_pages = load_json(pages_path)
    knowledge_map = load_json(knowledge_map_path)
    meta = load_json(meta_path) if meta_path.exists() else {}
    source_map_text = read_text(source_map_path) if source_map_path.exists() else ""
    chapter_number_match = re.match(r"^(\d+)", str(knowledge_map.get("chapter_id") or chapter_dir.name))
    chapter_number = int(chapter_number_match.group(1)) if chapter_number_match else None

    pages = [page for page in knowledge_pages.get("pages", []) if isinstance(page, dict)]
    if not pages:
        raise SystemExit(f"no pages found in: {pages_path}")

    node_lookup = {
        str(node.get("id")): node
        for node in knowledge_map.get("nodes", [])
        if isinstance(node, dict) and node.get("id")
    }
    section_numbers = infer_section_numbers(
        pages=pages,
        node_lookup=node_lookup,
        source_rows=parse_source_rows(source_map_text),
        chapter_number=chapter_number,
    )
    for page in pages:
        page_id = str(page.get("knowledge_point_id") or page.get("page_id") or "")
        if section_numbers.get(page_id):
            page["__section_number"] = section_numbers[page_id]
            node = node_lookup.get(page_id)
            if node is not None:
                node["section_number"] = section_numbers[page_id]

    ordered = ordered_nodes(knowledge_map)
    page_lookup = {
        str(page.get("knowledge_point_id") or page.get("page_id") or ""): page
        for page in pages
    }
    recommended_rank = {str(node.get("id") or ""): index for index, node in enumerate(ordered)}
    ordered_pages = sorted(
        pages,
        key=lambda page: page_sort_key(
            page,
            node_lookup.get(str(page.get("knowledge_point_id") or page.get("page_id") or ""), {}),
            recommended_rank.get(str(page.get("knowledge_point_id") or page.get("page_id") or ""), 9999),
        ),
    )

    study_titles = []
    for node_id in knowledge_map.get("recommended_paths", {}).get("study", []):
        title = str(node_lookup.get(str(node_id), {}).get("title") or "").strip()
        if title:
            study_titles.append(title)
    review_titles = []
    for node_id in knowledge_map.get("recommended_paths", {}).get("review", []):
        title = str(node_lookup.get(str(node_id), {}).get("title") or "").strip()
        if title:
            review_titles.append(title)

    chapter_title = str(meta.get("title") or knowledge_map.get("chapter_title") or knowledge_pages.get("chapter_title") or chapter_dir.name)
    chapter_problem = str(knowledge_map.get("chapter_problem") or "").strip()
    chapter_range = str(meta.get("chapter") or "").strip() or chapter_range_from_source_map(source_map_text)
    source_path = str(meta.get("source") or "").strip() or source_path_from_source_map(source_map_text)
    output_mode = str(meta.get("output_mode") or knowledge_pages.get("output_mode") or knowledge_map.get("output_mode") or "beginner_lecture")
    extraction_quality = extraction_quality_from_source_map(source_map_text)

    intro = build_intro(
        chapter_title=chapter_title,
        chapter_range=chapter_range,
        source_path=source_path,
        output_mode=output_mode,
        chapter_problem=chapter_problem,
        clusters=[item for item in knowledge_map.get("clusters", []) if isinstance(item, dict)],
        study_titles=study_titles,
        review_titles=review_titles,
        extraction_quality=extraction_quality,
    )

    sections: list[str] = []
    page_titles: dict[str, str] = {}
    for index, page in enumerate(ordered_pages, start=1):
        page_id = str(page.get("knowledge_point_id") or page.get("page_id") or "")
        node = node_lookup.get(page_id, {})
        section_title = subsection_title_for(page, node, index)
        page_titles[page_id] = section_title
        sections.append(render_section(page, node, node_lookup, index))

    closing = build_closing(chapter_title, ordered_pages, node_lookup)
    content = intro + "\n".join(sections) + "\n" + closing
    write_text(out_path, content.rstrip() + "\n")

    if args.sync_anchors:
        sync_anchors(chapter_dir, knowledge_map, knowledge_pages, page_titles)
    update_meta(chapter_dir, overwrite=True)

    summary = {
        "chapter_dir": str(chapter_dir),
        "output": str(out_path),
        "page_count": len(ordered_pages),
        "anchors_synced": bool(args.sync_anchors),
    }
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(f"compiled {len(ordered_pages)} pages -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
