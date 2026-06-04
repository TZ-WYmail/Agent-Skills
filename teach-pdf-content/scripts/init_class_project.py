#!/usr/bin/env python3
"""Initialize a local class-project workspace for source-grounded learning."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path


CONFIG_VERSION = "1.0"
DIRS = [
    ".teach-pdf-content/config",
    ".teach-pdf-content/models/tesseract/tessdata",
    ".teach-pdf-content/models/paddleocr",
    ".teach-pdf-content/cache/ocr",
    ".teach-pdf-content/logs",
    "sources",
    "extracts/pdf-text",
    "extracts/ocr",
    "lessons",
    "reviews",
]


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    return value or "class-project"


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a class-project workspace.")
    parser.add_argument("--project-root", default=".", help="Project root. Defaults to current directory.")
    parser.add_argument("--course-title", required=True, help="Human-readable course title.")
    parser.add_argument("--course-id", help="ASCII course id. Defaults to a slug from title.")
    parser.add_argument("--source", help="Primary source PDF path.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing class_project.json.")
    parser.add_argument("--json", action="store_true", help="Print JSON summary.")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    project_root.mkdir(parents=True, exist_ok=True)
    for relative in DIRS:
        (project_root / relative).mkdir(parents=True, exist_ok=True)

    course_id = args.course_id or slugify(args.course_title)
    config_path = project_root / ".teach-pdf-content" / "config" / "class_project.json"
    config = {
        "config_version": CONFIG_VERSION,
        "course_title": args.course_title,
        "course_id": course_id,
        "project_root": str(project_root),
        "source": str(Path(args.source).resolve()) if args.source else "",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "paths": {
            "config": ".teach-pdf-content/config",
            "models": ".teach-pdf-content/models",
            "cache": ".teach-pdf-content/cache",
            "logs": ".teach-pdf-content/logs",
            "sources": "sources",
            "extracts": "extracts",
            "lessons": "lessons",
            "reviews": "reviews",
        },
    }

    status = "skipped"
    if args.overwrite or not config_path.exists():
        config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        status = "written"

    summary = {
        "project_root": str(project_root),
        "course_id": course_id,
        "config_path": str(config_path),
        "config_status": status,
        "directories": DIRS,
    }
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(f"{status}: {config_path}")
        for relative in DIRS:
            print(f"dir: {project_root / relative}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
