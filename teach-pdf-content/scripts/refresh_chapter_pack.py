#!/usr/bin/env python3
"""Refresh a chapter pack through build, compile, check, targeted repair, recompile, and recheck."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def safe_print_json(payload: dict) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    try:
        print(text)
    except UnicodeEncodeError:
        sys.stdout.buffer.write(text.encode("utf-8", errors="replace"))
        sys.stdout.buffer.write(b"\n")


def run_step(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def parse_json_output(result: subprocess.CompletedProcess[str]) -> dict:
    if result.returncode != 0 and not result.stdout.strip():
        raise RuntimeError(result.stderr.strip() or f"command failed: {' '.join(result.args)}")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"failed to parse JSON output from {' '.join(result.args)}: {exc}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        ) from exc


def script_path(name: str) -> Path:
    return Path(__file__).with_name(name)


def run_json_step(
    summary: dict[str, object],
    step_name: str,
    command: list[str],
    cwd: Path,
) -> tuple[subprocess.CompletedProcess[str], dict]:
    result = run_step(command, cwd)
    payload = parse_json_output(result)

    item: dict[str, object] = {"step": step_name, "returncode": result.returncode}
    if result.stdout.strip():
        item["stdout"] = result.stdout.strip()
    if result.stderr.strip():
        item["stderr"] = result.stderr.strip()
    item["payload"] = payload
    summary["steps"].append(item)
    return result, payload


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Refresh a chapter pack through build/compile/check/repair/recompile/recheck."
    )
    parser.add_argument("chapter_dir", help="Chapter directory.")
    parser.add_argument(
        "--skip-build-pages",
        action="store_true",
        help="Skip build_knowledge_pages.py.",
    )
    parser.add_argument(
        "--skip-compile",
        action="store_true",
        help="Skip the initial compile_detailed_notes_from_pages.py pass.",
    )
    parser.add_argument(
        "--skip-repair",
        action="store_true",
        help="Skip repair_knowledge_pages.py even if checker finds page warnings.",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON summary.")
    args = parser.parse_args()

    chapter_dir = Path(args.chapter_dir).resolve()
    if not chapter_dir.exists():
        print(f"chapter directory not found: {chapter_dir}", file=sys.stderr)
        return 2

    cwd = Path(__file__).resolve().parent
    summary: dict[str, object] = {
        "chapter_dir": str(chapter_dir),
        "steps": [],
    }

    if not args.skip_build_pages:
        result, _payload = run_json_step(
            summary,
            "build_knowledge_pages",
            [sys.executable, str(script_path("build_knowledge_pages.py")), str(chapter_dir), "--overwrite", "--json"],
            cwd,
        )
        if result.returncode != 0:
            if args.json:
                safe_print_json(summary)
            else:
                print(result.stderr, file=sys.stderr)
            return result.returncode

    if not args.skip_compile:
        result, _payload = run_json_step(
            summary,
            "compile_detailed_notes",
            [
                sys.executable,
                str(script_path("compile_detailed_notes_from_pages.py")),
                str(chapter_dir),
                "--overwrite",
                "--sync-anchors",
                "--json",
            ],
            cwd,
        )
        if result.returncode != 0:
            if args.json:
                safe_print_json(summary)
            else:
                print(result.stderr, file=sys.stderr)
            return result.returncode

    check_result, check_payload = run_json_step(
        summary,
        "check_before_repair",
        [sys.executable, str(script_path("check_lesson_pack_vnext.py")), str(chapter_dir), "--json"],
        cwd,
    )

    repaired = False
    if not args.skip_repair and check_payload.get("warnings", 0):
        repair_result, repair_payload = run_json_step(
            summary,
            "repair_knowledge_pages",
            [sys.executable, str(script_path("repair_knowledge_pages.py")), str(chapter_dir), "--json"],
            cwd,
        )
        repaired = bool(repair_payload.get("repaired_pages"))

        if repaired:
            recompile_result, _recompile_payload = run_json_step(
                summary,
                "compile_detailed_notes_after_repair",
                [
                    sys.executable,
                    str(script_path("compile_detailed_notes_from_pages.py")),
                    str(chapter_dir),
                    "--overwrite",
                    "--sync-anchors",
                    "--json",
                ],
                cwd,
            )
            if recompile_result.returncode != 0:
                if args.json:
                    safe_print_json(summary)
                else:
                    print(recompile_result.stderr, file=sys.stderr)
                return recompile_result.returncode

            recheck_result, recheck_payload = run_json_step(
                summary,
                "check_after_repair",
                [sys.executable, str(script_path("check_lesson_pack_vnext.py")), str(chapter_dir), "--json"],
                cwd,
            )
            final_payload = recheck_payload
            final_returncode = recheck_result.returncode
        else:
            final_payload = check_payload
            final_returncode = check_result.returncode
    else:
        final_payload = check_payload
        final_returncode = check_result.returncode

    summary["final"] = {
        "errors": final_payload.get("errors"),
        "warnings": final_payload.get("warnings"),
        "repaired": repaired,
    }

    if args.json:
        safe_print_json(summary)
    else:
        final = summary["final"]
        print(
            f"refreshed {chapter_dir} | errors={final['errors']} warnings={final['warnings']} repaired={final['repaired']}"
        )
    return final_returncode


if __name__ == "__main__":
    raise SystemExit(main())
