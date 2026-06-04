#!/usr/bin/env python3
"""OCR selected PDF pages into a class-project workspace."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def parse_pages(spec: str) -> list[int]:
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
    if not pages or any(page < 1 for page in pages):
        raise ValueError("pages must be positive 1-based PDF pages")
    return sorted(dict.fromkeys(pages))


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    return value


def source_id_for(pdf: Path, provided: str | None) -> str:
    if provided:
        slug = slugify(provided)
        if len(slug) >= 3:
            return slug
        digest = hashlib.sha1(provided.encode("utf-8")).hexdigest()[:8]
        return f"source-{digest}"
    slug = slugify(pdf.stem)
    if len(slug) >= 3:
        return slug
    digest = hashlib.sha1(str(pdf).encode("utf-8")).hexdigest()[:8]
    return f"source-{digest}"


def ensure_under_root(root: Path, path: Path) -> Path:
    resolved = path.resolve()
    root_resolved = root.resolve()
    if not str(resolved).lower().startswith(str(root_resolved).lower()):
        raise ValueError(f"path escapes project root: {resolved}")
    return resolved


def run_command(command: list[str], encoding: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding=encoding,
        errors="replace",
        timeout=180,
    )


def find_tesseract(preferred: str | None) -> str | None:
    if preferred:
        path = Path(preferred)
        if path.exists():
            return str(path)
        return shutil.which(preferred)
    found = shutil.which("tesseract")
    if found:
        return found
    candidates: list[Path] = []
    for env_name in ("ProgramFiles", "ProgramFiles(x86)"):
        base = os.environ.get(env_name)
        if base:
            candidates.append(Path(base) / "Tesseract-OCR" / "tesseract.exe")
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return None


def required_tessdata(lang: str) -> list[str]:
    return [part for part in re.split(r"[+,\s]+", lang) if part]


def main() -> int:
    parser = argparse.ArgumentParser(description="Render selected PDF pages and OCR them locally.")
    parser.add_argument("pdf", help="Source PDF path.")
    parser.add_argument("--pages", required=True, help="1-based PDF pages, e.g. 10-12,15.")
    parser.add_argument("--project-root", default=".", help="Class project root. Defaults to current directory.")
    parser.add_argument("--source-id", help="ASCII id for this source.")
    parser.add_argument("--lang", default="chi_sim+eng", help="Tesseract language list.")
    parser.add_argument("--tesseract-exe", help="Tesseract executable path. Auto-detect if omitted.")
    parser.add_argument("--dpi", type=int, default=300)
    parser.add_argument("--psm", type=int, default=6, help="Tesseract page segmentation mode.")
    parser.add_argument("--encoding", default="utf-8", help="Subprocess output encoding.")
    parser.add_argument("--allow-global-tessdata", action="store_true", help="Use globally installed Tesseract language data.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing rendered images/text.")
    parser.add_argument("--json", action="store_true", help="Print JSON summary.")
    args = parser.parse_args()

    pdf = Path(args.pdf).resolve()
    if not pdf.exists():
        print(f"PDF not found: {pdf}", file=sys.stderr)
        return 2
    pdftoppm = shutil.which("pdftoppm")
    tesseract = find_tesseract(args.tesseract_exe)
    if not pdftoppm:
        print("pdftoppm not found; install Poppler or provide it in PATH", file=sys.stderr)
        return 2
    if not tesseract:
        print("tesseract not found; install Tesseract OCR or pass --tesseract-exe", file=sys.stderr)
        return 2

    try:
        pages = parse_pages(args.pages)
    except ValueError as exc:
        print(f"invalid --pages: {exc}", file=sys.stderr)
        return 2

    project_root = Path(args.project_root).resolve()
    project_root.mkdir(parents=True, exist_ok=True)
    source_id = source_id_for(pdf, args.source_id)
    cache_dir = ensure_under_root(project_root, project_root / ".teach-pdf-content" / "cache" / "ocr" / source_id)
    text_dir = ensure_under_root(project_root, project_root / "extracts" / "ocr" / source_id)
    log_dir = ensure_under_root(project_root, project_root / ".teach-pdf-content" / "logs" / "ocr")
    tessdata_dir = ensure_under_root(project_root, project_root / ".teach-pdf-content" / "models" / "tesseract" / "tessdata")
    for directory in (cache_dir, text_dir, log_dir, tessdata_dir):
        directory.mkdir(parents=True, exist_ok=True)

    missing_langs = [
        lang for lang in required_tessdata(args.lang) if not (tessdata_dir / f"{lang}.traineddata").exists()
    ]
    if missing_langs and not args.allow_global_tessdata:
        print(
            "missing local tessdata files under project root: "
            + ", ".join(f"{lang}.traineddata" for lang in missing_langs),
            file=sys.stderr,
        )
        print(f"expected directory: {tessdata_dir}", file=sys.stderr)
        return 2

    page_results: list[dict[str, Any]] = []
    for page in pages:
        image_prefix = cache_dir / f"page-{page:04d}"
        image_path = image_prefix.with_suffix(".png")
        text_base = text_dir / f"page-{page:04d}"
        text_path = text_base.with_suffix(".txt")
        if image_path.exists() and text_path.exists() and not args.overwrite:
            page_results.append({"pdf_page": page, "status": "skipped", "image": str(image_path), "text": str(text_path)})
            continue

        render_command = [
            pdftoppm,
            "-r",
            str(args.dpi),
            "-png",
            "-f",
            str(page),
            "-l",
            str(page),
            "-singlefile",
            str(pdf),
            str(image_prefix),
        ]
        render = run_command(render_command, args.encoding)
        if render.returncode != 0:
            page_results.append({"pdf_page": page, "status": "render_failed", "stderr": render.stderr})
            continue

        ocr_command = [tesseract, str(image_path), str(text_base), "-l", args.lang, "--psm", str(args.psm)]
        if not args.allow_global_tessdata:
            ocr_command.extend(["--tessdata-dir", str(tessdata_dir)])
        ocr = run_command(ocr_command, args.encoding)
        status = "written" if ocr.returncode == 0 else "ocr_failed"
        char_count = len(text_path.read_text(encoding="utf-8", errors="replace")) if text_path.exists() else 0
        page_results.append(
            {
                "pdf_page": page,
                "status": status,
                "image": str(image_path),
                "text": str(text_path),
                "char_count": char_count,
                "render_stderr": render.stderr,
                "ocr_stderr": ocr.stderr,
            }
        )

    summary = {
        "pdf": str(pdf),
        "project_root": str(project_root),
        "source_id": source_id,
        "lang": args.lang,
        "dpi": args.dpi,
        "tessdata_dir": str(tessdata_dir),
        "allow_global_tessdata": args.allow_global_tessdata,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "pages": page_results,
    }
    log_path = log_dir / f"{source_id}.json"
    log_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary["log_path"] = str(log_path)

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(f"log: {log_path}")
        for result in page_results:
            print(f"{result['status']}: [PDF p.{result['pdf_page']}]")
    failed = any(result["status"].endswith("failed") for result in page_results)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
