#!/usr/bin/env python3
"""Render lesson-pack Markdown files into a lightweight static course site."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from html import escape
from pathlib import Path
from typing import Iterable


SECTION_ORDER = [
    ("00-learning-path.md", "先学", "学习路径"),
    ("01-lesson-notes.md", "讲义", "课程讲义"),
    ("02-active-recall.md", "自测", "主动回忆"),
    ("03-exercises.md", "练习", "练习与答案"),
    ("04-glossary.md", "术语", "术语与公式"),
    ("05-review-plan.md", "复习", "复习计划"),
    ("06-memory-cards.md", "卡片", "记忆卡片"),
    ("07-code-extracts.md", "代码", "代码摘录"),
    ("source-map.md", "来源", "来源映射"),
]

VNEXT_SECTION_ORDER = [
    ("detailed-notes.md", "讲义", "详细讲义"),
    ("practice.md", "练习", "对应练习"),
    ("review-notes.md", "复习", "复习笔记"),
    ("source-map.md", "来源", "来源映射"),
]

TAB_GROUPS = [
    ("primer", "先学", ["00-learning-path.md", "01-lesson-notes.md"]),
    ("recall", "自测", ["02-active-recall.md"]),
    ("practice", "练习", ["03-exercises.md"]),
    ("review", "复习", ["05-review-plan.md", "06-memory-cards.md"]),
    ("glossary", "术语", ["04-glossary.md"]),
    ("code", "代码", ["07-code-extracts.md"]),
    ("source", "来源", ["source-map.md"]),
]

VNEXT_TAB_GROUPS = [
    ("primer", "讲义", ["detailed-notes.md"]),
    ("practice", "练习", ["practice.md"]),
    ("review", "复习", ["review-notes.md"]),
    ("source", "来源", ["source-map.md"]),
]

STAGE_MODES = {
    "primer": ("study",),
    "recall": ("study", "review"),
    "practice": ("study", "review"),
    "review": ("review",),
    "glossary": ("review",),
    "code": ("study",),
    "source": ("study", "review"),
}

FILE_LABELS = {
    name: (short_label, long_label)
    for name, short_label, long_label in SECTION_ORDER + VNEXT_SECTION_ORDER
}

INLINE_CODE_RE = re.compile(r"`([^`]+)`")
BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")
ITALIC_RE = re.compile(r"(?<!\*)\*([^*\n]+)\*(?!\*)")
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")


@dataclass
class Chapter:
    chapter_id: str
    title: str
    chapter_range: str
    output_mode: str
    output_format: str
    created_at: str
    path: Path
    files: list[Path]
    knowledge_map_path: Path | None
    knowledge_pages_path: Path | None
    note_lines: int
    note_chars: int


def section_order_for(output_format: str) -> list[tuple[str, str, str]]:
    return VNEXT_SECTION_ORDER if output_format == "vnext" else SECTION_ORDER


def tab_groups_for(output_format: str) -> list[tuple[str, str, list[str]]]:
    return VNEXT_TAB_GROUPS if output_format == "vnext" else TAB_GROUPS


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


def slug_to_title(value: str) -> str:
    parts = [part for part in value.split("-") if part]
    return " ".join(part.capitalize() for part in parts) or value


def load_json(path: Path) -> dict:
    return json.loads(read_text(path))


def discover_chapters(lessons_root: Path) -> list[Chapter]:
    chapters_root = lessons_root / "chapters"
    chapters: list[Chapter] = []
    for chapter_dir in sorted(p for p in chapters_root.iterdir() if p.is_dir()):
        meta_path = chapter_dir / "_meta.json"
        meta = load_json(meta_path) if meta_path.exists() else {}
        title = str(meta.get("title") or slug_to_title(chapter_dir.name))
        chapter_range = str(meta.get("chapter") or "未标注范围")
        output_mode = str(meta.get("output_mode") or "beginner_lecture")
        output_format = str(meta.get("output_format") or "")
        if not output_format:
            output_format = "vnext" if (chapter_dir / "detailed-notes.md").exists() else "legacy"
        created_at = str(meta.get("created_at") or "")
        files = [
            chapter_dir / name
            for name, _, _ in section_order_for(output_format)
            if (chapter_dir / name).exists()
        ]
        note_candidates = (
            ["detailed-notes.md", "01-lesson-notes.md"]
            if output_format == "vnext"
            else ["01-lesson-notes.md", "detailed-notes.md"]
        )
        note_path = next((chapter_dir / name for name in note_candidates if (chapter_dir / name).exists()), None)
        note_text = read_text(note_path) if note_path else ""
        knowledge_map_path = chapter_dir / "knowledge-map.json"
        knowledge_pages_path = chapter_dir / "knowledge-pages.json"
        chapters.append(
            Chapter(
                chapter_id=chapter_dir.name,
                title=title,
                chapter_range=chapter_range,
                output_mode=output_mode,
                output_format=output_format,
                created_at=created_at,
                path=chapter_dir,
                files=files,
                knowledge_map_path=knowledge_map_path if knowledge_map_path.exists() else None,
                knowledge_pages_path=knowledge_pages_path if knowledge_pages_path.exists() else None,
                note_lines=note_text.count("\n") + (1 if note_text else 0),
                note_chars=len(note_text),
            )
        )
    return chapters


def inline_markdown(text: str) -> str:
    text = escape(text)
    text = LINK_RE.sub(r'<a href="\2">\1</a>', text)
    text = INLINE_CODE_RE.sub(r"<code>\1</code>", text)
    text = BOLD_RE.sub(r"<strong>\1</strong>", text)
    text = ITALIC_RE.sub(r"<em>\1</em>", text)
    return text


def slugify(value: str) -> str:
    value = re.sub(r"<[^>]+>", "", value).strip().lower()
    value = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    return value or "section"


def consume_paragraph(lines: list[str], start: int) -> tuple[str, int]:
    buffer: list[str] = []
    index = start
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if not stripped:
            break
        if stripped.startswith(("#", "|", "- ", "* ", "> ", "```")):
            break
        if re.match(r"\d+\.\s", stripped):
            break
        buffer.append(stripped)
        index += 1
    return "<p>" + inline_markdown(" ".join(buffer)) + "</p>", index


def render_table(block: list[str]) -> str:
    rows = [
        [inline_markdown(cell.strip()) for cell in line.strip().strip("|").split("|")]
        for line in block
    ]
    header = rows[0]
    body = rows[2:] if len(rows) > 2 else []
    parts = ['<div class="table-wrap"><table><thead><tr>']
    parts.extend(f"<th>{cell}</th>" for cell in header)
    parts.append("</tr></thead><tbody>")
    for row in body:
        parts.append("<tr>")
        parts.extend(f"<td>{cell}</td>" for cell in row)
        parts.append("</tr>")
    parts.append("</tbody></table></div>")
    return "".join(parts)


def markdown_to_html(text: str) -> str:
    lines = text.replace("\r\n", "\n").split("\n")
    parts: list[str] = []
    index = 0
    in_code = False
    code_lines: list[str] = []
    list_mode: str | None = None

    def close_list() -> None:
        nonlocal list_mode
        if list_mode:
            parts.append(f"</{list_mode}>")
            list_mode = None

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()

        if in_code:
            if stripped.startswith("```"):
                parts.append("<pre><code>" + escape("\n".join(code_lines)).rstrip() + "</code></pre>")
                in_code = False
                code_lines = []
            else:
                code_lines.append(line)
            index += 1
            continue

        if not stripped:
            close_list()
            index += 1
            continue

        if stripped.startswith("```"):
            close_list()
            in_code = True
            code_lines = []
            index += 1
            continue

        if stripped.startswith("#"):
            close_list()
            level = min(len(stripped) - len(stripped.lstrip("#")), 6)
            content = stripped[level:].strip()
            anchor = slugify(content)
            parts.append(f"<h{level} id=\"{anchor}\">{inline_markdown(content)}</h{level}>")
            index += 1
            continue

        if stripped.startswith("> "):
            close_list()
            parts.append(f"<blockquote>{inline_markdown(stripped[2:].strip())}</blockquote>")
            index += 1
            continue

        if stripped.startswith("|") and index + 1 < len(lines):
            next_line = lines[index + 1].strip()
            if next_line.startswith("|") and set(next_line.replace("|", "").replace(" ", "")) <= {"-", ":"}:
                close_list()
                table_block = [line, lines[index + 1]]
                index += 2
                while index < len(lines) and lines[index].strip().startswith("|"):
                    table_block.append(lines[index])
                    index += 1
                parts.append(render_table(table_block))
                continue

        unordered = stripped.startswith("- ") or stripped.startswith("* ")
        ordered = bool(re.match(r"\d+\.\s", stripped))
        if unordered or ordered:
            desired = "ol" if ordered else "ul"
            if list_mode != desired:
                close_list()
                parts.append(f"<{desired}>")
                list_mode = desired
            item_text = re.sub(r"^(- |\* |\d+\.\s)", "", stripped)
            parts.append(f"<li>{inline_markdown(item_text)}</li>")
            index += 1
            continue

        close_list()
        paragraph, next_index = consume_paragraph(lines, index)
        if next_index == index:
            parts.append(f"<p>{inline_markdown(stripped)}</p>")
            index += 1
        else:
            parts.append(paragraph)
            index = next_index

    close_list()
    if in_code:
        parts.append("<pre><code>" + escape("\n".join(code_lines)).rstrip() + "</code></pre>")
    return "\n".join(parts)


def file_label(name: str) -> tuple[str, str]:
    return FILE_LABELS.get(name, (name, name))


def anchor_href(anchor: str | None, fallback: str) -> str:
    if not anchor:
        return fallback
    fragment = anchor.split("#", 1)[1] if "#" in anchor else anchor
    fragment = fragment.strip()
    if not fragment:
        return fallback
    return f"#{escape(fragment)}"


def ordered_knowledge_nodes(data: dict, node_lookup: dict[str, dict]) -> list[dict]:
    ordered_ids: list[str] = []
    for path_name in ("study", "review"):
        for node_id in data.get("recommended_paths", {}).get(path_name, []):
            node_key = str(node_id)
            if node_key in node_lookup and node_key not in ordered_ids:
                ordered_ids.append(node_key)

    def importance_rank(node: dict) -> tuple[int, str]:
        order = {"high": 0, "medium": 1, "low": 2}
        importance = str(node.get("importance_level") or "medium").lower()
        return order.get(importance, 3), str(node.get("id") or "")

    remaining = sorted(
        (node for node_id, node in node_lookup.items() if node_id not in ordered_ids),
        key=importance_rank,
    )
    return [node_lookup[node_id] for node_id in ordered_ids] + remaining


def render_knowledge_map(chapter: Chapter) -> str:
    if not chapter.knowledge_map_path:
        return ""

    try:
        data = load_json(chapter.knowledge_map_path)
    except json.JSONDecodeError:
        return ""

    nodes = [node for node in data.get("nodes", []) if isinstance(node, dict)]
    if not nodes:
        return ""

    node_lookup = {str(node.get("id")): node for node in nodes if node.get("id")}
    chapter_problem = str(data.get("chapter_problem") or "").strip()
    study_ids = [str(node_id) for node_id in data.get("recommended_paths", {}).get("study", [])]
    review_ids = [str(node_id) for node_id in data.get("recommended_paths", {}).get("review", [])]

    def render_path_panel(path_title: str, node_ids: list[str], anchor_key: str, fallback: str) -> str:
        pills: list[str] = []
        for index, node_id in enumerate(node_ids, start=1):
            node = node_lookup.get(node_id)
            if not node:
                continue
            pills.append(
                f"""
                <a class="path-pill" href="{anchor_href(str(node.get(anchor_key) or ""), fallback)}">
                  <span>{index:02d}</span>
                  <strong>{escape(str(node.get("title") or node_id))}</strong>
                </a>
                """
            )
        if not pills:
            return ""
        return f"""
        <section class="path-panel">
          <span class="eyebrow">{path_title}</span>
          <div class="path-pill-row">
            {''.join(pills)}
          </div>
        </section>
        """

    study_panel = render_path_panel("学习路径", study_ids, "notes_anchor", "#detailed-notes")
    review_panel = render_path_panel("复习路径", review_ids, "review_anchor", "#review-notes")

    clusters = [cluster for cluster in data.get("clusters", []) if isinstance(cluster, dict)]
    cluster_cards: list[str] = []
    for cluster in clusters:
        cluster_nodes = [
            escape(str(node_lookup[node_id].get("title") or node_id))
            for node_id in [str(node_id) for node_id in cluster.get("node_ids", [])]
            if node_id in node_lookup
        ]
        cluster_cards.append(
            f"""
            <article class="mini-card">
              <span class="eyebrow">知识簇</span>
              <h3>{escape(str(cluster.get("title") or ""))}</h3>
              <p>{inline_markdown(str(cluster.get("summary") or ""))}</p>
              <p class="mini-meta">{escape(' / '.join(cluster_nodes[:5]))}</p>
            </article>
            """
        )

    node_cards: list[str] = []
    for node in ordered_knowledge_nodes(data, node_lookup):
        title = str(node.get("title") or node.get("id") or "")
        summary = str(node.get("summary") or "").strip() or title
        complexity = str(node.get("complexity_level") or "")
        importance = str(node.get("importance_level") or "")
        badges = [
            f'<span class="meta-badge">{escape(complexity)}</span>' if complexity else "",
            f'<span class="meta-badge">{escape(importance)}</span>' if importance else "",
        ]
        note_link = anchor_href(str(node.get("notes_anchor") or ""), "#detailed-notes")
        practice_link = anchor_href(str(node.get("practice_anchor") or ""), "#practice")
        review_link = anchor_href(str(node.get("review_anchor") or ""), "#review-notes")
        node_cards.append(
            f"""
            <article class="knowledge-node-card">
              <div class="doc-card-head">
                <div>
                  <span class="eyebrow">知识点</span>
                  <h3>{escape(title)}</h3>
                </div>
                <span class="file-chip">{escape(str(node.get("id") or ""))}</span>
              </div>
              <p>{inline_markdown(summary)}</p>
              <div class="meta-badge-row">
                {''.join(badge for badge in badges if badge)}
              </div>
              <div class="knowledge-link-row">
                <a class="outline-link" href="{note_link}">讲义</a>
                <a class="outline-link" href="{practice_link}">练习</a>
                <a class="outline-link" href="{review_link}">复习</a>
              </div>
            </article>
            """
        )

    cluster_block = f'<div class="mini-card-grid">{"".join(cluster_cards)}</div>' if cluster_cards else ""
    problem_block = f'<p class="knowledge-map-problem">{inline_markdown(chapter_problem)}</p>' if chapter_problem else ""
    return f"""
    <section class="knowledge-map-board" id="knowledge-map">
      <div class="section-topline">
        <span class="eyebrow">知识图谱</span>
        <h2>先看本章地图，再读细节</h2>
      </div>
      {problem_block}
      <div class="knowledge-map-shell">
        <div class="path-stack">
          {study_panel}
          {review_panel}
        </div>
        <div class="knowledge-node-grid">
          {''.join(node_cards)}
        </div>
      </div>
      {cluster_block}
    </section>
    """


def render_page_block_content(content: object) -> str:
    if isinstance(content, list):
        items = [str(item).strip() for item in content if str(item).strip()]
        if not items:
            return ""
        return "<ul>" + "".join(f"<li>{inline_markdown(item)}</li>" for item in items) + "</ul>"
    text = str(content or "").strip()
    if not text:
        return ""
    return markdown_to_html(text)


def render_block_badge(block_type: str) -> str:
    label_map = {
        "hook": "问题",
        "minimum_example": "例子",
        "intuition": "直觉",
        "formal_statement": "结论",
        "why_it_holds": "为什么",
        "trace": "过程",
        "comparison": "对比",
        "confusion_fix": "易错",
        "implementation_bridge": "实现",
        "closed_book_retell": "闭卷",
        "mini_check": "自测",
        "recap": "总结",
    }
    return label_map.get(block_type, block_type)


def render_knowledge_pages(chapter: Chapter) -> str:
    if not chapter.knowledge_pages_path:
        return ""
    try:
        data = load_json(chapter.knowledge_pages_path)
    except json.JSONDecodeError:
        return ""

    pages = [page for page in data.get("pages", []) if isinstance(page, dict)]
    if not pages:
        return ""

    nav_cards: list[str] = []
    article_cards: list[str] = []
    for index, page in enumerate(pages):
        page_id = str(page.get("page_id") or f"page-{index + 1}")
        title = str(page.get("title") or page_id)
        summary = str(page.get("page_summary") or page.get("entry_question") or "").strip()
        complexity = str(page.get("complexity_level") or "").strip()
        importance = str(page.get("importance_level") or "").strip()
        minutes = page.get("estimated_teaching_minutes")
        badges = []
        for item in (complexity, importance):
            if item:
                badges.append(f'<span class="meta-badge">{escape(item)}</span>')
        if minutes:
            badges.append(f'<span class="meta-badge">{escape(str(minutes))} min</span>')

        nav_cards.append(
            f"""
            <button class="kp-nav-card" type="button" data-kp-target="{escape(page_id)}" aria-pressed="{str(index == 0).lower()}">
              <span>{index + 1:02d}</span>
              <strong>{escape(title)}</strong>
              <small>{inline_markdown(summary or "打开这一页知识点讲解")}</small>
            </button>
            """
        )

        block_cards: list[str] = []
        for block in page.get("blocks", []):
            if not isinstance(block, dict):
                continue
            block_type = str(block.get("type") or "")
            block_title = str(block.get("title") or render_block_badge(block_type))
            block_html = render_page_block_content(block.get("content"))
            if not block_html:
                continue
            block_cards.append(
                f"""
                <article class="kp-block kp-block-{escape(block_type or 'content')}">
                  <div class="kp-block-head">
                    <span class="kp-block-badge">{escape(render_block_badge(block_type))}</span>
                    <h3>{escape(block_title)}</h3>
                  </div>
                  <div class="markdown-body">{block_html}</div>
                </article>
                """
            )

        practice_refs = [str(item) for item in page.get("practice_refs", []) if str(item).strip()]
        review_refs = [str(item) for item in page.get("review_refs", []) if str(item).strip()]
        practice_html = ""
        if practice_refs:
            practice_html = (
                '<div class="kp-ref-row"><span class="eyebrow">练习关联</span><p>'
                + " / ".join(escape(item) for item in practice_refs)
                + "</p></div>"
            )
        review_html = ""
        if review_refs:
            review_html = (
                '<div class="kp-ref-row"><span class="eyebrow">复习关联</span><p>'
                + " / ".join(escape(item) for item in review_refs)
                + "</p></div>"
            )

        article_cards.append(
            f"""
            <article class="kp-page" id="kp-{escape(page_id)}" data-kp-page="{escape(page_id)}" data-active="{str(index == 0).lower()}">
              <header class="kp-page-head">
                <div>
                  <span class="eyebrow">知识点页 {index + 1:02d}</span>
                  <h2>{escape(title)}</h2>
                </div>
                <div class="meta-badge-row">
                  {''.join(badges)}
                </div>
              </header>
              <div class="focus-callout">
                <span class="eyebrow">入口问题</span>
                <p>{inline_markdown(str(page.get("entry_question") or summary or title))}</p>
              </div>
              <div class="kp-page-goal">
                <div class="kp-ref-row">
                  <span class="eyebrow">学完要会</span>
                  <p>{inline_markdown(str(page.get("learning_goal") or summary or title))}</p>
                </div>
                {practice_html}
                {review_html}
              </div>
              <div class="kp-block-grid">
                {''.join(block_cards)}
              </div>
            </article>
            """
        )

    return f"""
    <section class="knowledge-pages-board" id="knowledge-pages" data-kp-root>
      <div class="section-topline">
        <span class="eyebrow">知识点翻页</span>
        <h2>按知识点逐页阅读，不再在整章 Markdown 里来回滚动</h2>
      </div>
      <div class="knowledge-pages-shell">
        <aside class="kp-nav">
          <div class="kp-nav-head">
            <span class="eyebrow">快速翻页</span>
            <p>每一页都是一个可以独立讲清的知识点。</p>
          </div>
          <div class="kp-nav-list">
            {''.join(nav_cards)}
          </div>
        </aside>
        <div class="kp-stage">
          <div class="kp-toolbar">
            <button class="inline-tool" type="button" data-kp-move="prev">上一页</button>
            <button class="inline-tool" type="button" data-kp-move="next">下一页</button>
          </div>
          <div class="kp-page-stack">
            {''.join(article_cards)}
          </div>
        </div>
      </div>
    </section>
    """


def render_text_list(items: list[str], empty: str = "") -> str:
    normalized = [str(item).strip() for item in items if str(item).strip()]
    if not normalized:
        return f"<p>{inline_markdown(empty)}</p>" if empty else ""
    return "<ul>" + "".join(f"<li>{inline_markdown(item)}</li>" for item in normalized) + "</ul>"


def page_meta_badges(page: dict) -> list[str]:
    badges: list[str] = []
    for key in ("complexity_level", "importance_level", "teaching_profile", "clarity_risk"):
        value = str(page.get(key) or "").strip()
        if value:
            badges.append(f'<span class="meta-badge">{escape(value)}</span>')
    minutes = page.get("estimated_teaching_minutes")
    if minutes:
        badges.append(f'<span class="meta-badge">{escape(str(minutes))} min</span>')
    return badges


def render_teaching_contract(page: dict) -> str:
    sections = [
        ("Must Answer", [str(item) for item in page.get("must_answer", []) if str(item).strip()]),
        ("Exit Outcomes", [str(item) for item in page.get("exit_outcomes", []) if str(item).strip()]),
        ("Failure Signals", [str(item) for item in page.get("failure_signals", []) if str(item).strip()]),
        ("Prerequisites", [str(item) for item in page.get("prerequisites", []) if str(item).strip()]),
        ("Source Refs", [str(item) for item in page.get("source_refs", []) if str(item).strip()]),
    ]
    cards: list[str] = []
    for title, items in sections:
        if not items:
            continue
        cards.append(
            f"""
            <article class="mini-card">
              <span class="eyebrow">Teaching Contract</span>
              <h3>{escape(title)}</h3>
              {render_text_list(items)}
            </article>
            """
        )
    if not cards:
        return ""
    return f'<div class="mini-card-grid kp-contract-grid">{"".join(cards)}</div>'


def render_page_summary_chips(page: dict) -> str:
    items = [
        ("Page Kind", str(page.get("page_kind") or "").strip()),
        ("Profile", str(page.get("teaching_profile") or "").strip()),
        ("Risk", str(page.get("clarity_risk") or "").strip()),
    ]
    chips = [
        f'<span class="meta-badge">{escape(label)}: {escape(value)}</span>'
        for label, value in items
        if value
    ]
    if not chips:
        return ""
    return f'<div class="meta-badge-row">{"".join(chips)}</div>'


def render_knowledge_pages(chapter: Chapter) -> str:
    if not chapter.knowledge_pages_path:
        return ""
    try:
        data = load_json(chapter.knowledge_pages_path)
    except json.JSONDecodeError:
        return ""

    pages = [page for page in data.get("pages", []) if isinstance(page, dict)]
    if not pages:
        return ""

    nav_cards: list[str] = []
    article_cards: list[str] = []
    total_pages = len(pages)

    for index, page in enumerate(pages):
        page_id = str(page.get("page_id") or f"page-{index + 1}")
        title = str(page.get("title") or page_id)
        summary = str(page.get("page_summary") or page.get("entry_question") or "").strip()
        badges = page_meta_badges(page)
        chip_row = render_page_summary_chips(page)
        contract_html = render_teaching_contract(page)

        nav_cards.append(
            f"""
            <button class="kp-nav-card" type="button" data-kp-target="{escape(page_id)}" aria-pressed="{str(index == 0).lower()}" data-kp-index="{index}">
              <span>{index + 1:02d}</span>
              <strong>{escape(title)}</strong>
              <small>{inline_markdown(summary or "Open this knowledge page")}</small>
            </button>
            """
        )

        block_cards: list[str] = []
        for block in page.get("blocks", []):
            if not isinstance(block, dict):
                continue
            block_type = str(block.get("type") or "")
            block_title = str(block.get("title") or render_block_badge(block_type))
            block_html = render_page_block_content(block.get("content"))
            if not block_html:
                continue
            block_cards.append(
                f"""
                <article class="kp-block kp-block-{escape(block_type or 'content')}" data-block-type="{escape(block_type)}">
                  <div class="kp-block-head">
                    <span class="kp-block-badge">{escape(render_block_badge(block_type))}</span>
                    <h3>{escape(block_title)}</h3>
                  </div>
                  <div class="markdown-body">{block_html}</div>
                </article>
                """
            )

        practice_refs = [str(item) for item in page.get("practice_refs", []) if str(item).strip()]
        review_refs = [str(item) for item in page.get("review_refs", []) if str(item).strip()]
        practice_html = ""
        if practice_refs:
            practice_html = (
                '<div class="kp-ref-row"><span class="eyebrow">Practice Links</span><p>'
                + " / ".join(escape(item) for item in practice_refs)
                + "</p></div>"
            )
        review_html = ""
        if review_refs:
            review_html = (
                '<div class="kp-ref-row"><span class="eyebrow">Review Links</span><p>'
                + " / ".join(escape(item) for item in review_refs)
                + "</p></div>"
            )

        article_cards.append(
            f"""
            <article class="kp-page" id="kp-{escape(page_id)}" data-kp-page="{escape(page_id)}" data-active="{str(index == 0).lower()}" data-kp-index="{index}">
              <header class="kp-page-head">
                <div>
                  <span class="eyebrow">Knowledge Page {index + 1:02d} / {total_pages:02d}</span>
                  <h2>{escape(title)}</h2>
                </div>
                <div class="meta-badge-row">
                  {''.join(badges)}
                </div>
              </header>
              {chip_row}
              <div class="focus-callout">
                <span class="eyebrow">Entry Question</span>
                <p>{inline_markdown(str(page.get("entry_question") or summary or title))}</p>
              </div>
              <div class="kp-page-goal">
                <div class="kp-ref-row">
                  <span class="eyebrow">Learning Goal</span>
                  <p>{inline_markdown(str(page.get("learning_goal") or summary or title))}</p>
                </div>
                {practice_html}
                {review_html}
              </div>
              {contract_html}
              <div class="kp-block-grid">
                {''.join(block_cards)}
              </div>
            </article>
            """
        )

    return f"""
    <section class="knowledge-pages-board" id="knowledge-pages" data-kp-root>
      <div class="section-topline">
        <span class="eyebrow">Knowledge Pages</span>
        <h2>Read one knowledge point at a time instead of scrolling through the whole chapter</h2>
      </div>
      <div class="knowledge-pages-shell">
        <aside class="kp-nav">
          <div class="kp-nav-head">
            <span class="eyebrow">Quick Flip</span>
            <p>Each page is a standalone knowledge point. Start from the entry question, then unfold the full explanation.</p>
          </div>
          <div class="kp-nav-list">
            {''.join(nav_cards)}
          </div>
        </aside>
        <div class="kp-stage">
          <div class="kp-toolbar">
            <button class="inline-tool" type="button" data-kp-move="prev">Previous</button>
            <button class="inline-tool" type="button" data-kp-move="next">Next</button>
            <span class="meta-badge" data-kp-progress>1 / {total_pages}</span>
          </div>
          <div class="kp-page-stack">
            {''.join(article_cards)}
          </div>
        </div>
      </div>
    </section>
    """


def split_markdown_sections(text: str) -> list[tuple[int, str, str]]:
    sections: list[tuple[int, str, str]] = []
    current_level = 0
    current_title = ""
    buffer: list[str] = []
    for line in text.replace("\r\n", "\n").split("\n"):
        match = HEADING_RE.match(line.strip())
        if match:
            if current_title or buffer:
                sections.append((current_level, current_title, "\n".join(buffer).strip()))
            current_level = len(match.group(1))
            current_title = match.group(2).strip()
            buffer = []
        else:
            buffer.append(line)
    if current_title or buffer:
        sections.append((current_level, current_title, "\n".join(buffer).strip()))
    return sections


def heading_has(title: str, *keywords: str) -> bool:
    lowered = title.lower()
    return any(keyword.lower() in lowered for keyword in keywords)


def clean_line_for_summary(line: str) -> str:
    stripped = re.sub(r"^[-*]\s*", "", line.strip())
    stripped = re.sub(r"^\d+\.\s*", "", stripped)
    return stripped


def extract_first_paragraph(text: str) -> str:
    for chunk in re.split(r"\n\s*\n", text.strip()):
        lines = [clean_line_for_summary(line) for line in chunk.splitlines()]
        cleaned = " ".join(line for line in lines if line)
        if not cleaned:
            continue
        if cleaned.startswith("|") or cleaned.startswith("```"):
            continue
        return cleaned
    return ""


def extract_bullet_lines(text: str) -> list[str]:
    items: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            items.append(clean_line_for_summary(stripped))
    return [item for item in items if item]


def summarize_block(text: str) -> str:
    paragraph = extract_first_paragraph(text)
    if paragraph:
        return paragraph
    bullets = extract_bullet_lines(text)
    if bullets:
        return bullets[0]
    for line in text.splitlines():
        stripped = clean_line_for_summary(line)
        if stripped and not stripped.startswith("|") and not stripped.startswith("```"):
            return stripped
    return ""


def build_outline_links(
    sections: list[tuple[int, str, str]],
    *,
    levels: tuple[int, ...],
    title: str,
    skip_keywords: tuple[str, ...] = (),
) -> str:
    items: list[str] = []
    for level, heading, _ in sections:
        if level not in levels or not heading:
            continue
        if skip_keywords and heading_has(heading, *skip_keywords):
            continue
        items.append(
            f'<a class="outline-link outline-level-{level}" href="#{slugify(heading)}">{escape(heading)}</a>'
        )
    if not items:
        return ""
    return f"""
    <nav class="outline-card">
      <span class="eyebrow">章节目录</span>
      <h3>{escape(title)}</h3>
      <div class="outline-links">
        {''.join(items)}
      </div>
    </nav>
    """


def parse_markdown_table(text: str) -> tuple[list[str], list[list[str]]] | None:
    lines = [line.rstrip() for line in text.splitlines() if line.strip()]
    if len(lines) < 2:
        return None
    if not lines[0].strip().startswith("|") or not lines[1].strip().startswith("|"):
        return None
    if set(lines[1].replace("|", "").replace(" ", "")) - {"-", ":"}:
        return None
    header = [cell.strip() for cell in lines[0].strip().strip("|").split("|")]
    rows = [
        [cell.strip() for cell in line.strip().strip("|").split("|")]
        for line in lines[2:]
        if line.strip().startswith("|")
    ]
    return header, rows


def build_key_value_cards(rows: list[list[str]], label: str) -> str:
    cards: list[str] = []
    for row in rows:
        if len(row) < 2:
            continue
        title = row[0]
        detail = row[1]
        extra = " / ".join(cell for cell in row[2:] if cell)
        cards.append(
            f"""
            <article class="mini-card">
              <span class="eyebrow">{escape(label)}</span>
              <h3>{inline_markdown(title)}</h3>
              <p>{inline_markdown(detail)}</p>
              {'<p class="mini-meta">' + inline_markdown(extra) + '</p>' if extra else ''}
            </article>
            """
        )
    if not cards:
        return ""
    return f'<div class="mini-card-grid">{"".join(cards)}</div>'


def render_learning_path(path: Path) -> str:
    short_label, long_label = file_label(path.name)
    text = read_text(path)
    sections = split_markdown_sections(text)
    dashboard_blocks: list[str] = []
    timeline_rows: list[list[str]] = []

    for level, heading, body in sections:
        if level != 2 or not heading:
            continue
        if heading_has(heading, "学习目标", "知识点掌握标准"):
            continue
        summary = summarize_block(body)
        if heading_has(heading, "章节学习用时表"):
            parsed = parse_markdown_table(body)
            if parsed:
                _, timeline_rows = parsed
            continue
        if summary:
            dashboard_blocks.append(
                f"""
                <article class="dashboard-card">
                  <span class="eyebrow">学习路径</span>
                  <h3>{escape(heading)}</h3>
                  <p>{inline_markdown(summary)}</p>
                </article>
                """
            )

    outline = build_outline_links(
        sections,
        levels=(2,),
        title="学习路径",
        skip_keywords=("答案区",),
    )
    html = markdown_to_html(text)
    dashboard = f'<div class="dashboard-grid">{"".join(dashboard_blocks)}</div>' if dashboard_blocks else ""
    timeline = ""
    if timeline_rows:
        timeline = f"""
        <section class="teaching-strip">
          <div class="section-topline">
            <span class="eyebrow">推荐顺序</span>
            <h3>按阶段推进，不一次读完</h3>
          </div>
          {build_key_value_cards(timeline_rows, "阶段")}
        </section>
        """
    return f"""
    <section class="doc-card" id="{path.stem}">
      <div class="doc-card-head">
        <span class="eyebrow">{short_label}</span>
        <h2>{escape(long_label)}</h2>
        <span class="file-chip">{escape(path.name)}</span>
      </div>
      {dashboard}
      {timeline}
      {outline}
      <div class="doc-card-body markdown-body">
        {html}
      </div>
    </section>
    """


def render_collapsible_doc(path: Path, answer_keywords: tuple[str, ...]) -> str:
    short_label, long_label = file_label(path.name)
    text = read_text(path)
    sections = split_markdown_sections(text)
    prompt_sections: list[str] = []
    answer_sections: list[str] = []
    in_answers = False
    for level, title, body in sections:
        if title and heading_has(title, *answer_keywords):
            in_answers = True
        target = answer_sections if in_answers else prompt_sections
        heading = f"{'#' * max(level, 1)} {title}\n" if title else ""
        if body:
            target.append(heading + body)
        elif heading:
            target.append(heading)

    prompt_text = "\n\n".join(prompt_sections).strip()
    answer_text = "\n\n".join(answer_sections).strip()
    prompt_html = markdown_to_html(prompt_text)
    answer_html = markdown_to_html(answer_text) if answer_text else ""
    prompt_summary = summarize_block(prompt_text)
    summary_block = ""
    if prompt_summary:
        summary_block = f"""
        <div class="focus-callout">
          <span class="eyebrow">使用方式</span>
          <p>{inline_markdown(prompt_summary)}</p>
        </div>
        """
    answer_block = ""
    if answer_html:
        answer_block = f"""
        <div class="answer-tools">
          <button class="inline-tool" type="button" data-answer-action="open">展开答案</button>
          <button class="inline-tool" type="button" data-answer-action="close">收起答案</button>
        </div>
        <details class="answer-box">
          <summary>查看答案区</summary>
          <div class="markdown-body">{answer_html}</div>
        </details>
        """

    return f"""
    <section class="doc-card" id="{path.stem}">
      <div class="doc-card-head">
        <span class="eyebrow">{short_label}</span>
        <h2>{escape(long_label)}</h2>
        <span class="file-chip">{escape(path.name)}</span>
      </div>
      {summary_block}
      <div class="doc-card-body markdown-body">
        {prompt_html}
      </div>
      {answer_block}
    </section>
    """


def render_memory_cards(path: Path) -> str:
    text = read_text(path)
    sections = split_markdown_sections(text)
    intro_chunks: list[str] = []
    cards: list[dict[str, str]] = []
    oral_review: list[str] = []
    current_tier = "卡片"
    oral_mode = False

    for level, title, body in sections:
        if level <= 2 and title:
            if heading_has(title, "Core Cards"):
                current_tier = "Core"
                oral_mode = False
                continue
            if heading_has(title, "Secondary Cards"):
                current_tier = "Secondary"
                oral_mode = False
                continue
            if heading_has(title, "Trap Cards"):
                current_tier = "Trap"
                oral_mode = False
                continue
            if heading_has(title, "3 分钟口头复习", "3-Minute Oral Review"):
                oral_mode = True
                continue
            intro_chunks.append((f"{'#' * level} {title}\n{body}").strip())
            continue

        if oral_mode:
            oral_review.extend(extract_bullet_lines(body))
            continue

        if level == 3 and title:
            cards.append({"id": title.strip(), "tier": current_tier, "body": body})

    def field(patterns: tuple[str, ...], block: str) -> str:
        for line in block.splitlines():
            stripped = line.strip()
            if not stripped.startswith("- "):
                continue
            normalized = stripped[2:]
            for pattern in patterns:
                if normalized.lower().startswith(pattern.lower()):
                    return normalized.split(":", 1)[-1].strip()
        return ""

    intro_html = markdown_to_html("\n\n".join(intro_chunks))
    cards_html: list[str] = []
    for card in cards:
        prompt = field(("Prompt", "提问"), card["body"])
        answer = field(("Answer", "答案"), card["body"])
        card_type = field(("Type", "类型"), card["body"])
        why = field(("Why memorize", "为什么要记"), card["body"])
        tier_class = escape(card["tier"].lower())
        cards_html.append(
            f"""
            <article class="flash-card flash-card-{tier_class}">
              <div class="flash-card-face flash-card-front">
                <span class="tier-chip">{escape(card['tier'])}</span>
                <h3>{escape(card['id'])}</h3>
                <p>{inline_markdown(prompt or "未抽取到题面")}</p>
              </div>
              <div class="flash-card-face flash-card-back">
                <p><strong>答案</strong></p>
                <p>{inline_markdown(answer or "未抽取到答案")}</p>
                <p class="flash-meta">{inline_markdown(card_type or "")}</p>
                <p class="flash-meta">{inline_markdown(why or "")}</p>
              </div>
            </article>
            """
        )

    oral_block = ""
    if oral_review:
        oral_items = "".join(f"<li>{inline_markdown(item)}</li>" for item in oral_review)
        oral_block = f"""
        <section class="teaching-strip">
          <div class="section-topline">
            <span class="eyebrow">口头复习</span>
            <h3>3 分钟速过一遍</h3>
          </div>
          <ul class="oral-review-list">{oral_items}</ul>
        </section>
        """

    return f"""
    <section class="doc-card" id="{path.stem}">
      <div class="doc-card-head">
        <span class="eyebrow">卡片</span>
        <h2>记忆卡片</h2>
        <span class="file-chip">{escape(path.name)}</span>
      </div>
      <div class="doc-card-body markdown-body">
        {intro_html}
      </div>
      {oral_block}
      <div class="flash-card-grid">
        {''.join(cards_html)}
      </div>
    </section>
    """


def render_code_extracts(path: Path) -> str:
    text = read_text(path)
    sections = split_markdown_sections(text)
    intro_chunks: list[str] = []
    snippet_sections: list[tuple[str, str]] = []
    for level, heading, body in sections:
        if level == 3 and heading.startswith("Code"):
            snippet_sections.append((heading, body))
            continue
        if not snippet_sections:
            intro_chunks.append((f"{'#' * max(level, 1)} {heading}\n{body}").strip() if heading else body)

    intro_html = markdown_to_html("\n\n".join(chunk for chunk in intro_chunks if chunk.strip()))
    index_links: list[str] = []
    snippet_cards: list[str] = []
    for heading, body in snippet_sections:
        summary = summarize_block(body) or "代码摘录"
        code_match = re.search(r"```[^\n]*\n(.*?)```", body, re.S)
        code_id = f"{path.stem}-{slugify(heading)}-code"
        code_block = ""
        if code_match:
            code_block = f"""
            <div class="code-toolbar">
              <button class="inline-tool" type="button" data-copy-target="{code_id}">复制代码</button>
            </div>
            <pre><code id="{code_id}">{escape(code_match.group(1).rstrip())}</code></pre>
            """
        index_links.append(
            f'<a class="outline-link outline-level-3" href="#{slugify(heading)}">{escape(heading)}<small>{inline_markdown(summary)}</small></a>'
        )
        body_without_code = re.sub(r"```[^\n]*\n.*?```", "", body, flags=re.S).strip()
        snippet_cards.append(
            f"""
            <article class="code-card" id="{slugify(heading)}">
              <div class="code-card-head">
                <span class="eyebrow">代码片段</span>
                <h3>{escape(heading)}</h3>
              </div>
              <div class="markdown-body">{markdown_to_html(body_without_code)}</div>
              {code_block}
            </article>
            """
        )
    outline = ""
    if index_links:
        outline = f"""
        <nav class="outline-card">
          <span class="eyebrow">代码索引</span>
          <h3>按片段定位</h3>
          <div class="outline-links code-index-links">
            {''.join(index_links)}
          </div>
        </nav>
        """
    return f"""
    <section class="doc-card" id="{path.stem}">
      <div class="doc-card-head">
        <span class="eyebrow">代码</span>
        <h2>代码摘录</h2>
        <span class="file-chip">{escape(path.name)}</span>
      </div>
      {outline}
      <div class="doc-card-body markdown-body">
        {intro_html}
      </div>
      <div class="code-card-grid">
        {''.join(snippet_cards)}
      </div>
    </section>
    """


def render_review_plan(path: Path) -> str:
    short_label, long_label = file_label(path.name)
    text = read_text(path)
    sections = split_markdown_sections(text)
    steps: list[str] = []
    fallback_html = markdown_to_html(text)

    for level, heading, body in sections:
        if level != 2 or not heading:
            continue
        bullets = extract_bullet_lines(body)
        if not bullets:
            continue
        step_items = "".join(f"<li>{inline_markdown(item)}</li>" for item in bullets)
        steps.append(
            f"""
            <article class="review-step">
              <span class="eyebrow">复习节点</span>
              <h3>{escape(heading)}</h3>
              <ul>{step_items}</ul>
            </article>
            """
        )

    timeline = f'<div class="review-timeline">{"".join(steps)}</div>' if steps else ""
    return f"""
    <section class="doc-card" id="{path.stem}">
      <div class="doc-card-head">
        <span class="eyebrow">{short_label}</span>
        <h2>{escape(long_label)}</h2>
        <span class="file-chip">{escape(path.name)}</span>
      </div>
      {timeline}
      <div class="doc-card-body markdown-body">
        {fallback_html}
      </div>
    </section>
    """


def render_glossary(path: Path) -> str:
    short_label, long_label = file_label(path.name)
    text = read_text(path)
    sections = split_markdown_sections(text)
    curated_blocks: list[str] = []

    for level, heading, body in sections:
        if level != 2 or not heading:
            continue
        parsed = parse_markdown_table(body)
        if not parsed:
            continue
        _, rows = parsed
        label = "术语卡"
        if heading_has(heading, "公式"):
            label = "公式卡"
        elif heading_has(heading, "易混"):
            label = "辨析卡"
        block = build_key_value_cards(rows, label)
        if not block:
            continue
        curated_blocks.append(
            f"""
            <section class="teaching-strip">
              <div class="section-topline">
                <span class="eyebrow">术语模块</span>
                <h3>{escape(heading)}</h3>
              </div>
              {block}
            </section>
            """
        )

    html = markdown_to_html(text)
    return f"""
    <section class="doc-card" id="{path.stem}">
      <div class="doc-card-head">
        <span class="eyebrow">{short_label}</span>
        <h2>{escape(long_label)}</h2>
        <span class="file-chip">{escape(path.name)}</span>
      </div>
      {''.join(curated_blocks)}
      <div class="doc-card-body markdown-body">
        {html}
      </div>
    </section>
    """


def render_lesson_notes(path: Path) -> str:
    text = read_text(path)
    sections = split_markdown_sections(text)
    spotlight_blocks: list[str] = []
    keywords = (
        ("起步例子", "starter example"),
        ("本章地图", "chapter map"),
        ("概念主线", "conceptual spine"),
        ("10 分钟", "10-minute review"),
        ("最低完成标准", "must pass"),
    )
    for level, title, body in sections:
        if level != 2 or not title:
            continue
        if any(heading_has(title, *group) for group in keywords):
            summary = summarize_block(body)
            if summary:
                spotlight_blocks.append(
                    f"""
                    <article class="spotlight-card">
                      <span class="eyebrow">重点模块</span>
                      <h3>{escape(title)}</h3>
                      <p>{inline_markdown(summary)}</p>
                    </article>
                    """
                )

    short_label, long_label = file_label(path.name)
    html = markdown_to_html(text)
    spotlight = f'<div class="spotlight-grid">{"".join(spotlight_blocks)}</div>' if spotlight_blocks else ""
    outline = build_outline_links(
        sections,
        levels=(2, 3),
        title="讲义目录",
        skip_keywords=("答案区", "闭卷检查答案区"),
    )

    return f"""
    <section class="doc-card" id="{path.stem}">
      <div class="doc-card-head">
        <span class="eyebrow">{short_label}</span>
        <h2>{escape(long_label)}</h2>
        <span class="file-chip">{escape(path.name)}</span>
      </div>
      {spotlight}
      {outline}
      <div class="doc-card-body markdown-body">
        {html}
      </div>
    </section>
    """


def render_file_section(path: Path) -> str:
    if path.name == "00-learning-path.md":
        return render_learning_path(path)
    if path.name == "01-lesson-notes.md":
        return render_lesson_notes(path)
    if path.name == "detailed-notes.md":
        return render_lesson_notes(path)
    if path.name == "02-active-recall.md":
        return render_collapsible_doc(path, ("答案区", "Answer Key"))
    if path.name == "03-exercises.md":
        return render_collapsible_doc(path, ("完整答案", "Complete Answers and Scoring"))
    if path.name == "practice.md":
        return render_collapsible_doc(path, ("完整答案", "Complete Answers and Scoring"))
    if path.name == "04-glossary.md":
        return render_glossary(path)
    if path.name == "05-review-plan.md":
        return render_review_plan(path)
    if path.name == "review-notes.md":
        return render_review_plan(path)
    if path.name == "06-memory-cards.md":
        return render_memory_cards(path)
    if path.name == "07-code-extracts.md":
        return render_code_extracts(path)

    short_label, long_label = file_label(path.name)
    html = markdown_to_html(read_text(path))
    return f"""
    <section class="doc-card" id="{path.stem}">
      <div class="doc-card-head">
        <span class="eyebrow">{short_label}</span>
        <h2>{escape(long_label)}</h2>
        <span class="file-chip">{escape(path.name)}</span>
      </div>
      <div class="doc-card-body markdown-body">
        {html}
      </div>
    </section>
    """


def file_exists_map(chapter: Chapter) -> dict[str, Path]:
    return {path.name: path for path in chapter.files}


def build_stage_panels(chapter: Chapter) -> str:
    available = file_exists_map(chapter)
    panels: list[str] = []
    visible_index = 0
    for stage_id, _, filenames in tab_groups_for(chapter.output_format):
        content = [render_file_section(available[name]) for name in filenames if name in available]
        if not content:
            continue
        active_attr = ' data-active="true"' if visible_index == 0 else ""
        mode_attr = " ".join(STAGE_MODES.get(stage_id, ("study", "review")))
        visible_index += 1
        panels.append(
            f"""
            <section class="stage-panel"{active_attr} id="panel-{stage_id}" data-stage="{stage_id}" data-mode="{mode_attr}">
              {''.join(content)}
            </section>
            """
        )
    return "\n".join(panels)


def build_stage_buttons(chapter: Chapter) -> str:
    available = file_exists_map(chapter)
    buttons: list[str] = []
    visible_index = 0
    for stage_id, stage_label, filenames in tab_groups_for(chapter.output_format):
        present = [name for name in filenames if name in available]
        if not present:
            continue
        is_active = visible_index == 0
        mode_attr = " ".join(STAGE_MODES.get(stage_id, ("study", "review")))
        visible_index += 1
        filenames_label = " / ".join(file_label(name)[1] for name in present)
        buttons.append(
            f"""
            <button class="stage-tab" type="button" data-stage-target="{stage_id}" data-mode="{mode_attr}" aria-pressed="{str(is_active).lower()}">
              <span>{escape(stage_label)}</span>
              <small>{escape(filenames_label)}</small>
            </button>
            """
        )
    return "\n".join(buttons)


def build_quick_nav(chapter: Chapter) -> str:
    items = []
    if chapter.knowledge_map_path:
        items.append('<a href="#knowledge-map"><span>地图</span><strong>知识图谱</strong></a>')
    for path in chapter.files:
        short_label, long_label = file_label(path.name)
        items.append(
            f'<a href="#{escape(path.stem)}"><span>{escape(short_label)}</span><strong>{escape(long_label)}</strong></a>'
        )
    if chapter.knowledge_pages_path:
        items.insert(
            1 if chapter.knowledge_map_path else 0,
            '<a href="#knowledge-pages"><span>Pages</span><strong>Knowledge Pages</strong></a>',
        )
    return "\n".join(items)


def build_stage_summary(chapter: Chapter) -> str:
    available = file_exists_map(chapter)
    cards: list[str] = []
    descriptions = {
        "primer": "先抓章节主线、起步例子和地图，不先陷入细节。",
        "recall": "先闭卷说，再展开答案，用来查漏。",
        "practice": "把知识变成题感，优先做核心题。",
        "review": "用时间轴和卡片回捞长期记忆。",
        "glossary": "压缩术语、公式和易混点，适合扫读。",
        "code": "把结构、算法和实现风险连到代码片段。",
        "source": "回到来源页与抽取可靠性，控制误读。",
    }
    for stage_id, stage_label, filenames in tab_groups_for(chapter.output_format):
        present = [name for name in filenames if name in available]
        if not present:
            continue
        cards.append(
            f"""
            <article class="mini-card">
              <span class="eyebrow">学习阶段</span>
              <h3>{escape(stage_label)}</h3>
              <p>{escape(descriptions.get(stage_id, ""))}</p>
              <p class="mini-meta">{escape(' / '.join(file_label(name)[1] for name in present))}</p>
            </article>
            """
        )
    if not cards:
        return ""
    return f'<div class="mini-card-grid">{"".join(cards)}</div>'


def build_mode_switcher() -> str:
    return """
    <section class="mode-switcher" data-mode-root>
      <div class="mode-copy">
        <span class="eyebrow">阅读模式</span>
        <h2>同一份内容，两种阅读密度</h2>
        <p>学习模式优先带你走主线和理解链路，复习模式优先压缩到回忆、题感、术语和复盘。</p>
      </div>
      <div class="mode-actions">
        <button class="mode-pill-button" type="button" data-mode-target="study" aria-pressed="true">
          <span>学习模式</span>
          <small>先讲义，再自测，再练习</small>
        </button>
        <button class="mode-pill-button" type="button" data-mode-target="review" aria-pressed="false">
          <span>复习模式</span>
          <small>先回忆，再术语，再复盘</small>
        </button>
      </div>
    </section>
    """


def render_chapter_page(course_title: str, chapter: Chapter, out_dir: Path) -> None:
    body = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(chapter.title)} - {escape(course_title)}</title>
  <link rel="stylesheet" href="assets/site.css">
</head>
<body>
  <div class="site-shell">
    <aside class="left-rail">
      <a class="course-back" href="index.html">返回课程首页</a>
      <p class="rail-label">阅读导航</p>
      <h1>{escape(chapter.title)}</h1>
      <div class="meta-stack">
        <span>{escape(chapter.chapter_range)}</span>
        <span>{escape(chapter.output_mode)}</span>
        <span>{chapter.note_lines} 行讲义</span>
      </div>
      <nav class="jump-links">
        {build_quick_nav(chapter)}
      </nav>
    </aside>
    <main class="chapter-main">
      <header class="hero">
        <div class="hero-copy">
          <p class="eyebrow">Lesson View</p>
          <h1>{escape(chapter.title)}</h1>
          <p class="hero-summary">保留原始 Markdown 作为内容源，按学习节奏重组为网页阅读层。先学、再测、再练，避免一上来就被长文档压扁。</p>
        </div>
        <div class="hero-stats">
          <div><span>章节范围</span><strong>{escape(chapter.chapter_range)}</strong></div>
          <div><span>讲义体量</span><strong>{chapter.note_lines} 行 / {chapter.note_chars} 字符</strong></div>
          <div><span>生成时间</span><strong>{escape(chapter.created_at or "未知")}</strong></div>
        </div>
      </header>

      {render_knowledge_map(chapter)}
      {render_knowledge_pages(chapter)}

      <section class="reading-notes">
        <div class="reading-card">
          <span class="eyebrow">阅读策略</span>
          <h2>先抓主线，再下钻细节</h2>
          <p>网页层不是替代原有 study pack，而是把同一批内容按学习任务重排。优先看路径和讲义，再切换到自测、练习、代码与来源核对。</p>
        </div>
        <div class="reading-card">
          <span class="eyebrow">适合场景</span>
          <h2>大章、密章、考前回看</h2>
          <p>像树、图这类结构重、对比多、公式多的章节，更适合拆成阶段阅读，而不是一次滚完整个 Markdown。</p>
        </div>
      </section>

      {build_mode_switcher()}

      <section class="teaching-strip">
        <div class="section-topline">
          <span class="eyebrow">阶段切换</span>
          <h2>按任务进入，不按文件进入</h2>
        </div>
        <div class="mode-hint" data-mode-hint>
          <span class="mode-hint-badge">当前模式</span>
          <strong data-mode-label>学习模式</strong>
          <p data-mode-description>推荐从学习路径和讲义开始，建立章节地图后再切换到自测与练习。</p>
        </div>
        {build_stage_summary(chapter)}
      </section>

      <section class="stage-strip">
        {build_stage_buttons(chapter)}
      </section>

      {build_stage_panels(chapter)}
    </main>
  </div>
  <script src="assets/site.js"></script>
</body>
</html>
"""
    write_text(out_dir / f"{chapter.chapter_id}.html", body)


