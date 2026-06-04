#!/usr/bin/env python3
"""Create a Markdown study-pack scaffold for a source-grounded lesson."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path


TEMPLATE_VERSION = "2.1"
CHECKER_VERSION = "1.1"
FULL_FILE_ORDER = [
    "00-learning-path.md",
    "01-lesson-notes.md",
    "02-active-recall.md",
    "03-exercises.md",
    "04-glossary.md",
    "05-review-plan.md",
    "source-map.md",
]
SHORT_FILE_ORDER = [
    "00-learning-path.md",
    "01-lesson-notes.md",
    "02-active-recall.md",
    "source-map.md",
]


FILES_ZH = {
    "00-learning-path.md": """# 学习路径：{title}

## 来源与范围

- 文件：{source}
- 范围：{chapter}
- 创建时间：{created_at}
- 模板版本：{template_version}

## 学习者画像

| 维度 | 内容 |
| --- | --- |
| 当前水平 |  |
| 学习目的 |  |
| 可用时间 |  |
| 考试/作业/项目导向 |  |
| 是否需要中英术语对照 |  |

## 预计用时

- 初读：
- 深入学习：
- 练习与复习：

## 学习目标

| ID | 可观察能力 | 达成标准 | 对应练习 | 来源 |
| --- | --- | --- | --- | --- |
| LO1 | 能... | 闭卷回答包含... | Q1, E1 | [PDF p.x] |
| LO2 | 能... | 能在新情境中... | Q2, E2 | [Section x] |

## 先修知识

- 

## 推荐学习顺序

1. 
2. 
3. 

## 完成标准

- [ ] 所有 LO 都能闭卷解释。
- [ ] Basic/Core 题达到自定评分标准。
- [ ] 至少完成 1 道 Transfer 题并能解释适用边界。
""",
    "01-lesson-notes.md": """# 课程笔记：{title}

## 本章解决的问题

- 原文依据：

## 概念主线

1. 
2. 
3. 

## 关键定义与来源

| 概念 | 精确定义 | 直觉解释 | 来源 |
| --- | --- | --- | --- |
|  |  | 教师补充： | [PDF p.x] |

## 分层讲解

### 1. 

- 原文依据：
- 教师补充：
- 合理推断：
- 待核对：
- 检查点：

### 2. 

- 原文依据：
- 教师补充：
- 合理推断：
- 待核对：
- 检查点：

## 最小例子

- 原文依据或教师补充：

## 反例与边界

- 

## 公式 / 表格 / 图示说明

### 公式

| 原式 | 符号含义 | 适用条件 | 最小算例 | 常见误用 | 来源 |
| --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |

### 表格

| 比较对象 | 比较维度 | 主要差异 | 读表结论 | 可能误读 | 来源 |
| --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |

### 图示

| 图中元素 | 元素关系 | 支持的结论 | 不能证明什么 | 来源 |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |

## 教师补充

- 

## 本章小结

- 
""",
    "02-active-recall.md": """# 主动回忆：{title}

## 闭卷解释题

| ID | 目标 | 题目 | 自检标准 | 来源 |
| --- | --- | --- | --- | --- |
| Q1 | LO1 |  |  | [PDF p.x] |

## 概念辨析题

| ID | 目标 | 题目 | 答案要点 | 常见错误 |
| --- | --- | --- | --- | --- |
| Q2 | LOx |  |  |  |

## 填空题

1. 
   - 答案：

## 错因判断题

1. 错误说法：
   - 为什么错：
   - 正确说法：

## 迁移自测题

1. 教师设计题，不是原文例题：
   - 答案要点：
   - 检查的目标：
""",
    "03-exercises.md": """# 练习与答案：{title}

## Basic

### E1

- 目标：LOx
- 类型：recall | discrimination | procedure | error-correction | transfer
- 难度：Basic
- 题目：
- 标准答案：
- 评分要点：
- 常见错误：
- 来源依据：
- 进一步追问：

## Core

### E2

