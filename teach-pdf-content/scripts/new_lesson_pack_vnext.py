#!/usr/bin/env python3
"""Create a vNext three-file lesson pack scaffold."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path


TEMPLATE_VERSION = "3.1"
CHECKER_VERSION = "3.1"


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    return value or "chapter"


def write_text(path: Path, content: str, overwrite: bool) -> dict[str, str]:
    if path.exists() and not overwrite:
        return {
            "status": "skipped",
            "path": str(path),
            "message": "skipped existing file; use --overwrite to replace it",
        }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return {"status": "written", "path": str(path), "message": "written"}


def default_out_dir(args: argparse.Namespace) -> tuple[Path, str, str]:
    source_seed = Path(args.source).stem if args.source else args.title
    source_id = args.source_id or slugify(source_seed)
    chapter_id = args.chapter_id or slugify(args.chapter or args.title)
    if args.out:
        return Path(args.out), source_id, chapter_id
    if args.project_root:
        return Path(args.project_root) / "lessons" / source_id / "chapters" / chapter_id, source_id, chapter_id
    return Path(chapter_id), source_id, chapter_id


ZH_TEMPLATES = {
    "detailed-notes.md": """# {title}

## 这章解决什么问题

- 本章主问题：
- 为什么会有这一章：
- 学完后你应该能做到：
- 原文依据：

## 先修提醒

- 需要已有的知识：
- 如果这里不稳，建议先回看：

## 本章知识地图

- 核心知识簇：
- 推荐起步节点：
- 最难节点：
- 对应图谱文件：`knowledge-map.json`

## 建议学习路径

- 第一次学习：
- 第二次整理：
- 复习回看：
- 主流程提醒：先补 `knowledge-pages.json`，再汇编本讲义。

## 起步例子 / 章节引子

```text

```

- 先观察什么：
- 看完至少要能说出什么：

## 本章主线

1.
2.
3.

## 小节讲解

### x.x 小节标题

#### 本节主问题

#### 本节知识点
| 知识点 ID | 名称 | 是否新概念 | 复杂度 | 重要度 | 掌握目标 |
| --- | --- | --- | --- | --- | --- |
| KP-x |  | 是/否 | C1-C4 | 高/中/低 | 识别/解释/区分/复述/应用/诊断 |

#### 先看一个最小例子

#### 先观察会发生什么

#### 正式结论 / 定义

#### 为什么成立

#### 过程追踪 / Trace

#### 边界、反例与易错点

#### 和相邻概念的区别

#### 代码 / 实现 / 题型连接

#### 本节闭卷输出模板

#### 本节自测

## 关键术语与公式速查

| 项目 | 最小定义/规则 | 使用条件 | 常错点 |
| --- | --- | --- | --- |
|  |  |  |  |

## 实现与代码连接

- 对应数据结构/表示：
- 空情况/边界情况：
- 最容易写错的位置：

## 易混概念总对比

| A | B | 关键差异 | 如何判断 |
| --- | --- | --- | --- |
|  |  |  |  |

## 闭卷输出模板

- 一句话版：
- 展开版：
- 如果题目问“为什么”应补充：

## 10 分钟速读路线

1.
2.
3.
""",
    "practice.md": """# {title} 练习与自测

## 使用方式

- 先做题，再看答案。
- 先做闭卷解释题，再做过程题和迁移题。

## 知识点与题目映射

| 知识点 ID | 题目 ID | 题型 | 难度 |
| --- | --- | --- | --- |
| KP-x | Q-01 | 解释/辨析/过程/迁移 | 基础/核心/提高 |

## 闭卷解释题

### Q-01

- 知识点：
- 题型：解释
- 难度：
- 目标能力：
- 建议耗时：

题目：

提示：

## 判断与辨析题

### Q-02

- 知识点：
- 题型：辨析
- 难度：

题目：

提示：

## 过程追踪题

### Q-03

- 知识点：
- 题型：过程
- 难度：

题目：

提示：

## 基础练习

### E-01

- 知识点：
- 题型：
- 难度：

题目：

提示：

## 核心练习

### E-02

- 知识点：
- 题型：
- 难度：

题目：

提示：

## 迁移练习

### E-03

- 知识点：
- 题型：迁移
- 难度：

题目：

提示：

## 常见错误诊断

### D-01

- 对应知识点：

错误说法：

为什么错：

正确说法：

## 完整答案与评分点

### Q-01

- 标准答案：
- 得分点 / 自查点：
- 常见误答：
- 错误原因：
- 回看位置：
""",
    "review-notes.md": """# {title} 复习笔记

## 本章 3 分钟回忆路线

1.
2.
3.

## 本章 10 分钟复习路线

1.
2.
3.

## 必记定义 / 规则 / 结论

- 

## 高价值易错点

| 易错点 | 正确说法 | 为什么容易错 |
| --- | --- | --- |
|  |  |  |

## 概念对比速查

| A | B | 关键差异 |
| --- | --- | --- |
|  |  |  |

## 口头复述模板

### 模板 1

- 题目：
- 标准骨架：
- 必须提到：
- 容易漏掉：

## 记忆卡片

