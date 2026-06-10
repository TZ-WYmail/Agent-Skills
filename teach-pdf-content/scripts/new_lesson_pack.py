#!/usr/bin/env python3
"""Create a Markdown study-pack scaffold for a source-grounded lesson."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path


TEMPLATE_VERSION = "2.5"
CHECKER_VERSION = "1.5"
FULL_FILE_ORDER = [
    "00-learning-path.md",
    "01-lesson-notes.md",
    "02-active-recall.md",
    "03-exercises.md",
    "04-glossary.md",
    "05-review-plan.md",
    "06-memory-cards.md",
    "07-code-extracts.md",
    "source-map.md",
]
SHORT_FILE_ORDER = [
    "00-learning-path.md",
    "01-lesson-notes.md",
    "02-active-recall.md",
    "source-map.md",
]

CHAPTER_INDEX_ZH = """# 章节索引：{source_id}

## 来源

- 文件：{source}
- 创建时间：{created_at}
- 说明：长课程或长 PDF 应按章节/模块逐个生成学习包，不要合成一个巨大 Markdown。

## 章节计划

| 章节 ID | 标题 | 范围 | 状态 | 输出目录 | 备注 |
| --- | --- | --- | --- | --- | --- |
| {chapter_id} | {title} | {chapter} | scaffolded | chapters/{chapter_id} |  |
"""

CHAPTER_INDEX_EN = """# Chapter Index: {source_id}

## Source

- File: {source}
- Created: {created_at}
- Note: Split long courses or long PDFs into chapter/module study packs instead of one huge Markdown file.

## Chapter Plan