- 目标：LOx
- 类型：
- 难度：Core
- 题目：
- 标准答案：
- 评分要点：
- 常见错误：
- 来源依据：
- 进一步追问：

## Transfer

### E3

- 目标：LOx
- 类型：transfer
- 难度：Transfer
- 题目：教师设计题，不是原文例题。
- 标准答案：
- 评分要点：
- 常见错误：
- 来源依据或教师补充：
- 进一步追问：
""",
    "04-glossary.md": """# 术语、公式与易混点：{title}

## 术语表

| 术语 | 定义 | 直觉解释 | 来源 | 例子 | 反例 |
| --- | --- | --- | --- | --- | --- |
|  |  | 教师补充： | [PDF p.x] |  |  |

## 公式与符号

| 符号/公式 | 含义 | 条件 | 常见误用 | 来源 |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |

## 易混概念

| 概念 A | 概念 B | 关键差异 | 判断方法 | 常见错误 |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |
""",
    "05-review-plan.md": """# 复习计划：{title}

## 今天

- 重测目标：
- 任务：
- 完成标准：

## 明天

- 重测目标：
- 任务：
- 完成标准：

## 三天后

- 重测目标：
- 任务：
- 完成标准：

## 一周后

- 重测目标：
- 任务：
- 完成标准：

## 错题回炉规则

- 如果闭卷解释缺少关键条件，回到对应小节并补做辨析题。
- 如果迁移题失败，补做反例/边界练习。
- 如果公式误用，重写符号含义、适用条件和最小算例。
""",
    "source-map.md": """# 来源映射：{title}

## 抽取记录

- 文件：{source}
- 范围：{chapter}
- 抽取工具：
- 抽取命令或方法：
- 抽取时间：{created_at}
- 章节定位置信度：高 / 中 / 低
- 章节定位依据：

## 页码体系

| PDF 物理页 | 印刷页码 | 小节/标题 | 主题 | 备注 |
| --- | --- | --- | --- | --- |
| [PDF p.x] | [Book p.y] |  |  |  |

## 关键结论证据

| 结论/定义/公式 | 来源 | 可靠性备注 |
| --- | --- | --- |
|  | [PDF p.x] |  |

## 抽取质量

- 文本质量：高 / 中 / 低
- 疑似 OCR 问题：
- 公式限制：
- 表格限制：
- 图示限制：
- 未可靠抽取内容：
- 需要人工核对的位置：
""",
}


FILES_EN = {
    "00-learning-path.md": """# Learning Path: {title}

## Source and Scope

- File: {source}
- Range: {chapter}
- Created: {created_at}
- Template version: {template_version}

## Learner Profile

| Dimension | Notes |
| --- | --- |
| Current level |  |
| Learning goal |  |
| Available time |  |
| Exam/homework/project context |  |
| Bilingual terminology needed |  |

## Time Estimate

- First pass:
- Deep study:
- Practice and review:

## Learning Objectives

| ID | Observable performance | Mastery criterion | Assessed by | Source |
| --- | --- | --- | --- | --- |
| LO1 | Can... | Closed-book answer includes... | Q1, E1 | [PDF p.x] |
| LO2 | Can... | Can apply in a new scenario... | Q2, E2 | [Section x] |

## Prerequisites

- 

## Recommended Order

1. 
2. 
3. 

## Completion Standard

- [ ] Explain every LO closed-book.
- [ ] Meet the scoring standard for Basic/Core exercises.
- [ ] Complete at least one Transfer exercise and explain the boundary conditions.
""",
    "01-lesson-notes.md": """# Lesson Notes: {title}

## Problem This Chapter Solves

- Source basis:

## Conceptual Spine

1. 
2. 
3. 

## Key Definitions and Sources

| Concept | Precise definition | Intuition | Source |
| --- | --- | --- | --- |
|  |  | Teacher supplement: | [PDF p.x] |

## Layered Explanation

### 1. 

- Source basis:
- Teacher supplement:
- Reasoned inference:
- Needs verification:
- Checkpoint:

### 2. 