def render_index_page(course_title: str, chapters: Iterable[Chapter], out_dir: Path) -> None:
    cards = []
    for chapter in chapters:
        cards.append(
            f"""
            <article class="chapter-card">
              <div class="chapter-card-top">
                <span class="eyebrow">{escape(chapter.chapter_id)}</span>
                <span class="mode-pill">{escape(chapter.output_mode)}</span>
              </div>
              <h2><a href="{escape(chapter.chapter_id)}.html">{escape(chapter.title)}</a></h2>
              <p>{escape(chapter.chapter_range)}</p>
              <div class="chapter-metrics">
                <span>{chapter.note_lines} 行讲义</span>
                <span>{len(chapter.files)} 个学习文件</span>
              </div>
              <a class="card-link" href="{escape(chapter.chapter_id)}.html">进入章节</a>
            </article>
            """
        )

    body = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(course_title)} - Lesson Site</title>
  <link rel="stylesheet" href="assets/site.css">
</head>
<body class="index-body">
  <main class="index-shell">
    <section class="index-hero">
      <p class="eyebrow">Lesson Site Prototype</p>
      <h1>{escape(course_title)}</h1>
      <p>现有 Markdown 学习包不变，只新增一个轻量网页阅读层。目标不是改内容，而是提高扫读速度、切换效率和复习命中率。</p>
    </section>
    <section class="index-grid">
      {''.join(cards)}
    </section>
  </main>