| Chapter ID | Title | Range | Status | Output directory | Notes |
| --- | --- | --- | --- | --- | --- |
| {chapter_id} | {title} | {chapter} | scaffolded | chapters/{chapter_id} |  |
"""


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

## 章节学习用时表

| 学习块 | 来源范围 | 目标 | 任务 | 建议用时 | 完成检查 |
| --- | --- | --- | --- | --- | --- |
| 初读 | {chapter} | 建立章节地图 | 标出标题、关键概念、疑问 |  | 能说出本章解决的问题 |
| 精学 |  | LOx | 学习核心小节并写闭环笔记 |  | 能闭卷解释核心机制 |
| 练习 |  | LOx | 完成基础/核心题 |  | 对照答案区完成自评 |
| 复习 |  | LOx | 记忆卡与错题回炉 |  | 3 分钟口头复述通过 |

## 压缩学习方案

| 可用时间 | 必做 | 可跳过 | 风险 |
| --- | --- | --- | --- |
| 30 分钟 |  |  |  |
| 60 分钟 |  |  |  |

## 学习目标

| ID | 可观察能力 | 达成标准 | 对应练习 | 来源 |
| --- | --- | --- | --- | --- |
| LO1 | 能... | 闭卷回答包含... | Q1, E1 | [PDF p.x] |
| LO2 | 能... | 能在新情境中... | Q2, E2 | [Section x] |

## 知识点掌握标准

| 知识点 | 掌握层级 | 闭卷标准 | 是否必须记忆 | 检查方式 | 来源 |
| --- | --- | --- | --- | --- | --- |
|  | recognize / explain / distinguish / sequence / apply / memorize / diagnose |  | 是 / 否 | Qx / Ex / Cx | [PDF p.x] |

## 章节管理

- 所属来源 ID：{source_id}
- 章节 ID：{chapter_id}
- 上一章：
- 下一章：
- 是否需要拆分为更多模块：

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

## 标题与范围

- 章节：{title}
- 来源：{source}
- 页码或范围：{chapter}
- 来源映射：`source-map.md`
- 抽取质量/待核对：
- 文件编码：UTF-8
- 本章主题：

## 如何使用本笔记

- 第一遍必读：
- 第二遍加强：
- 做题前必须会：
- 配套主动回忆：`02-active-recall.md`
- 配套练习：`03-exercises.md`
- 配套代码摘录：`07-code-extracts.md`
- 来源核对：`source-map.md`

## 本章地图

用树状图或流程图展示本章知识结构。结构类、算法类、转换类章节必须有图示或 ASCII 草图。

```text

```

## 分层学习路线

| 层级 | 内容 | 完成标准 |
| --- | --- | --- |
| 第一遍必读 |  | 能说出核心问题和主线 |
| 第二遍加强 |  | 能做核心例题和辨析题 |
| 拓展/考试专项 |  | 能完成迁移题或综合题 |

## 本章解决的问题

用 3-6 句回答：

- 为什么会有这个主题：
- 它试图解决什么问题：
- 学完之后应当会判断什么：
- 原文依据：

## 概念主线

用 3-5 条写出本章最重要的推进线，不要堆定义。

1. 
2. 
3. 

## 关键概念速览

| 名称 | 最小定义 | 直觉理解 | 掌握层级 | 闭卷标准 | 来源 |
| --- | --- | --- | --- | --- | --- |
|  |  | 教师补充： | explain / distinguish / apply / memorize |  | [PDF p.x] |

## 关键概念例子与边界

| 概念 | 正例 | 非例/边界 | 易混点 | 对应练习 |
| --- | --- | --- | --- | --- |
|  | 教师补充： |  |  | Qx / Ex |

## 小节闭环笔记

### x.x 小节标题

- 这一节回答什么问题：
- 先给结论：
- 原文依据：
- 直觉理解：
- 简单具体例子：
- 图示/过程追踪：
- 核心机制/展开：
- 为什么这样设计：
- 边界/易错点：
- 代码对应：
- 最小自测：
- 答案位置：见文末“小节自测答案区”

### x.x 小节标题

- 这一节回答什么问题：
- 先给结论：
- 原文依据：
- 直觉理解：
- 简单具体例子：
- 图示/过程追踪：
- 核心机制/展开：
- 为什么这样设计：
- 边界/易错点：
- 代码对应：
- 最小自测：
- 答案位置：见文末“小节自测答案区”

## 章节级重要对比

| 对比 | A 是什么 | B 是什么 | 关键差异 | 判断方法 | 来源 |
| --- | --- | --- | --- | --- | --- |
|  |  |  |  |  | [PDF p.x] |

## 章节级易错点

| 常见误解 | 正确说法 | 为什么容易错 | 修正自测 |
| --- | --- | --- | --- |
|  |  |  |  |

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

## 实现桥接与专项补充

用于 C、数据结构、算法、公式或转换较多的章节；不相关项可标为“不适用”。

| 主题 | 代码/材料位置 | 表示方式 | 空/边界情况 | 常见实现陷阱 |
| --- | --- | --- | --- | --- |
|  | `07-code-extracts.md` |  |  |  |

| 专项信号 | 本章是否涉及 | 必补内容 |
| --- | --- | --- |
| 二叉树 | 是 / 否 | 空树、五种基本形态、形态图、1-based/0-based 编号 |
| 遍历 | 是 / 否 | 访问模板、6-8 结点追踪、层序说明、递归出口 |
| 非递归遍历 | 是 / 否 | 栈状态表、栈内元素含义 |
| 线索二叉树 | 是 / 否 | `LTag/RTag` 表、指针/tag 改写例 |
| 并查集 | 是 / 否 | parent 数组追踪、先 Find 后合并、下标约定、均摊说明 |
| 赫夫曼 | 是 / 否 | 合并表、WPL、路径长度、权值相等不唯一、前缀条件 |
| 回溯 | 是 / 否 | 状态树、choose/recurse/undo 伪码、共享状态撤销 |
| Catalan/计数 | 是 / 否 | `b0,b1,b2,b3` 手算、`b_n`/`C_n`、有序树 n-1 偏移 |

## 闭卷检查

至少给出 5-8 个问题，覆盖本章总问题、关键流程、关键对比、最易错概念，以及至少一个“为什么这样设计”。题目区不写完整答案。

| ID | 难度 | 问题 | 提示 | 对应目标 | 答错回看 |
| --- | --- | --- | --- | --- | --- |
| NQ1 | Basic / Core / Transfer |  |  | LOx |  |

## 小节自测答案区

### x.x

- 最小自测答案：
- 自检标准：
- 常见错误：

## 闭卷检查答案区

### NQ1

- 完整答案：
- 评分/自检要点：
- 如果答错，回看：

## 必须闭卷记住

- 

## 理解即可

- 

## 练习映射

| 完成标准 | 对应主动回忆 | 对应练习 | 通过标准 |
| --- | --- | --- | --- |
|  | `02-active-recall.md` Qx | `03-exercises.md` Ex |  |

## 考前 10 分钟速读

1. 
2. 
3. 

## 最低完成标准

用“闭卷能回答什么”定义，不要写空话。

- 

## 本章小结

- 
""",
    "02-active-recall.md": """# 主动回忆：{title}

说明：题目区只放题目、目标、提示和来源。完整答案统一写在文件末尾的“答案区”。

## 闭卷解释题

| ID | 目标 | 题目 | 提示 | 来源 |
| --- | --- | --- | --- | --- |
| Q1 | LO1 |  | 只提示关键词，不写完整答案 | [PDF p.x] |

## 概念辨析题

| ID | 目标 | 题目 | 提示 | 常见误区提示 |
| --- | --- | --- | --- | --- |
| Q2 | LOx |  |  |  |

## 填空题

1. 
   - 提示：

## 错因判断题

1. 错误说法：
   - 提示：

## 迁移自测题

1. 教师设计题，不是原文例题：
   - 提示：
   - 检查的目标：

## 答案区

### Q1

- 完整答案：
- 自检标准：
- 常见遗漏：
- 来源依据：

### Q2

- 完整答案：
- 判断步骤：
- 常见错误：
- 来源依据：

### 填空题答案

1.

### 错因判断题答案

1.
   - 为什么错：
   - 正确说法：

### 迁移自测题答案

1.
   - 完整答案：
   - 评分/自检要点：
   - 教师设计题说明：
""",
    "03-exercises.md": """# 练习与答案：{title}

说明：练习区不写完整答案，只写题目、提示、目标和来源。完整答案、评分点、常见错误和代码答案统一写在文件末尾。

## Basic

### E1

- 目标：LOx
- 类型：recall | discrimination | procedure | error-correction | transfer
- 难度：Basic
- 题目：
- 提示：
- 来源依据：
- 进一步追问提示：

## Core

### E2

- 目标：LOx
- 类型：
- 难度：Core
- 题目：
- 提示：
- 来源依据：
- 进一步追问提示：

## Transfer

### E3

- 目标：LOx
- 类型：transfer
- 难度：Transfer
- 题目：教师设计题，不是原文例题。
- 提示：
- 来源依据或教师补充：
- 进一步追问提示：

## 完整答案与评分标准

### E1

- 标准答案：
- 评分要点：
- 常见错误：
- 来源依据：
- 如果涉及代码，完整代码：

```text

```

### E2

- 标准答案：
- 评分要点：
- 常见错误：
- 来源依据：
- 如果涉及代码，完整代码：

```text

```

### E3

- 标准答案：
- 评分要点：
- 常见错误：
- 来源依据或教师补充：
- 如果涉及代码，完整代码：

```text

```
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
    "06-memory-cards.md": """# 记忆卡片：{title}