- Source basis:
- Teacher supplement:
- Reasoned inference:
- Needs verification:
- Checkpoint:

## Minimal Example

- Source basis or teacher supplement:

## Counterexamples and Boundaries

- 

## Formula / Table / Figure Notes

### Formula

| Formula | Symbol meanings | Conditions | Minimal calculation | Common misuse | Source |
| --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |

### Table

| Objects | Dimensions | Main differences | Reading conclusion | Possible misread | Source |
| --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |

### Figure

| Elements | Relationships | Supported conclusion | What it does not prove | Source |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |

## Teacher Supplements

- 

## Chapter Summary

- 
""",
    "02-active-recall.md": """# Active Recall: {title}

## Closed-Book Explanation

| ID | Objective | Prompt | Self-check standard | Source |
| --- | --- | --- | --- | --- |
| Q1 | LO1 |  |  | [PDF p.x] |

## Concept Discrimination

| ID | Objective | Prompt | Answer points | Common error |
| --- | --- | --- | --- | --- |
| Q2 | LOx |  |  |  |

## Cloze Prompts

1. 
   - Answer:

## Error Diagnosis

1. Wrong statement:
   - Why it is wrong:
   - Correct version:

## Transfer Self-Test

1. Teacher-designed prompt, not a source example:
   - Answer points:
   - Objective tested:
""",
    "03-exercises.md": """# Exercises and Answers: {title}

## Basic

### E1

- Objective: LOx
- Type: recall | discrimination | procedure | error-correction | transfer
- Difficulty: Basic
- Prompt:
- Expected answer:
- Scoring points:
- Common wrong answer:
- Source basis:
- Follow-up:

## Core

### E2

- Objective: LOx
- Type:
- Difficulty: Core
- Prompt:
- Expected answer:
- Scoring points:
- Common wrong answer:
- Source basis:
- Follow-up:

## Transfer

### E3

- Objective: LOx
- Type: transfer
- Difficulty: Transfer
- Prompt: Teacher-designed prompt, not a source example.
- Expected answer:
- Scoring points:
- Common wrong answer:
- Source basis or teacher supplement:
- Follow-up:
""",
    "04-glossary.md": """# Terms, Formulas, and Confusions: {title}

## Terms

| Term | Definition | Intuition | Source | Example | Non-example |
| --- | --- | --- | --- | --- | --- |
|  |  | Teacher supplement: | [PDF p.x] |  |  |

## Formulas and Symbols

| Symbol/formula | Meaning | Conditions | Common misuse | Source |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |

## Easily Confused Concepts

| Concept A | Concept B | Key difference | How to decide | Common error |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |
""",
    "05-review-plan.md": """# Review Plan: {title}

## Today

- Objectives to retest:
- Task:
- Completion standard:

## Tomorrow

- Objectives to retest:
- Task:
- Completion standard:

## Three Days Later

- Objectives to retest:
- Task:
- Completion standard:

## One Week Later

- Objectives to retest:
- Task:
- Completion standard:

## Wrong-Answer Recovery Rules

- If a closed-book explanation misses key conditions, return to the source section and add a discrimination question.
- If a transfer exercise fails, practice counterexamples and boundary cases.
- If a formula is misused, rewrite symbol meanings, conditions, and a minimal calculation.
""",
    "source-map.md": """# Source Map: {title}

## Extraction Record

- File: {source}
- Range: {chapter}
- Extraction tool:
- Extraction command or method:
- Extracted at: {created_at}
- Chapter-location confidence: high / medium / low
- Chapter-boundary evidence:

## Page Systems

| Physical PDF page | Printed page | Section/title | Topic | Notes |
| --- | --- | --- | --- | --- |
| [PDF p.x] | [Book p.y] |  |  |  |

## Evidence for Key Claims

| Claim/definition/formula | Source | Reliability note |
| --- | --- | --- |
|  | [PDF p.x] |  |

## Extraction Quality