### Core

- 卡片：

### Secondary

- 卡片：

### Trap

- 卡片：

## 错题回炉规则

- 如果同一个点错两次：
- 下一次回看时优先：

## 分日复习计划

### 今天

- 看什么：
- 说什么：
- 练什么：

### 明天

- 看什么：
- 说什么：
- 练什么：

### 三天后

- 看什么：
- 说什么：
- 练什么：

### 一周后

- 看什么：
- 说什么：
- 练什么：
""",
    "source-map.md": """# {title} Source Map

## 提取记录

- 文件：{source}
- 范围：{chapter}
- 提取工具：
- 提取命令或方法：
- 提取时间：{created_at}
- 章节定位置信度：
- 章节边界依据：

## 页码系统

| PDF 页 | 书页 | 标题/小节 | 说明 |
| --- | --- | --- | --- |
|  |  |  |  |

## 关键结论依据

| 结论/定义/公式 | 来源 | 可靠性说明 |
| --- | --- | --- |
|  |  |  |

## 提取质量

- 文本质量：
- 公式限制：
- 表格限制：
- 图示限制：
- 代码限制：
- 待人工核对内容：
""",
}


EN_TEMPLATES = {
    "detailed-notes.md": """# {title}

## What Problem This Chapter Solves

- Chapter problem:
- Why this chapter exists:
- What the learner should be able to do after learning it:
- Source basis:

## Prerequisites

- Required prior knowledge:
- Review first if weak:

## Chapter Knowledge Map

- Core knowledge clusters:
- Recommended start node:
- Hardest node:
- Graph file: `knowledge-map.json`

## Suggested Study Path

- First pass:
- Second pass:
- Review pass:

## Starter Example / Chapter Hook

```text

```

- What to notice first:
- What the learner must be able to say after this:

## Conceptual Spine

1.
2.
3.

## Section Teaching

### x.x Subsection Title

#### Subsection Question

#### Knowledge Points
| ID | Title | New Concept | Complexity | Importance | Mastery |
| --- | --- | --- | --- | --- | --- |
| KP-x |  | yes/no | C1-C4 | high/medium/low | recognize/explain/distinguish/sequence/apply/diagnose |

#### Minimum Example

#### Observation

#### Formal Result / Definition

#### Why It Holds

#### Process Trace

#### Boundaries, Counterexamples, and Traps

#### Difference From Nearby Concepts

#### Code / Implementation / Problem-Type Link

#### Closed-Book Retell Template

#### Self-Check

## Quick Terms and Formulas

## Implementation Bridge

## Easy Confusions

## Closed-Book Output Template

## 10-Minute Review Route
""",
    "practice.md": """# {title} Practice

## How To Use This File

## Knowledge-Point Mapping

## Closed-Book Explanation

## Discrimination Questions

## Process Trace Questions

## Basic Exercises

## Core Exercises

## Transfer Exercises

## Common Error Diagnosis

## Complete Answers and Scoring
""",
    "review-notes.md": """# {title} Review Notes

## 3-Minute Recall Route

## 10-Minute Review Route

## Must-Memorize Definitions / Rules / Results

## High-Value Traps

## Concept Comparison Quick Reference

## Oral Retell Templates

## Memory Cards

## Wrong-Answer Recovery Rules

## Spaced Review Plan
""",
    "source-map.md": """# {title} Source Map

## Extraction Record