## 卡片集信息

- 章节：{title}
- 来源：{source}
- 范围：{chapter}
- 目标：

## 必须记忆项筛选

| 项目 | 层级 | 为什么要记 | 对应目标 | 来源 |
| --- | --- | --- | --- | --- |
|  | Core / Secondary / Trap |  | LOx | [PDF p.x] |

## Core Cards

### C01

- 类型：definition | distinction | sequence | condition -> result | misconception repair | cloze
- 提问：
- 答案：
- 来源：
- 为什么要记：

### C02

- 类型：
- 提问：
- 答案：
- 来源：
- 为什么要记：

## Secondary Cards

### S01

- 类型：
- 提问：
- 答案：
- 来源：
- 为什么要记：

## Trap Cards

### T01

- 类型：distinction
- 提问：
- 答案：
- 来源：
- 常见错误：

## 3 分钟口头复习

-
""",
    "07-code-extracts.md": """# 代码整理：{title}

## 使用说明

- 本文件单独整理来源中的代码，尤其是扫描/OCR 得到的代码，方便阅读、复制和人工核对。
- 如果本章没有代码，写明“未发现需要单独整理的代码”。
- 不确定的 OCR token、缩进、换行、标点或运算符必须标为“待核对”。

## 代码索引

| ID | 来源位置 | 语言 | 可靠性 | 主题 | 状态 |
| --- | --- | --- | --- | --- | --- |
| Code1 | [PDF p.x] |  | 高 / 中 / 低 / 待核对 |  |  |

