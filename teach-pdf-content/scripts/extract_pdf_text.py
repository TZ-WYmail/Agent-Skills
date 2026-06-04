#!/usr/bin/env python3
"""Extract PDF pages and produce source-map friendly Markdown/JSON."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def parse_pages(spec: str | None) -> list[int]:
    if not spec:
        return []
    pages: list[int] = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start_text, end_text = part.split("-", 1)
            start = int(start_text)
            end = int(end_text)
            if end < start:
                raise ValueError(f"invalid page range: {part}")
            pages.extend(range(start, end + 1))
        else:
            pages.append(int(part))
    if any(page < 1 for page in pages):
        raise ValueError("PDF pages are 1-based and must be positive")
    return sorted(dict.fromkeys(pages))


def command_version(command: list[str], encoding: str) -> str:
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding=encoding,
            errors="replace",
            timeout=10,
        )
    except Exception as exc:  # pragma: no cover - environment specific
        return f"unknown ({exc})"
    output = (result.stdout + result.stderr).strip()
    return output.splitlines()[0] if output else "unknown"


def detect_page_count(pdf: Path, encoding: str) -> int | None:
    reader_info = import_pdf_reader()
    if reader_info is not None:
        reader_class, _version = reader_info
        try:
            return len(reader_class(str(pdf)).pages)
        except Exception:
            pass
    if shutil.which("pdfinfo"):
        result = subprocess.run(
            ["pdfinfo", str(pdf)],
            capture_output=True,
            text=True,
            encoding=encoding,
            errors="replace",
            timeout=30,
        )
        for line in (result.stdout + result.stderr).splitlines():
            if line.lower().startswith("pages:"):
                match = re.search(r"\d+", line)
                if match:
                    return int(match.group(0))
    return None


def extract_with_pdftotext(pdf: Path, pages: list[int], extract_all: bool, encoding: str) -> tuple[list[dict[str, Any]], str] | None:
    if not shutil.which("pdftotext"):
        return None

    version = command_version(["pdftotext", "-v"], encoding)
    page_records: list[dict[str, Any]] = []
    if extract_all:
        command = ["pdftotext", "-layout", str(pdf), "-"]
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding=encoding,
            errors="replace",
            timeout=120,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "pdftotext failed")
        chunks = result.stdout.split("\f")
        for index, text in enumerate(chunks, start=1):
            if text.strip():
                page_records.append({"pdf_page": index, "text": text.strip()})
        return page_records, f"pdftotext; {version}"

    for page in pages:
        command = ["pdftotext", "-f", str(page), "-l", str(page), "-layout", str(pdf), "-"]
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding=encoding,
            errors="replace",
            timeout=60,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or f"pdftotext failed on page {page}")
        page_records.append({"pdf_page": page, "text": result.stdout.replace("\f", "").strip()})
    return page_records, f"pdftotext; {version}"


def import_pdf_reader() -> tuple[Any, str] | None:
    try:
        import pypdf  # type: ignore

        return pypdf.PdfReader, f"pypdf {getattr(pypdf, '__version__', 'unknown')}"
    except Exception:
        pass
    try:
        import PyPDF2  # type: ignore

        return PyPDF2.PdfReader, f"PyPDF2 {getattr(PyPDF2, '__version__', 'unknown')}"
    except Exception:
        return None


def extract_with_python_pdf(pdf: Path, pages: list[int], extract_all: bool, encoding: str) -> tuple[list[dict[str, Any]], str] | None:
    _ = encoding
    reader_info = import_pdf_reader()
    if reader_info is None:
        return None
    reader_class, version = reader_info
    reader = reader_class(str(pdf))
    selected = range(1, len(reader.pages) + 1) if extract_all else pages
    records = []
    for page_number in selected:
        if page_number > len(reader.pages):
            raise ValueError(f"requested [PDF p.{page_number}] but PDF has {len(reader.pages)} pages")
        text = reader.pages[page_number - 1].extract_text() or ""
        records.append({"pdf_page": page_number, "text": text.strip()})
    return records, version


def extract_with_mutool(pdf: Path, pages: list[int], extract_all: bool, encoding: str) -> tuple[list[dict[str, Any]], str] | None:
    if not shutil.which("mutool") or extract_all:
        return None
    version = command_version(["mutool", "-v"], encoding)
    records = []
    for page in pages:
        command = ["mutool", "draw", "-F", "txt", "-o", "-", str(pdf), str(page)]
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding=encoding,
            errors="replace",
            timeout=60,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or f"mutool failed on page {page}")
        records.append({"pdf_page": page, "text": result.stdout.strip()})
    return records, f"mutool; {version}"


def assess_quality(records: list[dict[str, Any]]) -> dict[str, Any]:
    page_summaries = []
    low_text_pages = 0
    for record in records:
        text = record["text"]
        stripped = text.strip()
        char_count = len(stripped)
        flags = []
        if char_count < 80:
            flags.append("low_text_or_possible_scan")
            low_text_pages += 1
        if "\ufffd" in stripped:
            flags.append("encoding_artifacts")
        if len(re.findall(r"[=+\-*/∑∫√≤≥]", stripped)) > 20:
            flags.append("formula_dense")
        if stripped.count("|") > 10 or len(re.findall(r"\s{4,}", stripped)) > 30:
            flags.append("possible_table_or_columns")
        page_summaries.append(
            {
                "pdf_page": record["pdf_page"],
                "char_count": char_count,
                "flags": flags,
                "needs_verification": any(flag in flags for flag in ("formula_dense", "possible_table_or_columns", "low_text_or_possible_scan")),
            }
        )

    avg_chars = sum(page["char_count"] for page in page_summaries) / max(len(page_summaries), 1)
    blockers = []
    if records and low_text_pages == len(records):
        blockers.append("likely_image_only_pdf_or_no_text_layer")

    if not records or low_text_pages >= max(1, len(records) // 2):
        rating = "low"
    elif avg_chars < 250 or any(page["flags"] for page in page_summaries):
        rating = "medium"
    else:
        rating = "high"

    return {
        "rating": rating,
        "average_chars_per_page": round(avg_chars, 1),
        "low_text_pages": low_text_pages,
        "blockers": blockers,
        "pages": page_summaries,
        "notes": [
            "This is a text-extraction heuristic rating, not a complete judgment of content quality.",
            "Figures, tables, formulas, OCR accuracy, and two-column reading order still need manual verification when flagged.",
            "If all sampled pages have near-zero text, use OCR or visual inspection before building source-grounded lessons.",
        ],
    }


def normalize_for_match(value: str) -> str:
    return re.sub(r"\s+", " ", value.casefold()).strip()


def locate_chapter(records: list[dict[str, Any]], title: str) -> dict[str, Any] | None:
    title = title.strip()
    if not title:
        return None

    normalized_title = normalize_for_match(title)
    title_tokens = {
        token for token in re.findall(r"[\w\u4e00-\u9fff]+", normalized_title) if len(token) >= 2
    }
    candidates = []
    for record in records:
        text = record["text"]
        normalized_text = normalize_for_match(text)
        first_block = normalize_for_match(text[:800])
        evidence = []
        score = 0.0
        if normalized_title and normalized_title in first_block:
            evidence.append("heading_or_early_text_exact_match")
            score = max(score, 1.0)
        elif normalized_title and normalized_title in normalized_text:
            evidence.append("page_text_exact_match")
            score = max(score, 0.85)

        if title_tokens:
            text_tokens = set(re.findall(r"[\w\u4e00-\u9fff]+", normalized_text))
            overlap = len(title_tokens & text_tokens) / len(title_tokens)
            if overlap >= 0.6:
                evidence.append(f"title_token_overlap={overlap:.2f}")
                score = max(score, overlap * 0.75)

        if evidence:
            candidates.append(
                {
                    "candidate_start_pdf_page": record["pdf_page"],
                    "candidate_end_pdf_page": None,
                    "evidence": evidence,
                    "score": round(score, 2),
                }
            )

    if not candidates:
        return {
            "query": title,
            "confidence": "low",
            "candidates": [],
            "notes": ["No title match found in extracted text; inspect outline/TOC or ask the user for pages."],
        }

    best = max(candidates, key=lambda item: item["score"])
    if best["score"] >= 0.95:
        confidence = "high"
    elif best["score"] >= 0.6:
        confidence = "medium"
    else:
        confidence = "low"
    return {
        "query": title,
        "confidence": confidence,
        "candidates": sorted(candidates, key=lambda item: item["score"], reverse=True)[:5],
        "notes": [
            "Candidate chapter location is based on extracted text matching only.",
            "Confirm boundaries with outline/TOC, printed page numbers, or user confirmation before generating a full study pack.",
        ],
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# PDF 抽取报告：{report['chapter_title'] or report['pdf_path']}",
        "",
        "该文件包含源文本抽取结果，仅用于本地学习材料制作；最终回答和学习包应以释义、综合和短引用为主。",
        "",
        "## 抽取记录",
        "",
        f"- 文件：{report['pdf_path']}",
        f"- 章节标题：{report['chapter_title'] or '未指定'}",
        f"- PDF 物理页：{report['pages_spec']}",
        f"- 印刷页码：{report['book_pages'] or '未指定'}",
        f"- 抽取工具：{report['extractor']}",
        f"- 抽取时间：{report['extracted_at']}",
        f"- 文本抽取启发式评级：{report['quality']['rating']}",
        "",
        "## 质量说明",
        "",
    ]
    lines.extend(f"- {note}" for note in report["quality"]["notes"])
    if report["quality"].get("blockers"):
        lines.extend(["", "## 抽取阻塞项", ""])
        lines.extend(f"- {blocker}" for blocker in report["quality"]["blockers"])

    if report.get("chapter_location"):
        location = report["chapter_location"]
        lines.extend(
            [
                "",
                "## 章节定位候选",
                "",
                f"- 查询标题：{location['query']}",
                f"- 置信度：{location['confidence']}",
                "",
                "| 候选起始页 | 候选结束页 | 分数 | 证据 |",
                "| --- | --- | ---: | --- |",
            ]
        )
        for candidate in location["candidates"]:
            evidence = ", ".join(candidate["evidence"])
            end_page = candidate["candidate_end_pdf_page"] or ""
            lines.append(
                f"| [PDF p.{candidate['candidate_start_pdf_page']}] | {end_page} | {candidate['score']} | {evidence} |"
            )
        lines.extend([""])
        lines.extend(f"- {note}" for note in location["notes"])

    lines.extend(
        [
            "",
            "## 每页质量",
            "",
            "| PDF 物理页 | 字符数 | 风险标记 | 需核对 |",
            "| --- | ---: | --- | --- |",
        ]
    )
    for page in report["quality"]["pages"]:
        flags = ", ".join(page["flags"]) if page["flags"] else ""
        needs_verification = "yes" if page["needs_verification"] else ""
        lines.append(
            f"| [PDF p.{page['pdf_page']}] | {page['char_count']} | {flags} | {needs_verification} |"
        )

    lines.extend(["", "## 抽取文本", ""])
    for record in report["pages"]:
        text = record["text"] or "待核对：该页未抽取到可靠文本。"
        lines.extend([f"### [PDF p.{record['pdf_page']}]", "", text, ""])
    return "\n".join(lines)


def run_extraction(pdf: Path, pages: list[int], extract_all: bool, encoding: str) -> tuple[list[dict[str, Any]], str]:
    extractors = (
        extract_with_pdftotext,
        extract_with_python_pdf,
        extract_with_mutool,
    )
    last_error: Exception | None = None
    for extractor in extractors:
        try:
            result = extractor(pdf, pages, extract_all, encoding)
            if result is not None:
                return result
        except Exception as exc:
            last_error = exc
    if last_error:
        raise RuntimeError(f"all available extractors failed; last error: {last_error}")
    raise RuntimeError("no PDF extractor found; install pdftotext, mutool, pypdf, or PyPDF2")


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract PDF text with page-level quality metadata.")
    parser.add_argument("pdf", help="PDF file path.")
    parser.add_argument("--pages", help="1-based PDF physical pages, e.g. 10-18,22.")
    parser.add_argument("--all", action="store_true", help="Extract the whole PDF.")
    parser.add_argument("--force-all", action="store_true", help="Allow large whole-PDF extraction.")
    parser.add_argument("--max-pages", type=int, default=80, help="Maximum pages without --force-all.")
    parser.add_argument("--encoding", default="utf-8", help="Encoding for external extractor output.")
    parser.add_argument("--chapter-title", default="", help="Chapter or section title.")
    parser.add_argument("--locate-chapter", default="", help="Search extracted text for a chapter title.")
    parser.add_argument("--book-pages", default="", help="Printed book page range if visible.")
    parser.add_argument("--out", help="Markdown output path.")
    parser.add_argument("--json-out", help="JSON output path.")
    parser.add_argument("--json", action="store_true", help="Print JSON to stdout.")
    args = parser.parse_args()

    pdf = Path(args.pdf)
    if not pdf.exists():
        print(f"PDF not found: {pdf}", file=sys.stderr)
        return 2
    if args.locate_chapter and not args.pages and not args.all:
        args.all = True
    if not args.pages and not args.all:
        parser.error("provide --pages, --all, or --locate-chapter")

    try:
        pages = parse_pages(args.pages)
        requested_count = len(pages)
        if args.all:
            page_count = detect_page_count(pdf, args.encoding)
            if not args.force_all and page_count is None:
                raise RuntimeError("cannot determine page count for --all; use --pages or --force-all")
            if not args.force_all and page_count is not None and page_count > args.max_pages:
                raise RuntimeError(
                    f"--all would extract {page_count} pages; use --pages or --force-all to continue"
                )
        elif not args.force_all and requested_count > args.max_pages:
            raise RuntimeError(
                f"requested {requested_count} pages; use a smaller --pages range or --force-all"
            )
        page_records, extractor = run_extraction(pdf, pages, args.all, args.encoding)
    except Exception as exc:
        print(f"extraction failed: {exc}", file=sys.stderr)
        return 2

    report = {
        "pdf_path": str(pdf),
        "chapter_title": args.chapter_title,
        "pages_spec": "all" if args.all else args.pages,
        "book_pages": args.book_pages,
        "extractor": extractor,
        "extracted_at": datetime.now().isoformat(timespec="seconds"),
        "quality": assess_quality(page_records),
        "chapter_location": locate_chapter(page_records, args.locate_chapter or args.chapter_title),
        "pages": page_records,
    }
    markdown = build_markdown(report)

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(markdown, encoding="utf-8")
    if args.json_out:
        json_path = Path(args.json_out)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif not args.out and not args.json_out:
        print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