- File: {source}
- Range: {chapter}
- Extraction tool:
- Extraction method:
- Extracted at: {created_at}
- Chapter-boundary confidence:
- Chapter-boundary evidence:
""",
}


def build_knowledge_map(values: dict[str, str]) -> dict[str, object]:
    return {
        "version": "1.0",
        "chapter_id": values["chapter_id"],
        "chapter_title": values["title"],
        "chapter_problem": "",
        "source_id": values["source_id"],
        "output_mode": values["output_mode"],
        "generated_at": values["created_at"],
        "recommended_paths": {"study": [], "review": []},
        "nodes": [],
        "edges": [],
        "clusters": [],
        "exercise_map": [],
        "review_map": [],
    }


def build_knowledge_pages(values: dict[str, str]) -> dict[str, object]:
    return {
        "version": "1.0",
        "chapter_id": values["chapter_id"],
        "chapter_title": values["title"],
        "source_id": values["source_id"],
        "output_mode": values["output_mode"],
        "generated_at": values["created_at"],
        "pages": [
            {
                "page_id": "kp-x",
                "knowledge_point_id": "kp-x",
                "title": "待补充知识点标题",
                "type": "concept_explanation",
                "page_kind": "concept",
                "complexity_level": "C2",
                "importance_level": "high",
                "teaching_profile": "standard",
                "clarity_risk": "medium",
                "estimated_teaching_minutes": 10,
                "prerequisites": [],
                "learning_goal": "",
                "entry_question": "",
                "page_summary": "",
                "must_answer": [
                    "这一页最少要回答哪 2-4 个具体问题？",
                    "学习者看完后还要能做到什么？"
                ],
                "exit_outcomes": [
                    "能用自己的话说出核心机制或区分标准",
                    "能从最小例子中指出这个知识点怎么用"
                ],
                "failure_signals": [
                    "如果学习者看完后仍会回到书上问“为什么”，说明这页还没讲清",
                    "如果学习者仍会把它和相邻概念混淆，说明边界和对比不够"
                ],
                "notes_anchor": "detailed-notes#x-x-知识点标题",
                "practice_refs": [],
                "review_refs": [],
                "source_refs": [],
                "blocks": [
                    {"type": "hook", "title": "入口问题", "content": [""]},
                    {"type": "formal_statement", "title": "正式结论 / 定义", "content": [""]},
                    {"type": "minimum_example", "title": "最小例子", "content": [""]},
                    {"type": "why_it_holds", "title": "为什么成立", "content": [""]},
                    {"type": "trace", "title": "过程追踪", "content": [""]},
                    {"type": "confusion_fix", "title": "易错点 / 误区", "content": [""]},
                    {"type": "closed_book_retell", "title": "闭卷输出", "content": [""]},
                    {"type": "recap", "title": "一句话回顾", "content": [""]},
                ],
            }
        ],
    }


def choose_templates(language: str) -> dict[str, str]:
    return ZH_TEMPLATES if language == "zh" else EN_TEMPLATES


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a vNext three-file lesson pack scaffold.")
    parser.add_argument("--title", required=False, help="Lesson or chapter title.")
    parser.add_argument("--source", help="Source PDF or document path.")
    parser.add_argument("--chapter", help="Chapter, section, or page range.")
    parser.add_argument("--out", help="Output directory.")
    parser.add_argument("--project-root", help="Class project root. If --out is omitted, write under lessons/<source-id>/chapters/<chapter-id>.")
    parser.add_argument("--source-id", help="ASCII source id.")
    parser.add_argument("--chapter-id", help="ASCII chapter id.")
    parser.add_argument("--language", choices=["zh", "en"], default="zh")
    parser.add_argument(
        "--output-mode",
        choices=["beginner_lecture", "standard_study_pack", "review_cram"],
        default="beginner_lecture",
    )
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing files.")
    parser.add_argument("--json", action="store_true", help="Print a JSON summary.")
    parser.add_argument("--template-version", action="store_true", help="Print template version and exit.")
    args = parser.parse_args()

    if args.template_version:
        print(TEMPLATE_VERSION)
        return 0
    if not args.title:
        parser.error("--title is required unless --template-version is used")

    created_at = datetime.now().isoformat(timespec="seconds")
    out_dir, source_id, chapter_id = default_out_dir(args)
    templates = choose_templates(args.language)
    unspecified = "未指定" if args.language == "zh" else "unspecified"
    values = {
        "title": args.title,
        "source": args.source or unspecified,
        "chapter": args.chapter or unspecified,
        "created_at": created_at,
        "source_id": source_id,
        "chapter_id": chapter_id,
        "output_mode": args.output_mode,
    }

    results: dict[str, dict[str, str]] = {}
    for name, template in templates.items():
        results[name] = write_text(out_dir / name, template.format(**values), args.overwrite)

    knowledge_map = build_knowledge_map(values)
    results["knowledge-map.json"] = write_text(
        out_dir / "knowledge-map.json",
        json.dumps(knowledge_map, ensure_ascii=False, indent=2) + "\n",
        args.overwrite,
    )
    knowledge_pages = build_knowledge_pages(values)
    results["knowledge-pages.json"] = write_text(
        out_dir / "knowledge-pages.json",
        json.dumps(knowledge_pages, ensure_ascii=False, indent=2) + "\n",
        args.overwrite,
    )

    meta = {
        "title": args.title,
        "source": values["source"],
        "chapter": values["chapter"],
        "language": args.language,
        "output_mode": args.output_mode,
        "output_format": "vnext",
        "template_version": TEMPLATE_VERSION,
        "checker_version": CHECKER_VERSION,
        "created_at": created_at,
        "source_id": source_id,
        "chapter_id": chapter_id,
        "files": [
            "detailed-notes.md",
            "practice.md",
            "review-notes.md",
            "knowledge-map.json",
            "knowledge-pages.json",
            "source-map.md",
        ],
    }
    results["_meta.json"] = write_text(
        out_dir / "_meta.json",
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
        args.overwrite,
    )

    if args.project_root and not args.out:
        chapter_index = Path(args.project_root) / "lessons" / source_id / "chapter-index.md"
        index_text = (
            f"# Chapter Index: {source_id}\n\n"
            "| Chapter ID | Title | Range | Status |\n"
            "| --- | --- | --- | --- |\n"
            f"| {chapter_id} | {args.title} | {values['chapter']} | scaffolded-vnext |\n"
        )
        results["chapter-index.md"] = write_text(chapter_index, index_text, overwrite=False)

    summary = {
        "out_dir": str(out_dir),
        "template_version": TEMPLATE_VERSION,
        "checker_version": CHECKER_VERSION,
        "source_id": source_id,
        "chapter_id": chapter_id,
        "results": results,
    }
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        for name, result in results.items():
            print(f"{name}: {result['status']} {result['path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