## 可复制代码块

### Code1

- 来源位置：
- 语言：
- OCR/抽取可靠性：
- 这段代码演示什么：
- 待核对位置：

```text

```

## 代码阅读笔记

| ID | 关键行/片段 | 作用 | 易错点 | 来源 |
| --- | --- | --- | --- | --- |
| Code1 |  |  |  | [PDF p.x] |

## 人工核对清单

- [ ] 缩进已核对。
- [ ] 标识符大小写已核对。
- [ ] 运算符和标点已核对。
- [ ] 换行和续行已核对。
- [ ] 代码能否运行或只是伪代码已标明。
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

## Chapter Study Time Table

| Study block | Source range | Objective | Task | Suggested time | Completion check |
| --- | --- | --- | --- | --- | --- |
| First pass | {chapter} | Build a chapter map | Mark headings, key concepts, and questions |  | Can state the problem this chapter solves |
| Deep study |  | LOx | Study core sections and write closed-loop notes |  | Can explain the main mechanism closed-book |
| Practice |  | LOx | Complete Basic/Core exercises |  | Self-grade against the answer key |
| Review |  | LOx | Use memory cards and recover wrong answers |  | Pass a 3-minute oral review |

## Compressed Study Plan

| Available time | Must do | Can skip | Risk |
| --- | --- | --- | --- |
| 30 minutes |  |  |  |
| 60 minutes |  |  |  |

## Learning Objectives

| ID | Observable performance | Mastery criterion | Assessed by | Source |
| --- | --- | --- | --- | --- |
| LO1 | Can... | Closed-book answer includes... | Q1, E1 | [PDF p.x] |
| LO2 | Can... | Can apply in a new scenario... | Q2, E2 | [Section x] |

## Knowledge-Point Mastery Standard

| Knowledge point | Mastery level | Closed-book criterion | Must memorize | Check method | Source |
| --- | --- | --- | --- | --- | --- |
|  | recognize / explain / distinguish / sequence / apply / memorize / diagnose |  | yes / no | Qx / Ex / Cx | [PDF p.x] |

## Chapter Management

- Source ID: {source_id}
- Chapter ID: {chapter_id}
- Previous chapter:
- Next chapter:
- Needs further module split:

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

## Title and Scope

- Chapter: {title}
- Source: {source}
- Page or section range: {chapter}
- Source map: `source-map.md`
- Extraction quality / needs verification:
- File encoding: UTF-8
- Chapter topic:

## How To Use This Note

- First-pass essentials:
- Second-pass strengthening:
- Must know before exercises:
- Companion active recall: `02-active-recall.md`
- Companion exercises: `03-exercises.md`
- Companion code extracts: `07-code-extracts.md`
- Source verification: `source-map.md`

## Chapter Map

Show the chapter's knowledge structure as a tree, flow, or ASCII sketch. Structural, algorithmic, and conversion-heavy chapters require a diagram or trace.