</body>
</html>
"""
    write_text(out_dir / "index.html", body)


def render_assets(out_dir: Path) -> None:
    css = """* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  color: #1f2733;
  background:
    radial-gradient(circle at top left, rgba(219, 189, 135, 0.22), transparent 28%),
    linear-gradient(180deg, #f8f1e7 0%, #f5f6f2 48%, #eef1ef 100%);
  font-family: "Source Han Serif SC", "Noto Serif SC", "Songti SC", Georgia, serif;
}
a { color: inherit; text-decoration: none; }
code, pre {
  font-family: "IBM Plex Mono", "Cascadia Code", "Consolas", monospace;
}
.eyebrow {
  display: inline-block;
  font: 600 0.76rem/1.2 "IBM Plex Sans", "Segoe UI Variable Text", sans-serif;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #8a5a2b;
}
.site-shell {
  display: grid;
  grid-template-columns: 18rem minmax(0, 1fr);
  min-height: 100vh;
}
.left-rail {
  position: sticky;
  top: 0;
  align-self: start;
  height: 100vh;
  padding: 2rem 1.4rem 2rem 1.6rem;
  border-right: 1px solid rgba(79, 71, 55, 0.12);
  background: rgba(252, 249, 243, 0.82);
  backdrop-filter: blur(14px);
}
.course-back {
  display: inline-block;
  margin-bottom: 1rem;
  font: 600 0.94rem/1.2 "IBM Plex Sans", "Segoe UI Variable Text", sans-serif;
  color: #6f4b28;
}
.rail-label {
  margin: 0 0 0.3rem;
  font: 600 0.8rem/1.2 "IBM Plex Sans", "Segoe UI Variable Text", sans-serif;
  color: #8e7150;
}
.left-rail h1 {
  margin: 0;
  font-size: 1.7rem;
  line-height: 1.18;
}
.meta-stack {
  display: grid;
  gap: 0.45rem;
  margin: 1rem 0 1.4rem;
  color: #576171;
  font: 500 0.9rem/1.45 "IBM Plex Sans", "Segoe UI Variable Text", sans-serif;
}
.jump-links {
  display: grid;
  gap: 0.55rem;
}
.jump-links a {
  display: grid;
  gap: 0.12rem;
  padding: 0.75rem 0.85rem;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(95, 82, 63, 0.08);
  transition: transform 160ms ease, border-color 160ms ease, background 160ms ease;
}
.jump-links a:hover {
  transform: translateX(4px);
  border-color: rgba(138, 90, 43, 0.24);
  background: rgba(255, 255, 255, 0.96);
}
.jump-links span {
  font: 600 0.76rem/1.2 "IBM Plex Sans", "Segoe UI Variable Text", sans-serif;
  color: #8a5a2b;
}
.jump-links strong {
  font-size: 0.95rem;
  line-height: 1.32;
}
.chapter-main {
  padding: 2.2rem clamp(1rem, 2vw, 2rem) 3rem;
}
.hero {
  display: grid;
  gap: 1.2rem;
  grid-template-columns: minmax(0, 1.6fr) minmax(18rem, 0.9fr);
  padding: 1.5rem;
  border-radius: 28px;
  background:
    linear-gradient(135deg, rgba(255,255,255,0.92), rgba(250,244,235,0.86)),
    linear-gradient(135deg, #fff, #faf5ee);
  border: 1px solid rgba(118, 92, 63, 0.12);
  box-shadow: 0 24px 70px rgba(89, 71, 52, 0.08);
}
.hero h1 {
  margin: 0.25rem 0 0.55rem;
  font-size: clamp(2rem, 3.6vw, 3.25rem);
  line-height: 1.05;
}
.hero-summary {
  max-width: 48rem;
  margin: 0;
  color: #46505c;
  font-size: 1.03rem;
  line-height: 1.75;
}
.hero-stats {
  display: grid;
  gap: 0.85rem;
}
.hero-stats div,
.reading-card,
.chapter-card {
  padding: 1rem 1.1rem;
  border-radius: 20px;
  background: rgba(255,255,255,0.75);
  border: 1px solid rgba(95, 82, 63, 0.09);
}
.hero-stats span,
.chapter-metrics,
.file-chip {
  display: block;
  color: #847566;
  font: 500 0.82rem/1.3 "IBM Plex Sans", "Segoe UI Variable Text", sans-serif;
}
.hero-stats strong {
  display: block;
  margin-top: 0.3rem;
  font: 600 1rem/1.45 "IBM Plex Sans", "Segoe UI Variable Text", sans-serif;
}
.reading-notes {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
  margin: 1.15rem 0 1.4rem;
}
.reading-card h2 {
  margin: 0.25rem 0 0.4rem;
  font-size: 1.2rem;
}
.reading-card p {
  margin: 0;
  color: #4e5967;
  line-height: 1.68;
}
.mode-switcher {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(18rem, 1fr);
  gap: 1rem;
  margin: 1rem 0 1.35rem;
  padding: 1rem 1.1rem;
  border-radius: 24px;
  background: linear-gradient(135deg, rgba(255,255,255,0.92), rgba(247,238,223,0.88));
  border: 1px solid rgba(120, 94, 61, 0.12);
}
.mode-copy h2 {
  margin: 0.22rem 0 0.45rem;
  font-size: 1.35rem;
}
.mode-copy p {
  margin: 0;
  color: #4e5967;
  line-height: 1.7;
}
.mode-actions {
  display: grid;
  gap: 0.8rem;
}
.mode-pill-button {
  display: grid;
  gap: 0.18rem;
  padding: 0.95rem 1rem;
  border-radius: 18px;
  border: 1px solid rgba(122, 95, 57, 0.12);
  background: rgba(255,255,255,0.75);
  color: #283240;
  text-align: left;
  cursor: pointer;
  transition: transform 160ms ease, border-color 160ms ease, background 160ms ease;
}
.mode-pill-button:hover {
  transform: translateY(-2px);
}
.mode-pill-button[aria-pressed="true"] {
  background: linear-gradient(135deg, #fff8ef, #f3e0c5);
  border-color: rgba(138, 90, 43, 0.34);
}
.mode-pill-button span {
  font: 700 1rem/1.2 "IBM Plex Sans", "Segoe UI Variable Text", sans-serif;
}
.mode-pill-button small {
  color: #6a7688;
  font: 500 0.82rem/1.4 "IBM Plex Sans", "Segoe UI Variable Text", sans-serif;
}
.teaching-strip {
  margin: 1rem 0 1.4rem;
  padding: 1rem 1rem 1.1rem;
  border-radius: 22px;
  background: rgba(255,255,255,0.68);
  border: 1px solid rgba(95, 82, 63, 0.08);
}
.mode-hint {
  display: grid;
  gap: 0.18rem;
  margin: 0 0 1rem;
  padding: 0.9rem 1rem;
  border-radius: 18px;
  background: rgba(252, 245, 233, 0.92);
  border: 1px solid rgba(138, 90, 43, 0.12);
}
.mode-hint-badge {
  width: fit-content;
  padding: 0.18rem 0.55rem;
  border-radius: 999px;
  background: rgba(138, 90, 43, 0.12);
  color: #7d542c;
  font: 700 0.74rem/1.2 "IBM Plex Sans", "Segoe UI Variable Text", sans-serif;
}
.mode-hint strong {
  font: 700 1rem/1.3 "IBM Plex Sans", "Segoe UI Variable Text", sans-serif;
}
.mode-hint p {
  margin: 0;
  color: #566170;
  line-height: 1.62;
}
.section-topline h2,
.section-topline h3 {
  margin: 0.25rem 0 0.6rem;
}
.knowledge-map-board {
  margin: 1rem 0 1.35rem;
  padding: 1.1rem;
  border-radius: 24px;
  background: linear-gradient(135deg, rgba(255,255,255,0.94), rgba(247,239,226,0.92));
  border: 1px solid rgba(120, 94, 61, 0.12);
}
.knowledge-pages-board {
  margin: 1rem 0 1.35rem;
  padding: 1.1rem;
  border-radius: 24px;
  background: linear-gradient(135deg, rgba(255,255,255,0.96), rgba(238,244,239,0.92));
  border: 1px solid rgba(83, 110, 88, 0.12);
}
.knowledge-pages-shell {
  display: grid;
  grid-template-columns: minmax(17rem, 0.85fr) minmax(0, 1.8fr);
  gap: 1rem;
  align-items: start;
}
.kp-nav,
.kp-page,
.kp-block {
  border-radius: 20px;
  background: rgba(255,255,255,0.82);
  border: 1px solid rgba(95, 82, 63, 0.09);
}
.kp-nav {
  padding: 1rem;
}
.kp-nav-head p {
  margin: 0.3rem 0 0;
  color: #586475;
  line-height: 1.6;
}
.kp-nav-list {
  display: grid;
  gap: 0.65rem;
  margin-top: 0.9rem;
}
.kp-nav-card {
  display: grid;
  gap: 0.2rem;
  padding: 0.85rem 0.9rem;
  text-align: left;
  border-radius: 16px;
  border: 1px solid rgba(95, 82, 63, 0.08);
  background: rgba(255,255,255,0.8);
  cursor: pointer;
  transition: transform 140ms ease, border-color 140ms ease, background 140ms ease;
}
.kp-nav-card:hover {
  transform: translateY(-2px);
}
.kp-nav-card[aria-pressed="true"] {
  background: linear-gradient(135deg, #fff9f1, #eaf4ee);
  border-color: rgba(83, 110, 88, 0.24);
}
.kp-nav-card span {
  display: inline-flex;
  width: fit-content;
  padding: 0.2rem 0.48rem;
  border-radius: 999px;
  background: rgba(83, 110, 88, 0.1);
  color: #44624c;
  font: 700 0.74rem/1.2 "IBM Plex Sans", "Segoe UI Variable Text", sans-serif;
}
.kp-nav-card strong {
  font: 700 0.98rem/1.35 "IBM Plex Sans", "Segoe UI Variable Text", sans-serif;
}
.kp-nav-card small {
  color: #667283;
  line-height: 1.45;
}
.kp-stage {
  display: grid;
  gap: 0.85rem;
}
.kp-toolbar {
  display: flex;
  gap: 0.55rem;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
}
.kp-contract-grid {
  margin-bottom: 0.95rem;
}
.kp-progress {
  white-space: nowrap;
}
.kp-page[data-mode="review"] .kp-block[data-block-type="minimum_example"],
.kp-page[data-mode="review"] .kp-block[data-block-type="formal_statement"],
.kp-page[data-mode="review"] .kp-block[data-block-type="implementation_bridge"],
.kp-page[data-mode="review"] .kp-block[data-block-type="trace"],
.kp-page[data-mode="review"] .kp-block[data-block-type="why_it_holds"] {
  display: none;
}
.kp-page {
  display: none;
  padding: 1.1rem;
  animation: rise 220ms ease;
}
.kp-page[data-active="true"] {
  display: block;
}
.kp-page-head {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 0.7rem;
  align-items: end;
}
.kp-page-head h2 {
  margin: 0.24rem 0 0;
  font-size: 1.5rem;
  line-height: 1.15;
}
.kp-page-goal {
  display: grid;
  gap: 0.7rem;
  margin: 1rem 0;
}
.kp-ref-row {
  padding: 0.85rem 0.95rem;
  border-radius: 16px;
  background: rgba(248, 250, 247, 0.94);
  border: 1px solid rgba(83, 110, 88, 0.1);
}
.kp-ref-row p {
  margin: 0.28rem 0 0;
  color: #4e5967;
  line-height: 1.62;
}
.kp-block-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 0.85rem;
}
.kp-block {
  padding: 0.95rem;
}
.kp-block-head {
  display: grid;
  gap: 0.24rem;
  margin-bottom: 0.7rem;
}
.kp-block-head h3 {
  margin: 0;
  font-size: 1.02rem;
}
.kp-block-badge {
  width: fit-content;
  padding: 0.2rem 0.55rem;
  border-radius: 999px;
  background: rgba(83, 110, 88, 0.1);
  color: #44624c;
  font: 700 0.74rem/1.2 "IBM Plex Sans", "Segoe UI Variable Text", sans-serif;
}
.knowledge-map-problem {
  margin: 0 0 1rem;
  color: #4b5564;
  line-height: 1.68;
}
.knowledge-map-shell {
  display: grid;
  grid-template-columns: minmax(18rem, 0.8fr) minmax(0, 1.6fr);
  gap: 1rem;
  align-items: start;
}
.path-stack {
  display: grid;
  gap: 0.85rem;
}
.path-panel {
  padding: 1rem;
  border-radius: 18px;
  background: rgba(255,255,255,0.72);
  border: 1px solid rgba(95, 82, 63, 0.09);
}
.path-pill-row {
  display: grid;
  gap: 0.55rem;
  margin-top: 0.55rem;
}
.path-pill {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 0.7rem;
  align-items: center;
  padding: 0.72rem 0.8rem;
  border-radius: 14px;
  background: rgba(255,255,255,0.82);
  border: 1px solid rgba(95, 82, 63, 0.08);
}
.path-pill span {
  display: inline-flex;
  min-width: 2rem;
  justify-content: center;
  padding: 0.18rem 0.4rem;
  border-radius: 999px;
  background: rgba(138, 90, 43, 0.12);
  color: #7d542c;
  font: 700 0.74rem/1.2 "IBM Plex Sans", "Segoe UI Variable Text", sans-serif;
}
.path-pill strong {
  line-height: 1.4;
}
.knowledge-node-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 0.85rem;
}
.knowledge-node-card {
  padding: 1rem;
  border-radius: 18px;
  background: rgba(255,255,255,0.76);
  border: 1px solid rgba(95, 82, 63, 0.09);
}
.knowledge-node-card h3 {
  margin: 0.25rem 0 0.35rem;
  font-size: 1.02rem;
}
.knowledge-node-card p {
  margin: 0.4rem 0 0;
  color: #4f5967;
  line-height: 1.62;
}
.meta-badge-row,
.knowledge-link-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 0.8rem;
}
.meta-badge {
  padding: 0.22rem 0.55rem;
  border-radius: 999px;
  background: rgba(138, 90, 43, 0.11);
  color: #7d542c;
  font: 700 0.75rem/1.2 "IBM Plex Sans", "Segoe UI Variable Text", sans-serif;
}
.knowledge-link-row .outline-link {
  padding: 0.45rem 0.68rem;
  font-size: 0.88rem;
}
.mini-card-grid,
.dashboard-grid,
.spotlight-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
  gap: 0.85rem;
}
.mini-card,
.dashboard-card,
.outline-card,
.code-card {
  padding: 1rem;
  border-radius: 18px;
  background: rgba(255,255,255,0.72);
  border: 1px solid rgba(95, 82, 63, 0.09);
}
.mini-card h3,
.dashboard-card h3,
.outline-card h3,
.code-card h3,
.review-step h3 {
  margin: 0.25rem 0 0.35rem;
  font-size: 1.02rem;
}
.mini-card p,
.dashboard-card p,
.spotlight-card p {
  margin: 0;
  color: #4f5967;
  line-height: 1.62;
}
.mini-meta,
.flash-meta {
  color: #687484;
  font-size: 0.9rem;
}
.outline-card {
  margin: 0 0 1rem;
  background: linear-gradient(180deg, #fcf8f2, #f6efe6);
}
.outline-links {
  display: grid;
  gap: 0.45rem;
}
.outline-link {
  display: block;
  padding: 0.65rem 0.8rem;
  border-radius: 12px;
  background: rgba(255,255,255,0.76);
  color: #2c3440;
  border: 1px solid rgba(95, 82, 63, 0.08);
  transition: transform 140ms ease, border-color 140ms ease;
}
.outline-link:hover {
  transform: translateX(3px);
  border-color: rgba(138, 90, 43, 0.24);
}
.outline-level-3 {
  margin-left: 0.75rem;
}
.outline-link small {
  display: block;
  margin-top: 0.18rem;
  color: #687484;
  line-height: 1.4;
}
.stage-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 0.85rem;
  margin: 1.35rem 0 0;
}
.stage-tab {
  display: grid;
  gap: 0.18rem;
  padding: 0.95rem 1rem;
  min-width: 9rem;
  border: 1px solid rgba(122, 95, 57, 0.11);
  border-radius: 16px;
  background: rgba(255,255,255,0.68);
  color: #2c3440;
  text-align: left;
  cursor: pointer;
  transition: transform 160ms ease, background 160ms ease, border-color 160ms ease;
}
.stage-tab:hover { transform: translateY(-2px); }
.stage-tab[aria-pressed="true"] {
  background: linear-gradient(135deg, #fff9f1, #f6e6cf);
  border-color: rgba(138, 90, 43, 0.35);
}
.stage-tab span {
  font: 700 1rem/1.2 "IBM Plex Sans", "Segoe UI Variable Text", sans-serif;
}
.stage-tab small {
  color: #6a7688;
  font: 500 0.8rem/1.35 "IBM Plex Sans", "Segoe UI Variable Text", sans-serif;
}
.stage-panel { display: none; animation: rise 240ms ease; }
.stage-panel[data-active="true"] { display: block; }
.doc-card {
  margin-top: 1rem;
  padding: 1.25rem;
  border-radius: 24px;
  background: rgba(255,255,255,0.86);
  border: 1px solid rgba(95, 82, 63, 0.1);
  box-shadow: 0 16px 50px rgba(83, 67, 50, 0.06);
}
.doc-card-head {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 0.4rem 0.8rem;
  align-items: end;
  margin-bottom: 1rem;
}
.doc-card-head h2 {
  margin: 0;
  font-size: 1.45rem;
}
.file-chip {
  padding: 0.35rem 0.7rem;
  border-radius: 999px;
  background: #f3ede3;
}
.spotlight-card {
  padding: 1rem;
  border-radius: 18px;
  background: linear-gradient(135deg, #fbf6ee, #f3e5cf);
  border: 1px solid rgba(138, 90, 43, 0.14);
}
.spotlight-card h3 {
  margin: 0.25rem 0 0.35rem;
  font-size: 1.05rem;
}
.focus-callout {
  margin-bottom: 1rem;
  padding: 0.95rem 1rem;
  border-radius: 18px;
  background: #fcf4e8;
  border: 1px solid rgba(138, 90, 43, 0.14);
}
.focus-callout p {
  margin: 0.35rem 0 0;
  line-height: 1.65;
  color: #4b5564;
}
.answer-box {
  margin-top: 1rem;
  padding: 0.2rem 1rem 1rem;
  border-radius: 18px;
  background: #f7f1e8;
  border: 1px solid rgba(102, 85, 58, 0.12);
}
.answer-tools,
.code-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 0.55rem;
  margin-top: 1rem;
}
.inline-tool {
  border: 1px solid rgba(138, 90, 43, 0.18);
  background: #fffaf2;
  color: #724a24;
  border-radius: 999px;
  padding: 0.5rem 0.8rem;
  cursor: pointer;
  font: 700 0.82rem/1.2 "IBM Plex Sans", "Segoe UI Variable Text", sans-serif;
}
.inline-tool:hover {
  background: #f7e9d2;
}
.answer-box summary {
  cursor: pointer;
  padding: 0.9rem 0 0.7rem;
  font: 700 0.96rem/1.2 "IBM Plex Sans", "Segoe UI Variable Text", sans-serif;
  color: #724a24;
}
.flash-card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 0.9rem;
  margin-top: 1rem;
}
.flash-card {
  display: grid;
  gap: 0.85rem;
  padding: 1rem;
  border-radius: 18px;
  border: 1px solid rgba(95, 82, 63, 0.1);
  background: #fffdfa;
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.65);
}
.flash-card-core { background: linear-gradient(180deg, #fffdfa, #fff5e8); }
.flash-card-secondary { background: linear-gradient(180deg, #fdfdfc, #f4f4ef); }
.flash-card-trap { background: linear-gradient(180deg, #fff9f6, #f9e6da); }
.flash-card-face h3 {
  margin: 0.35rem 0 0.45rem;
  font-size: 1.08rem;
}
.flash-card-face p {
  margin: 0.3rem 0;
  line-height: 1.62;
}
.tier-chip {
  display: inline-block;
  padding: 0.22rem 0.55rem;
  border-radius: 999px;
  background: rgba(138, 90, 43, 0.11);
  color: #7d542c;
  font: 700 0.75rem/1.2 "IBM Plex Sans", "Segoe UI Variable Text", sans-serif;
  text-transform: uppercase;
}
.oral-review-list {
  margin: 0;
  padding-left: 1.2rem;
  line-height: 1.7;
}
.review-timeline {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 0.9rem;
  margin-bottom: 1rem;
}
.review-step {
  padding: 1rem;
  border-radius: 18px;
  background: linear-gradient(180deg, #fffaf2, #f8efe2);
  border: 1px solid rgba(95, 82, 63, 0.09);
}
.review-step ul {
  margin: 0.5rem 0 0;
  padding-left: 1.2rem;
  line-height: 1.65;
}
.code-card-grid {
  display: grid;
  gap: 0.95rem;
  margin-top: 1rem;
}
.code-card-head {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: center;
}
.code-index-links .outline-link {
  display: grid;
  gap: 0.12rem;
}
.markdown-body {
  color: #1f2733;
  line-height: 1.8;
  font-size: 1rem;
}
.markdown-body h1,
.markdown-body h2,
.markdown-body h3,
.markdown-body h4 {
  margin: 1.3em 0 0.5em;
  line-height: 1.2;
}
.markdown-body h1 { font-size: 1.75rem; }
.markdown-body h2 { font-size: 1.45rem; }
.markdown-body h3 { font-size: 1.18rem; }
.markdown-body p,
.markdown-body ul,
.markdown-body ol,
.markdown-body blockquote,
.markdown-body .table-wrap,
.markdown-body pre {
  margin: 0.7rem 0 0.95rem;
}
.markdown-body ul,
.markdown-body ol { padding-left: 1.3rem; }
.markdown-body li { margin: 0.32rem 0; }
.markdown-body code {
  padding: 0.1rem 0.34rem;
  border-radius: 6px;
  background: #efe9de;
  font-size: 0.92em;
}
.markdown-body pre {
  overflow-x: auto;
  padding: 0.95rem 1rem;
  border-radius: 16px;
  background: #1e252f;
  color: #f4f1eb;
}
.markdown-body pre code {
  padding: 0;
  background: transparent;
  color: inherit;
}
.markdown-body blockquote {
  padding: 0.2rem 1rem;
  border-left: 4px solid #d0a46a;
  background: #fbf4ea;
  color: #435062;
}
.table-wrap { overflow-x: auto; }
.markdown-body table {
  width: 100%;
  border-collapse: collapse;
  min-width: 36rem;
  background: #fff;
}
.markdown-body th,
.markdown-body td {
  padding: 0.72rem 0.8rem;
  vertical-align: top;
  border: 1px solid rgba(88, 73, 53, 0.12);
}
.markdown-body th {
  background: #f7efe2;
  font: 700 0.9rem/1.3 "IBM Plex Sans", "Segoe UI Variable Text", sans-serif;
}
.index-body {
  min-height: 100vh;
  padding: 2rem clamp(1rem, 3vw, 2.5rem) 3rem;
}
.index-shell {
  max-width: 1200px;
  margin: 0 auto;
}
.index-hero {
  padding: 1.6rem;
  border-radius: 28px;
  background: rgba(255,255,255,0.84);
  border: 1px solid rgba(95, 82, 63, 0.09);
  box-shadow: 0 24px 70px rgba(89, 71, 52, 0.08);
}
.index-hero h1 {
  margin: 0.2rem 0 0.6rem;
  font-size: clamp(2.4rem, 5vw, 4.5rem);
  line-height: 0.98;
}
.index-hero p:last-child {
  max-width: 52rem;
  margin: 0;
  font-size: 1.05rem;
  line-height: 1.78;
  color: #475161;
}
.index-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
  gap: 1rem;
  margin-top: 1.2rem;
}
.chapter-card {
  display: grid;
  gap: 0.7rem;
}
.chapter-card-top {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: center;
}
.mode-pill {
  padding: 0.3rem 0.6rem;
  border-radius: 999px;
  background: #f1eadf;
  color: #77502c;
  font: 600 0.78rem/1.2 "IBM Plex Sans", "Segoe UI Variable Text", sans-serif;
}
.chapter-card h2 {
  margin: 0;
  font-size: 1.28rem;
  line-height: 1.2;
}
.chapter-card p {
  margin: 0;
  color: #54606f;
  line-height: 1.55;
}
.chapter-metrics {
  display: flex;
  flex-wrap: wrap;
  gap: 0.8rem;
}
.card-link {
  margin-top: auto;
  font: 700 0.92rem/1.2 "IBM Plex Sans", "Segoe UI Variable Text", sans-serif;
  color: #8a5a2b;
}
@keyframes rise {
  from { opacity: 0; transform: translateY(6px); }
  to { opacity: 1; transform: translateY(0); }
}
@media (max-width: 980px) {
  .site-shell { grid-template-columns: 1fr; }
  .left-rail {
    position: static;
    height: auto;
    border-right: 0;
    border-bottom: 1px solid rgba(79, 71, 55, 0.12);
  }
  .hero,
  .reading-notes,
  .mode-switcher,
  .knowledge-map-shell,
  .knowledge-pages-shell {
    grid-template-columns: 1fr;
  }
}
@media (max-width: 640px) {
  .chapter-main { padding-inline: 0.8rem; }
  .hero,
  .doc-card,
  .index-hero,
  .chapter-card { border-radius: 20px; }
  .stage-tab { min-width: calc(50% - 0.5rem); }
  .flash-card-grid,
  .spotlight-grid,
  .review-timeline,
  .mini-card-grid,
  .dashboard-grid,
  .kp-block-grid { grid-template-columns: 1fr; }
}
"""
    js = """const tabs = Array.from(document.querySelectorAll('[data-stage-target]'));
const panels = Array.from(document.querySelectorAll('[data-stage]'));
const modeButtons = Array.from(document.querySelectorAll('[data-mode-target]'));
const modeLabel = document.querySelector('[data-mode-label]');
const modeDescription = document.querySelector('[data-mode-description]');

const MODE_COPY = {
  study: {
    label: '学习模式',
    description: '推荐从学习路径和讲义开始，建立章节地图后再切换到自测与练习。'
  },
  review: {
    label: '复习模式',
    description: '优先回忆、题感、术语与错题回炉，适合考前压缩和二刷。'
  }
};

let currentMode = 'study';

function visibleTabsForMode(mode) {
  return tabs.filter((tab) => {
    const modes = (tab.dataset.mode || '').split(/\\s+/).filter(Boolean);
    return modes.length === 0 || modes.includes(mode);
  });
}

function activate(stageId) {
  tabs.forEach((tab) => {
    const active = tab.dataset.stageTarget === stageId;
    tab.setAttribute('aria-pressed', String(active));
  });
  panels.forEach((panel) => {
    const visible = panel.dataset.stage === stageId;
    if (visible) {
      panel.setAttribute('data-active', 'true');
    } else {
      panel.removeAttribute('data-active');
    }
  });
}

function applyMode(mode) {
  currentMode = mode;
  modeButtons.forEach((button) => {
    button.setAttribute('aria-pressed', String(button.dataset.modeTarget === mode));
  });
  if (modeLabel) {
    modeLabel.textContent = MODE_COPY[mode].label;
  }
  if (modeDescription) {
    modeDescription.textContent = MODE_COPY[mode].description;
  }

  tabs.forEach((tab) => {
    const modes = (tab.dataset.mode || '').split(/\\s+/).filter(Boolean);
    const visible = modes.length === 0 || modes.includes(mode);
    tab.hidden = !visible;
  });

  const visibleTabs = visibleTabsForMode(mode);
  const activeVisible = visibleTabs.find((tab) => tab.getAttribute('aria-pressed') === 'true');
  if (activeVisible) {
    activate(activeVisible.dataset.stageTarget);
    return;
  }

  const preferred = mode === 'review' ? ['review', 'recall', 'glossary', 'practice'] : ['primer', 'recall', 'practice', 'code'];
  for (const stageId of preferred) {
    const matched = visibleTabs.find((tab) => tab.dataset.stageTarget === stageId);
    if (matched) {
      activate(stageId);
      return;
    }
  }
  if (visibleTabs[0]) {
    activate(visibleTabs[0].dataset.stageTarget);
  }

  const kpRoot = document.querySelector('[data-kp-root]');
  if (kpRoot) {
    kpRoot.querySelectorAll('[data-kp-page]').forEach((page) => {
      page.dataset.mode = mode;
    });
  }
}

tabs.forEach((tab) => {
  tab.addEventListener('click', () => activate(tab.dataset.stageTarget));
});

modeButtons.forEach((button) => {
  button.addEventListener('click', () => applyMode(button.dataset.modeTarget));
});

if (modeButtons.length) {
  applyMode('study');
}

document.querySelectorAll('[data-answer-action]').forEach((button) => {
  button.addEventListener('click', () => {
    const root = button.closest('.doc-card');
    if (!root) return;
    root.querySelectorAll('details.answer-box').forEach((box) => {
      box.open = button.dataset.answerAction === 'open';
    });
  });
});

document.querySelectorAll('[data-copy-target]').forEach((button) => {
  button.addEventListener('click', async () => {
    const target = document.getElementById(button.dataset.copyTarget);
    if (!target) return;
    try {
      await navigator.clipboard.writeText(target.textContent || '');
      const original = button.textContent;
      button.textContent = '已复制';
      setTimeout(() => { button.textContent = original; }, 1200);
    } catch (_) {
      button.textContent = '复制失败';
      setTimeout(() => { button.textContent = '复制代码'; }, 1200);
    }
  });
});

const kpRoot = document.querySelector('[data-kp-root]');
if (kpRoot) {
  const kpButtons = Array.from(kpRoot.querySelectorAll('[data-kp-target]'));
  const kpPages = Array.from(kpRoot.querySelectorAll('[data-kp-page]'));
  const kpProgress = kpRoot.querySelector('[data-kp-progress]');
  let kpIndex = Math.max(0, kpPages.findIndex((page) => page.dataset.active === 'true'));

  function applyKnowledgePageMode(mode) {
    kpPages.forEach((page) => {
      page.dataset.mode = mode;
    });
  }

  function activateKnowledgePage(index) {
    if (!kpPages.length) return;
    kpIndex = Math.max(0, Math.min(index, kpPages.length - 1));
    kpPages.forEach((page, current) => {
      if (current === kpIndex) {
        page.setAttribute('data-active', 'true');
      } else {
        page.setAttribute('data-active', 'false');
      }
    });
    kpButtons.forEach((button, current) => {
      button.setAttribute('aria-pressed', String(current === kpIndex));
    });
    if (kpProgress) {
      kpProgress.textContent = `${kpIndex + 1} / ${kpPages.length}`;
    }
  }

  kpButtons.forEach((button, index) => {
    button.addEventListener('click', () => activateKnowledgePage(index));
  });

  kpRoot.querySelectorAll('[data-kp-move]').forEach((button) => {
    button.addEventListener('click', () => {
      if (button.dataset.kpMove === 'prev') {
        activateKnowledgePage(kpIndex - 1);
      } else {
        activateKnowledgePage(kpIndex + 1);
      }
    });
  });

  applyKnowledgePageMode(currentMode);
  activateKnowledgePage(kpIndex);
}
"""
    write_text(out_dir / "assets" / "site.css", css)
    write_text(out_dir / "assets" / "site.js", js)


def resolve_course_title(lessons_root: Path) -> str:
    project_root = lessons_root.parent.parent
    config_path = project_root / ".teach-pdf-content" / "config" / "class_project.json"
    if config_path.exists():
        try:
            config = load_json(config_path)
            title = str(config.get("course_title") or "").strip()
            if title:
                return title
        except json.JSONDecodeError:
            pass
    return lessons_root.name


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render lesson-pack Markdown outputs into a lightweight static HTML site."
    )
    parser.add_argument(
        "--lessons-root",
        required=True,
        help="Path like <project>/lessons/<source-id> that contains chapter-index.md and chapters/.",
    )
    parser.add_argument(
        "--out",
        help="Output directory. Defaults to <project>/reviews/lesson-site/<source-id>.",
    )
    args = parser.parse_args()

    lessons_root = Path(args.lessons_root).resolve()
    if not lessons_root.exists():
        parser.error(f"lessons root not found: {lessons_root}")
    chapters = discover_chapters(lessons_root)
    if not chapters:
        parser.error(f"no chapter directories found under: {lessons_root / 'chapters'}")

    source_id = lessons_root.name
    project_root = lessons_root.parent.parent
    out_dir = Path(args.out).resolve() if args.out else project_root / "reviews" / "lesson-site" / source_id
    course_title = resolve_course_title(lessons_root)

    out_dir.mkdir(parents=True, exist_ok=True)
    render_assets(out_dir)
    render_index_page(course_title, chapters, out_dir)
    for chapter in chapters:
        render_chapter_page(course_title, chapter, out_dir)

    print(f"rendered {len(chapters)} chapters to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