- Text quality: high / medium / low
- Suspected OCR issues:
- Formula limitations:
- Table limitations:
- Figure limitations:
- Content not reliably extracted:
- Locations needing manual verification:
""",
}


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    return value


def default_out_dir(title: str, created_at: datetime) -> Path:
    slug = slugify(title)
    if len(slug) >= 3:
        base = Path(slug)
    else:
        digest = hashlib.sha1(title.encode("utf-8")).hexdigest()[:8]
        stamp = created_at.strftime("%Y%m%d-%H%M%S")
        base = Path(f"lesson-pack-{stamp}-{digest}")

    candidate = base
    index = 2
    while candidate.exists():
        candidate = Path(f"{base}-{index}")
        index += 1
    return candidate


def write_file(path: Path, content: str, overwrite: bool) -> dict[str, str]:
    if path.exists() and not overwrite:
        return {
            "status": "skipped",
            "path": str(path),
            "message": "skipped existing file; use --overwrite or choose a new --out",
        }
    path.write_text(content, encoding="utf-8")
    return {"status": "written", "path": str(path), "message": "written"}


def choose_files(language: str, pack: str) -> dict[str, str]:
    templates = FILES_ZH if language == "zh" else FILES_EN
    order = FULL_FILE_ORDER if pack == "full" else SHORT_FILE_ORDER
    return {name: templates[name] for name in order}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create Markdown files for a structured, source-grounded study pack."
    )
    parser.add_argument("--title", required=False, help="Lesson or chapter title.")
    parser.add_argument("--source", help="Source PDF or document path.")
    parser.add_argument("--chapter", help="Chapter, section, or page range.")
    parser.add_argument("--out", help="Output directory. Defaults to a unique slug from title.")
    parser.add_argument("--language", choices=["zh", "en"], default="zh")
    parser.add_argument("--pack", choices=["full", "short"], default="full")
    parser.add_argument("--require-source", action="store_true", help="Fail when --source or --chapter is missing.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing files.")
    parser.add_argument("--json", action="store_true", help="Print a machine-readable JSON summary.")
    parser.add_argument("--template-version", action="store_true", help="Print template version and exit.")
    args = parser.parse_args()

    if args.template_version:
        print(TEMPLATE_VERSION)
        return 0

    if not args.title:
        parser.error("--title is required unless --template-version is used")
    if args.require_source and (not args.source or not args.chapter):
        parser.error("--require-source needs both --source and --chapter")

    created_at_dt = datetime.now()
    created_at = created_at_dt.isoformat(timespec="seconds")
    out_dir = Path(args.out) if args.out else default_out_dir(args.title, created_at_dt)
    out_dir.mkdir(parents=True, exist_ok=True)

    unspecified = "未指定" if args.language == "zh" else "unspecified"
    warnings = []
    if not args.source:
        warnings.append("missing_source")
    if not args.chapter:
        warnings.append("missing_chapter")
    values = {
        "title": args.title,
        "source": args.source or unspecified,
        "chapter": args.chapter or unspecified,
        "created_at": created_at,
        "template_version": TEMPLATE_VERSION,
    }

    templates = choose_files(args.language, args.pack)
    results = {}
    for filename, template in templates.items():
        results[filename] = write_file(out_dir / filename, template.format(**values), args.overwrite)

    meta = {
        "title": args.title,
        "source": values["source"],
        "chapter": values["chapter"],
        "language": args.language,
        "pack": args.pack,
        "template_version": TEMPLATE_VERSION,
        "checker_version": CHECKER_VERSION,
        "created_at": created_at,
        "files": sorted(templates),
        "warnings": warnings,
    }
    results["_meta.json"] = write_file(
        out_dir / "_meta.json",
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
        args.overwrite,
    )

    summary = {
        "out_dir": str(out_dir),
        "template_version": TEMPLATE_VERSION,
        "checker_version": CHECKER_VERSION,
        "language": args.language,
        "pack": args.pack,
        "warnings": warnings,
        "results": results,
    }
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        for filename, result in results.items():
            print(f"{result['status']}: {result['path']} ({result['message']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