```text

```

## Layered Study Route

| Layer | Content | Completion check |
| --- | --- | --- |
| First pass |  | Can state the core problem and spine |
| Second pass |  | Can solve core examples and discriminations |
| Extension / exam focus |  | Can complete transfer or synthesis tasks |

## Problem This Chapter Solves

Answer in 3-6 sentences:

- Why this topic exists:
- What problem it tries to solve:
- What the learner should be able to judge after learning it:
- Source evidence:

## Conceptual Spine

Write the chapter's 3-5 most important moves. Do not dump definitions.

1. 
2. 
3. 

## Key Concept Overview

| Name | Minimal definition | Intuition | Mastery level | Closed-book criterion | Source |
| --- | --- | --- | --- | --- | --- |
|  |  | Teacher supplement: | explain / distinguish / apply / memorize |  | [PDF p.x] |

## Key Concept Examples And Boundaries

| Concept | Positive example | Non-example / boundary | Easy confusion | Matching practice |
| --- | --- | --- | --- | --- |
|  | Teacher supplement: |  |  | Qx / Ex |

## Closed-Loop Subsection Notes

### x.x Subsection title

- Question this subsection answers:
- Short conclusion:
- Source evidence:
- Intuition:
- Simple concrete example:
- Diagram / trace:
- Mechanism / development:
- Why this design or idea exists:
- Boundary / common confusion:
- Code connection:
- Minimum self-check:
- Answer location: see final "Subsection Self-Check Answer Key"

### x.x Subsection title

- Question this subsection answers:
- Short conclusion:
- Source evidence:
- Intuition:
- Simple concrete example:
- Diagram / trace:
- Mechanism / development:
- Why this design or idea exists:
- Boundary / common confusion:
- Code connection:
- Minimum self-check:
- Answer location: see final "Subsection Self-Check Answer Key"

## Chapter-Level Distinctions

| Contrast | A means | B means | Key difference | Decision rule | Source |
| --- | --- | --- | --- | --- | --- |
|  |  |  |  |  | [PDF p.x] |

## Chapter-Level Traps

| Common misconception | Correct version | Why it is tempting | Repair self-check |
| --- | --- | --- | --- |
|  |  |  |  |

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

## Implementation Bridge And Topic Add-Ons

Use this for C, data structures, algorithms, formulas, or conversion-heavy chapters. Mark irrelevant rows as "not applicable".

| Topic | Code/material location | Representation | Empty/boundary case | Common implementation pitfall |
| --- | --- | --- | --- | --- |
|  | `07-code-extracts.md` |  |  |  |

| Topic signal | Present? | Required add-on |
| --- | --- | --- |
| Binary tree | yes / no | empty tree, five basic forms, shape diagram, 1-based/0-based numbering |
| Traversal | yes / no | visit-order template, 6-8 node trace, level-order note, recursive base case |
| Non-recursive traversal | yes / no | stack-state table, what the stack stores |
| Threaded binary tree | yes / no | `LTag/RTag` table, pointer/tag rewrite example |
| Union-find | yes / no | parent array trace, Find before merge, index convention, amortized note |
| Huffman | yes / no | merge table, WPL, path length, equal weights are non-unique, prefix condition |
| Backtracking | yes / no | state tree, choose/recurse/undo pseudocode, shared-state undo |
| Catalan/counting | yes / no | `b0,b1,b2,b3` hand calculation, `b_n`/`C_n`, ordered-tree n-1 offset |

## Closed-Book Checks

Include 5-8 prompts covering the chapter problem, key flow, key contrasts, easiest trap, and at least one "why this design exists" question. Do not put complete answers in the prompt area.

| ID | Difficulty | Prompt | Hint | Objective | If wrong, review |
| --- | --- | --- | --- | --- | --- |
| NQ1 | Basic / Core / Transfer |  |  | LOx |  |

## Subsection Self-Check Answer Key

### x.x

- Minimum self-check answer:
- Self-check standard:
- Common mistake:

