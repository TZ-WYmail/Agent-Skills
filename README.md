# Agent-Skills

定制的个人化 Codex agent skills，用于沉淀特定场景的终端交互流程和效率提升工具。

## 仓库结构

每个 skill 都放在仓库根目录下的独立文件夹中，skill 目录本身只保留 Codex 运行需要的文件：`SKILL.md`、`agents/`、`references/`、`scripts/` 等。

```text
repo-root/
|-- README.md
|-- .gitignore
`-- teach-pdf-content/
    |-- SKILL.md
    |-- agents/
    |   `-- openai.yaml
    |-- references/
    |   `-- teaching_patterns.md
    `-- scripts/
        |-- init_class_project.py
        |-- extract_pdf_text.py
        |-- ocr_pdf_pages.py
        |-- new_lesson_pack.py
        `-- check_lesson_pack.py
```

## teach-pdf-content

`teach-pdf-content` 是一个用于 Codex 的教学类 skill。它把用户指定的 PDF 章节、教材片段、论文、讲义或课程阅读材料，转换成有来源依据的教学过程和 Markdown 学习包。

核心目标不是简单总结材料，而是像教师一样帮助学习：提炼学习目标、解释概念、设计主动回忆、练习题、答案、术语表和复习计划，并明确区分原文依据、教师补充、合理推断和待核对内容。

### Skill 能力

- 按指定 PDF 章节或页码范围生成学习包。
- 区分物理 PDF 页码、书籍印刷页码和章节位置。
- 对文本型 PDF 生成抽取结果和质量报告。
- 对扫描版或图片型 PDF 使用本地 OCR，并把缓存、模型和日志放进课程项目目录。
- 按一个 `class project` 管理整门课，而不是生成零散文件。
- 生成 `00-learning-path.md`、`01-lesson-notes.md`、`02-active-recall.md`、`03-exercises.md`、`04-glossary.md`、`05-review-plan.md` 和 `source-map.md` 等学习文件。

### 快速开始

验证 skill 基础格式：

```powershell
python "$env:USERPROFILE\.codex\skills\.system\skill-creator\scripts\quick_validate.py" .\teach-pdf-content
```

初始化一门课的项目目录：

```powershell
python teach-pdf-content\scripts\init_class_project.py `
  --project-root .\my-class `
  --course-title "示例课程" `
  --source .\sources\book.pdf
```

为一个章节创建学习包骨架：

```powershell
python teach-pdf-content\scripts\new_lesson_pack.py `
  --title "第 1 章 示例章节" `
  --source .\sources\book.pdf `
  --chapter "第 1 章" `
  --out .\my-class\lessons\chapter-01 `
  --require-source
```

检查学习包是否还有未完成字段：

```powershell
python teach-pdf-content\scripts\check_lesson_pack.py .\my-class\lessons\chapter-01
```

### PDF 抽取流程

文本型 PDF 优先使用：

```powershell
python teach-pdf-content\scripts\extract_pdf_text.py `
  .\sources\book.pdf `
  --pages 18-25 `
  --chapter-title "示例章节" `
  --out .\my-class\extracts\chapter-01.md `
  --json-out .\my-class\.teach-pdf-content\logs\chapter-01-extract.json
```

如果抽取质量报告显示页面几乎没有文字，通常说明 PDF 是扫描版或图片版，应改用 OCR。

### OCR 流程

扫描版 PDF 使用本地 OCR：

```powershell
python teach-pdf-content\scripts\ocr_pdf_pages.py `
  .\sources\book.pdf `
  --pages 18-25 `
  --project-root .\my-class `
  --source-id book `
  --lang chi_sim+eng `
  --tesseract-exe "<path-to-tesseract.exe>"
```

OCR 输出会保存在课程项目下：

```text
my-class/
|-- .teach-pdf-content/
|   |-- cache/
|   |-- logs/
|   `-- models/
`-- extracts/
    `-- ocr/
```

如果需要中文 OCR 模型，把 `chi_sim.traineddata`、`eng.traineddata`、`osd.traineddata` 等文件放到课程项目内的：

```text
.teach-pdf-content/models/tesseract/tessdata/
```

## 推送前检查

`.gitignore` 已配置为忽略课程项目产物、PDF、OCR 图片、Tesseract 模型、评估草稿和 Python 缓存。默认只应推送 skill 源码和仓库说明。

```powershell
git status --short --untracked-files=all
python "$env:USERPROFILE\.codex\skills\.system\skill-creator\scripts\quick_validate.py" .\teach-pdf-content
```