## Closed-Book Check Answer Key

### NQ1

- Complete answer:
- Scoring/self-check points:
- If wrong, review:

## Must Memorize

- 

## Understand Only

- 

## Practice Mapping

| Completion standard | Active recall | Exercise | Passing standard |
| --- | --- | --- | --- |
|  | `02-active-recall.md` Qx | `03-exercises.md` Ex |  |

## 10-Minute Review Route

1. 
2. 
3. 

## Minimum Completion Standard

Define this as what the learner can answer closed-book. Avoid vague claims.

- 

## Chapter Summary

- 
""",
    "02-active-recall.md": """# Active Recall: {title}

Note: The prompt section contains only prompts, objectives, hints, and sources. Put complete answers in the final Answer Key.

## Closed-Book Explanation

| ID | Objective | Prompt | Hint | Source |
| --- | --- | --- | --- | --- |
| Q1 | LO1 |  | Hint only; do not write the complete answer here | [PDF p.x] |

## Concept Discrimination

| ID | Objective | Prompt | Hint | Common-trap hint |
| --- | --- | --- | --- | --- |
| Q2 | LOx |  |  |  |

## Cloze Prompts

1. 
   - Hint:

## Error Diagnosis

1. Wrong statement:
   - Hint:

## Transfer Self-Test

1. Teacher-designed prompt, not a source example:
   - Hint:
   - Objective tested:

## Answer Key

### Q1

- Complete answer:
- Self-check standard:
- Common omission:
- Source basis:

### Q2

- Complete answer:
- Decision steps:
- Common error:
- Source basis:

### Cloze Answers

1.

### Error Diagnosis Answers

1.
   - Why it is wrong:
   - Correct version:

### Transfer Self-Test Answers

1.
   - Complete answer:
   - Scoring/self-check points:
   - Teacher-designed prompt note:
""",
    "03-exercises.md": """# Exercises and Answers: {title}

Note: Exercise sections contain prompts, hints, objectives, and sources only. Put complete answers, scoring points, common errors, and code answers at the end.

## Basic

### E1

- Objective: LOx
- Type: recall | discrimination | procedure | error-correction | transfer
- Difficulty: Basic
- Prompt:
- Hint:
- Source basis:
- Follow-up hint:

## Core

### E2

- Objective: LOx
- Type:
- Difficulty: Core
- Prompt:
- Hint:
- Source basis:
- Follow-up hint:

## Transfer

### E3

- Objective: LOx
- Type: transfer
- Difficulty: Transfer
- Prompt: Teacher-designed prompt, not a source example.
- Hint:
- Source basis or teacher supplement:
- Follow-up hint:

## Complete Answers and Scoring

### E1

- Expected answer:
- Scoring points:
- Common wrong answer:
- Source basis:
- Complete code if relevant:

```text

```

### E2

- Expected answer:
- Scoring points:
- Common wrong answer:
- Source basis:
- Complete code if relevant:

```text

```

### E3

- Expected answer:
- Scoring points:
- Common wrong answer:
- Source basis or teacher supplement:
- Complete code if relevant:

```text

```
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
    "06-memory-cards.md": """# Memory Cards: {title}

## Card Set Header

- Chapter: {title}
- Source: {source}
- Scope: {chapter}
- Goal:

## Memorization Selection

| Item | Tier | Why memorize | Objective | Source |
| --- | --- | --- | --- | --- |
|  | Core / Secondary / Trap |  | LOx | [PDF p.x] |

## Core Cards

### C01

- Type: definition | distinction | sequence | condition -> result | misconception repair | cloze
- Prompt:
- Answer:
- Source:
- Why memorize:

### C02

- Type:
- Prompt:
- Answer:
- Source:
- Why memorize:

## Secondary Cards

### S01

- Type:
- Prompt:
- Answer:
- Source:
- Why memorize:

## Trap Cards

### T01

- Type: distinction
- Prompt:
- Answer:
- Source:
- Common wrong answer:

## 3-Minute Oral Review

-
""",
    "07-code-extracts.md": """# Code Extracts: {title}

## Usage Notes

- Use this file to organize source code separately, especially scanned/OCR code, so it is easy to read, copy, and verify.
- If the chapter has no code, state "No code snippets need separate extraction."
- Mark uncertain OCR tokens, indentation, line breaks, punctuation, or operators as `Needs verification`.

## Code Index

| ID | Source location | Language | Reliability | Topic | Status |
| --- | --- | --- | --- | --- | --- |
| Code1 | [PDF p.x] |  | high / medium / low / needs verification |  |  |

## Copyable Code Blocks

### Code1

- Source location:
- Language:
- OCR/extraction reliability:
- What this code demonstrates:
- Needs verification:

```text

```

## Code Reading Notes

| ID | Key line/snippet | Role | Common trap | Source |
| --- | --- | --- | --- | --- |
| Code1 |  |  |  | [PDF p.x] |

## Manual Verification Checklist

- [ ] Indentation checked.
- [ ] Identifier casing checked.
- [ ] Operators and punctuation checked.
- [ ] Line breaks and continuations checked.
- [ ] Runnable code vs pseudocode marked.
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


def stable_slug(value: str, prefix: str) -> str:
    slug = slugify(value)
    if len(slug) >= 3:
        return slug
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()[:8]
    return f"{prefix}-{digest}"


def default_out_dir(title: str, created_at: datetime) -> Path:
    slug = stable_slug(title, "lesson-pack")
    base = Path(slug)

    candidate = base
    index = 2
    while candidate.exists():
        candidate = Path(f"{base}-{index}")
        index += 1
    return candidate


def resolve_out_dir(args: argparse.Namespace, created_at: datetime) -> tuple[Path, str, str]:
    source_seed = Path(args.source).stem if args.source else args.title
    source_id = args.source_id or stable_slug(source_seed, "source")
    chapter_id = args.chapter_id or stable_slug(args.chapter or args.title, "chapter")

    if args.out:
        return Path(args.out), source_id, chapter_id
    if args.project_root:
        return Path(args.project_root) / "lessons" / source_id / "chapters" / chapter_id, source_id, chapter_id
    return default_out_dir(args.title, created_at), source_id, chapter_id


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
    parser.add_argument("--project-root", help="Class project root. If --out is omitted, write under lessons/<source-id>/chapters/<chapter-id>.")
    parser.add_argument("--source-id", help="ASCII source id for chapter-managed lesson output.")
    parser.add_argument("--chapter-id", help="ASCII chapter/module id for chapter-managed lesson output.")
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
    out_dir, source_id, chapter_id = resolve_out_dir(args, created_at_dt)
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
        "source_id": source_id,
        "chapter_id": chapter_id,
        "created_at": created_at,
        "template_version": TEMPLATE_VERSION,
    }

    templates = choose_files(args.language, args.pack)
    results = {}
    for filename, template in templates.items():
        results[filename] = write_file(out_dir / filename, template.format(**values), args.overwrite)

    if args.project_root and not args.out:
        index_template = CHAPTER_INDEX_ZH if args.language == "zh" else CHAPTER_INDEX_EN
        index_path = Path(args.project_root) / "lessons" / source_id / "chapter-index.md"
        results["chapter-index.md"] = write_file(index_path, index_template.format(**values), overwrite=False)

    meta = {
        "title": args.title,
        "source": values["source"],
        "chapter": values["chapter"],
        "language": args.language,
        "pack": args.pack,
        "template_version": TEMPLATE_VERSION,
        "checker_version": CHECKER_VERSION,
        "created_at": created_at,
        "project_root": str(Path(args.project_root).resolve()) if args.project_root else "",
        "source_id": source_id,
        "chapter_id": chapter_id,
        "chapter_managed": bool(args.project_root and not args.out),
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
        "source_id": source_id,
        "chapter_id": chapter_id,
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
